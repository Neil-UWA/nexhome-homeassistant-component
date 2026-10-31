import logging
from datetime import time as dt_time, timedelta
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN, TIME_NUMBER, POLL_BATCH_SIZE,
    OPT_POLL_INTERVAL, OPT_IDLE_MAX_INTERVAL, OPT_QUIET_ENABLED,
    OPT_QUIET_START, OPT_QUIET_END, OPT_QUIET_INTERVAL,
    DEFAULT_IDLE_MAX_INTERVAL, DEFAULT_QUIET_ENABLED, DEFAULT_QUIET_START,
    DEFAULT_QUIET_END, DEFAULT_QUIET_INTERVAL,
    ACTIVE_WINDOW_SECONDS, PAUSED_CHECK_SECONDS, SENSOR_IDENTIFIERS,
)
from .gateway_scheduler import get_gateway_scheduler, POLL_SKIPPED

_LOGGER = logging.getLogger(__name__)


def _parse_time(value, default: str) -> dt_time:
    try:
        return dt_time.fromisoformat(value or default)
    except (TypeError, ValueError):
        return dt_time.fromisoformat(default)


class NexhomeCoordinator(DataUpdateCoordinator):
    """Polls all devices of a gateway with merged realtime requests.

    The realtime API accepts properties of many devices in one request and
    every returned item carries its `address`, so one request per poll covers
    the whole house instead of one request per device (gateway load and heat).

    `data` maps device address -> list of {identifier, address, value} items
    from the latest successful poll. On a skipped/failed poll it is `{}`, so
    entities keep their current state instead of re-applying stale values.

    Adaptive interval: right after activity (a state change seen by polling,
    a UDP push or a control from HA) the base interval is used; once idle for
    ACTIVE_WINDOW_SECONDS the interval doubles each poll up to the idle cap.
    During quiet hours the cap is the quiet interval, and 0 stops polling
    entirely (push only) until the next activity.
    """

    def __init__(self, hass, tool, options=None, push_enabled=False):
        """Initialize the data update coordinator.

        Args:
            hass: Home Assistant instance
            tool: ServiceTool instance
            options: Config entry options (adaptive polling settings)
            push_enabled: Whether push-based updates are active
        """
        options = options or {}
        self._base_interval = max(1, int(options.get(OPT_POLL_INTERVAL, TIME_NUMBER)))
        self._idle_max_interval = max(
            self._base_interval,
            int(options.get(OPT_IDLE_MAX_INTERVAL, DEFAULT_IDLE_MAX_INTERVAL)),
        )
        self._quiet_enabled = bool(options.get(OPT_QUIET_ENABLED, DEFAULT_QUIET_ENABLED))
        self._quiet_start = _parse_time(options.get(OPT_QUIET_START), DEFAULT_QUIET_START)
        self._quiet_end = _parse_time(options.get(OPT_QUIET_END), DEFAULT_QUIET_END)
        quiet_interval = int(options.get(OPT_QUIET_INTERVAL, DEFAULT_QUIET_INTERVAL))
        # 0 表示静默时段停止轮询；否则不低于基础间隔
        self._quiet_interval = 0 if quiet_interval <= 0 else max(self._base_interval, quiet_interval)

        DataUpdateCoordinator.__init__(
            self,
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self._base_interval),
        )
        self._tool = tool
        self._push_enabled = push_enabled
        # {device_address: set(identifiers)}
        self._targets = {}
        # 上一次轮询到的非测量类属性值 {(address, identifier): value}，用于检测状态变化
        self._snapshot = {}
        self._current_interval = self._base_interval
        self._in_update = False
        self._scheduler = get_gateway_scheduler(hass)
        self._remove_activity_listener = self._scheduler.add_activity_listener(
            self._handle_activity
        )

    def add_targets(self, device_address: str, identifiers) -> None:
        self._targets.setdefault(device_address, set()).update(identifiers)

    def remove_targets(self, device_address: str) -> None:
        self._targets.pop(device_address, None)

    async def async_shutdown(self) -> None:
        self._remove_activity_listener()
        await super().async_shutdown()

    def _build_params(self) -> list:
        return [
            {'identifier': identifier, 'address': address}
            for address, identifiers in self._targets.items()
            for identifier in identifiers
        ]

    def _in_quiet_hours(self) -> bool:
        if not self._quiet_enabled or self._quiet_start == self._quiet_end:
            return False
        now = dt_util.now().time()
        if self._quiet_start < self._quiet_end:
            return self._quiet_start <= now < self._quiet_end
        # 跨午夜，如 23:00 - 07:00
        return now >= self._quiet_start or now < self._quiet_end

    def _polling_suspended(self) -> bool:
        """静默时段配置为 0 且已空闲：不再向网关发请求。"""
        return (
            self._quiet_interval == 0
            and self._in_quiet_hours()
            and self._scheduler.idle_seconds() >= ACTIVE_WINDOW_SECONDS
        )

    def _set_interval(self, seconds: int) -> None:
        if seconds != self._current_interval:
            _LOGGER.debug("轮询间隔调整为 %ss", seconds)
        self._current_interval = seconds
        self.update_interval = timedelta(seconds=seconds)

    def _schedule_next_interval(self) -> None:
        """根据空闲时长和静默时段计算下一次轮询间隔。"""
        if self._scheduler.idle_seconds() < ACTIVE_WINDOW_SECONDS:
            self._set_interval(self._base_interval)
            return
        if self._in_quiet_hours():
            if self._quiet_interval == 0:
                self._set_interval(PAUSED_CHECK_SECONDS)
                return
            cap = self._quiet_interval
        else:
            cap = self._idle_max_interval
        self._set_interval(min(self._current_interval * 2, cap))

    @callback
    def _handle_activity(self) -> None:
        """有活动时立刻恢复基础间隔（例如夜间收到推送或在 HA 中操作）。"""
        if self._current_interval == self._base_interval:
            return
        self._set_interval(self._base_interval)
        if self._in_update:
            # 本轮轮询自身检测到的变化，结束时会按新间隔排程
            return
        # 立即触发一次刷新以按新间隔重新排程（控制刚发出时轮询会被跳过，不打扰网关）
        self.hass.async_create_task(self.async_request_refresh())

    def _detect_changes(self, result: dict) -> bool:
        """对比上次轮询，非测量类属性（开关、模式、亮度等）有变化即视为有人操作。"""
        changed = False
        for address, items in result.items():
            for item in items:
                identifier = item.get('identifier')
                if identifier is None or identifier in SENSOR_IDENTIFIERS:
                    continue
                key = (address, identifier)
                value = item.get('value')
                if key in self._snapshot and self._snapshot[key] != value:
                    changed = True
                self._snapshot[key] = value
        return changed

    async def _async_update_data(self):
        if self._polling_suspended():
            self._schedule_next_interval()
            return {}

        params = self._build_params()
        result = {}
        for start in range(0, len(params), POLL_BATCH_SIZE):
            chunk = params[start:start + POLL_BATCH_SIZE]
            try:
                response = await self._scheduler.async_poll(self._tool.devicePost, chunk)
                if response is POLL_SKIPPED:
                    # 控制请求优先，本轮剩余分片不再打扰网关
                    break
                if not response:
                    continue
                response.raise_for_status()
                device_property = response.json().get('result', {}).get('deviceProperty') or []
            except Exception as err:
                _LOGGER.debug("轮询设备属性失败: %s", err)
                continue
            for item in device_property:
                address = item.get('address')
                if address:
                    result.setdefault(address, []).append(item)

        if self._detect_changes(result):
            # 面板等 HA 之外的操作，恢复基础间隔以便后续变化快速同步
            self._in_update = True
            try:
                self._scheduler.note_activity()
            finally:
                self._in_update = False
        self._schedule_next_interval()
        return result
