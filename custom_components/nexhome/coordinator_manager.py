"""协调器管理器 - 所有设备共享一个协调器，合并请求以减少网关负载"""
import logging
from typing import Dict
from .nexhome_coordinator import NexhomeCoordinator
from .header import ServiceTool

_LOGGER = logging.getLogger(__name__)


class CoordinatorManager:
    """管理共享协调器，所有实体共用一个协调器"""
    
    _instances: Dict[str, 'CoordinatorManager'] = {}
    
    def __init__(self, hass, tool: ServiceTool, push_enabled: bool = False):
        self.hass = hass
        self.tool = tool
        self._push_enabled = push_enabled
        # 整个网关共用一个协调器，合并为一次 realtime 请求轮询所有设备
        self._coordinator = NexhomeCoordinator(hass, tool, push_enabled=push_enabled)

    @classmethod
    def get_instance(cls, hass, tool: ServiceTool, config_entry_id: str, push_enabled: bool = False):
        """获取或创建协调器管理器实例"""
        if config_entry_id not in cls._instances:
            cls._instances[config_entry_id] = cls(hass, tool, push_enabled)
        return cls._instances[config_entry_id]

    @classmethod
    async def async_remove_instance(cls, config_entry_id: str) -> None:
        """移除并清理指定配置条目的协调器管理器实例（支持集成 reload）"""
        instance = cls._instances.pop(config_entry_id, None)
        if instance is None:
            return
        await instance.async_shutdown()

    async def async_shutdown(self) -> None:
        """关闭协调器"""
        try:
            await self._coordinator.async_shutdown()
        except Exception as err:
            _LOGGER.debug("关闭协调器失败: %s", err)

    def get_or_create_coordinator(self, device_address: str, identifiers: list) -> NexhomeCoordinator:
        """
        登记设备需要轮询的标识符，并返回共享协调器
        :param device_address: 设备地址
        :param identifiers: 需要查询的标识符列表
        :return: 协调器实例
        """
        self._coordinator.add_targets(device_address, identifiers)
        return self._coordinator

    def remove_coordinator(self, device_address: str):
        """移除设备的轮询目标（当设备被移除时）"""
        self._coordinator.remove_targets(device_address)
