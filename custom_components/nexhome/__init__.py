import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import (
    DEVICES, ALL_PLATFORM, SN_CONFIG, IP_CONFIG, DOMAIN,
    FILTER_MODE_CONFIG, FILTER_DEVICES_CONFIG,
    UDP_LISTENER, PUSH_ENABLED,
)
from .header import ServiceTool
from .nexhome_discover import UDPListener
from .utils import set_hass_obj
from .coordinator_manager import CoordinatorManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry):
    await register_device_list_service(hass, entry)

    # 启动推送监听（UDP）
    push_enabled = await _async_start_push_listeners(hass)
    set_hass_obj(hass, PUSH_ENABLED, push_enabled)

    await hass.config_entries.async_forward_entry_setups(entry, ALL_PLATFORM)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # 停止推送监听
    await _async_stop_push_listeners(hass)

    # 卸载平台
    for platform in ALL_PLATFORM:
        await hass.config_entries.async_forward_entry_unload(entry, platform)
    # 清理跨 reload 保留的缓存（Home Assistant reload 不会重启 Python 进程）
    await CoordinatorManager.async_remove_instance(entry.entry_id)
    return True


async def _async_start_push_listeners(hass: HomeAssistant) -> bool:
    """启动 UDP 推送监听器，返回是否成功启动。"""
    push_enabled = False

    try:
        udp_listener = UDPListener(hass)
        await udp_listener.start()
        set_hass_obj(hass, UDP_LISTENER, udp_listener)
        push_enabled = True
        _LOGGER.info("Nexhome UDP 推送监听已就绪")
    except Exception:
        _LOGGER.warning("UDP 推送监听启动失败，将使用轮询模式", exc_info=True)

    return push_enabled


async def _async_stop_push_listeners(hass: HomeAssistant):
    """停止推送监听器。"""
    if DOMAIN in hass.data:
        udp_listener = hass.data[DOMAIN].get(UDP_LISTENER)
        if udp_listener and isinstance(udp_listener, UDPListener):
            udp_listener.close()


async def register_device_list_service(hass, entry):
    SN = entry.data.get(SN_CONFIG)
    IP = entry.data.get(IP_CONFIG)
    tool = ServiceTool(IP, SN)
    await tool.login(hass)
    deviceList = await tool.getDevice(hass) or []
    if not isinstance(deviceList, list):
        _LOGGER.warning("获取设备列表返回异常类型: %s", type(deviceList).__name__)
        deviceList = []
    
    # 从配置中获取筛选设置
    filter_mode = entry.data.get(FILTER_MODE_CONFIG, "exclude")
    filter_devices = entry.data.get(FILTER_DEVICES_CONFIG, [])
    
    # 过滤设备
    if deviceList and filter_devices:
        if filter_mode == "include":
            # 包含模式：只保留选中的设备
            deviceList = [
                device for device in deviceList
                if device.get('id') in filter_devices
            ]
        else:
            # 排除模式：排除选中的设备
            deviceList = [
                device for device in deviceList
                if device.get('id') not in filter_devices
            ]
    # 如果filter_devices为空，排除模式下相当于接入所有设备
    
    device_value = [
        {
            'device_id': device.get('id'),
            'device_type_id': device.get('type'),
            'device_name': device.get('name'),
            **device
        }
        for device in deviceList
    ]
    _LOGGER.debug("设备列表: %s", device_value)
    set_hass_obj(hass, DEVICES, device_value)
