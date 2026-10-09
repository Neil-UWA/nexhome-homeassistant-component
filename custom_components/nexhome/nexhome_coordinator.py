import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, TIME_NUMBER, POLL_BATCH_SIZE
from .gateway_scheduler import get_gateway_scheduler, POLL_SKIPPED

_LOGGER = logging.getLogger(__name__)

class NexhomeCoordinator(DataUpdateCoordinator):
    """Polls all devices of a gateway with merged realtime requests.

    The realtime API accepts properties of many devices in one request and
    every returned item carries its `address`, so one request per poll covers
    the whole house instead of one request per device (gateway load and heat).

    `data` maps device address -> list of {identifier, address, value} items
    from the latest successful poll. On a skipped/failed poll it is `{}`, so
    entities keep their current state instead of re-applying stale values.

    Keep polling active even when push mode is enabled, so out-of-band
    changes (e.g. physical panel operations without push events) can still
    be synchronized back to Home Assistant quickly.
    """

    def __init__(self, hass, tool, update_interval=None, push_enabled=False):
        """Initialize the data update coordinator.

        Args:
            hass: Home Assistant instance
            tool: ServiceTool instance
            update_interval: Update interval in seconds (default: TIME_NUMBER)
            push_enabled: Whether push-based updates are active
        """
        if update_interval is None:
            update_interval = TIME_NUMBER
        if push_enabled:
            _LOGGER.debug(
                "Push mode enabled; polling remains active every %ss for state sync",
                update_interval,
            )
        DataUpdateCoordinator.__init__(
            self,
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        self._tool = tool
        # {device_address: set(identifiers)}
        self._targets = {}

    def add_targets(self, device_address: str, identifiers) -> None:
        self._targets.setdefault(device_address, set()).update(identifiers)

    def remove_targets(self, device_address: str) -> None:
        self._targets.pop(device_address, None)

    def _build_params(self) -> list:
        return [
            {'identifier': identifier, 'address': address}
            for address, identifiers in self._targets.items()
            for identifier in identifiers
        ]

    async def _async_update_data(self):
        params = self._build_params()
        result = {}
        scheduler = get_gateway_scheduler(self.hass)
        for start in range(0, len(params), POLL_BATCH_SIZE):
            chunk = params[start:start + POLL_BATCH_SIZE]
            try:
                response = await scheduler.async_poll(self._tool.devicePost, chunk)
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
        return result
