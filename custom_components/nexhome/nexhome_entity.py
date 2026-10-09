from homeassistant.helpers.entity import Entity
from .const import DOMAIN, SIGNAL_PUSH_UPDATE
from .gateway_scheduler import get_gateway_scheduler
from .nexhome_device import NEXHOME_DEVICE
import logging
import time
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.core import callback
_LOGGER = logging.getLogger(__name__)


class NexhomeEntity(CoordinatorEntity, Entity):
    _attr_should_poll = False
    _optimistic_protect_seconds = 5.0

    def __init__(self, device, entity_key: str, coordinator):
        CoordinatorEntity.__init__(self, coordinator)
        self._device = device
        self._entity_key = entity_key
        self._config = NEXHOME_DEVICE[self._device['device_type_id']]["entities"][entity_key]
        self._unique_id = f"{DOMAIN}.{self._device['device_id']}_{entity_key}"
        self._device_name = self._device['device_name']
        self._property = None
        self._pending_control_values = {}
        

    # identifiers (必需): 一个集合，包含唯一标识设备的元组。通常，元组至少包含一个组件的域名和设备的唯一ID。这个唯一标识符用于确保Home Assistant可以准确地识别每个设备。

    # name (可选): 设备的友好名称，它将在Home Assistant的UI中显示。

    # manufacturer (可选): 制造设备的公司或个人的名称。

    # model (可选): 设备的型号。这有助于用户识别设备的具体版本或类型。

    # sw_version (可选): 设备的软件版本。这对于跟踪更新或解决问题可能很有用。

    # via_device (可选): 如果这个设备是通过另一个设备连接到Home Assistant的（例如，一个传感器通过一个网关连接），这里应该填写那个"网关"设备的标识符。

    # configuration_url (可选): 如果设备提供了一个用于配置或管理的web界面，这里可以填写那个界面的URL。

    # entry_type (可选): 设备条目类型，比如 gateway, service 等，用于进一步描述设备的角色或类型。

    # connections (可选): 一个集合，包含元组，用于表示设备的其他连接信息，如MAC地址、序列号等。每个元组的第一个元素是连接类型（例如，homeassistant.const.CONNECTION_NETWORK_MAC），第二个元素是实际的连接值。

    # suggested_area (可选): 建议的区域名称，可以帮助自动将设备分配到Home Assistant中的一个区域。
    @property
    def device(self):
        return self._device

    @property
    def device_info(self):
        return {
            "manufacturer": "Nexhome",
            "model": f"{self._device_name}-{self._device['device_type_id']}",
            "identifiers": {(DOMAIN, self._device['device_id'])},
            "name": self._device_name
        }

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._config.get("name")
    @property
    def icon(self):
        return self._config.get("icon")
    
    async def async_added_to_hass(self):
        """当实体添加到Home Assistant时调用"""
        await super().async_added_to_hass()
        # 请求一次刷新拿到初始状态；协调器自带防抖，大量实体同时添加只会合并成少量请求
        await self.coordinator.async_request_refresh()

        # 监听推送更新信号（UDP），实现实时状态更新
        device_address = self._device.get("address")
        if device_address:
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    f"{SIGNAL_PUSH_UPDATE}_{device_address}",
                    self._handle_push_update,
                )
            )

    @callback
    def _handle_push_update(self, properties: list) -> None:
        """处理来自 UDP 推送的实时状态更新。"""
        if not properties:
            return
        for prop in properties:
            identifier = prop.get("identifier")
            value = prop.get("value")
            if identifier is not None:
                self._device[identifier] = value
                self._pending_control_values.pop(identifier, None)
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._property = (self.coordinator.data or {}).get(self._device.get("address"))
        if self._property and len(self._property) > 0:
            for property in self._property:
                identifier = property.get('identifier')
                if identifier is None:
                    continue
                value = property.get('value', None)
                if not self._should_skip_stale_coordinator_value(identifier, value):
                    self._device[identifier] = value
        self.async_write_ha_state()

    def _async_device_control(self, data: dict) -> None:
        """异步发送设备控制指令，并立即做一次本地状态回显。"""
        address = self._device.get("address")
        if not address:
            return

        identifier = data.get("identifier")
        if identifier is not None and "value" in data:
            value = data.get("value")
            self._pending_control_values[identifier] = (
                self._normalize_state_value(value),
                time.monotonic() + self._optimistic_protect_seconds,
            )
            self._device[identifier] = value
            self.async_write_ha_state()

        self.hass.async_create_task(
            get_gateway_scheduler(self.hass).async_control(
                self._tool.device_control,
                data,
                address,
            )
        )

    async def async_turn_on(self, **kwargs):
        self.turn_on(**kwargs)

    async def async_turn_off(self, **kwargs):
        self.turn_off(**kwargs)

    async def async_select_option(self, option):
        self.select_option(option)

    async def async_open_cover(self, **kwargs):
        self.open_cover(**kwargs)

    async def async_close_cover(self, **kwargs):
        self.close_cover(**kwargs)

    async def async_stop_cover(self, **kwargs):
        self.stop_cover(**kwargs)

    async def async_set_cover_position(self, **kwargs):
        self.set_cover_position(**kwargs)

    async def async_set_hvac_mode(self, hvac_mode):
        self.set_hvac_mode(hvac_mode)

    async def async_set_temperature(self, **kwargs):
        self.set_temperature(**kwargs)

    async def async_set_fan_mode(self, fan_mode):
        self.set_fan_mode(fan_mode)

    async def async_set_swing_mode(self, swing_mode):
        self.set_swing_mode(swing_mode)

    async def async_set_preset_mode(self, preset_mode):
        self.set_preset_mode(preset_mode)

    def _normalize_state_value(self, value):
        return "" if value is None else str(value)

    def _should_skip_stale_coordinator_value(self, identifier, value) -> bool:
        pending = self._pending_control_values.get(identifier)
        if pending is None:
            return False

        pending_value, deadline = pending
        incoming_value = self._normalize_state_value(value)

        if incoming_value == pending_value:
            self._pending_control_values.pop(identifier, None)
            return False

        if time.monotonic() >= deadline:
            self._pending_control_values.pop(identifier, None)
            return False

        return True
