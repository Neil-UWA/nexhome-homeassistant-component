"""MQTT 处理器 - 订阅设备状态主题并分发推送更新。

支持两种 MQTT 消息格式:
1. 主题: {topic_prefix}/{device_address}
   负载: JSON 数组 [{"identifier": "PowerSwitch", "value": "1"}, ...]

2. 主题: {topic_prefix}/{device_address}/{identifier}
   负载: 属性值（纯文本）
"""
import json
import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, SIGNAL_PUSH_UPDATE

_LOGGER = logging.getLogger(__name__)


class MqttHandler:
    """管理 MQTT 订阅，将收到的设备状态消息分发给实体。"""

    def __init__(self, hass: HomeAssistant, topic_prefix: str):
        self.hass = hass
        self._topic_prefix = topic_prefix.rstrip("/")
        self._unsubscribe = None

    async def async_start(self):
        """订阅 MQTT 主题。"""
        try:
            from homeassistant.components import mqtt  # noqa: E402

            subscribe_topic = f"{self._topic_prefix}/#"
            self._unsubscribe = await mqtt.async_subscribe(
                self.hass, subscribe_topic, self._message_received, qos=0
            )
            _LOGGER.info("Nexhome MQTT 订阅已启动: %s", subscribe_topic)
        except Exception:
            _LOGGER.warning(
                "无法启动 MQTT 订阅，请确认 Home Assistant 已配置 MQTT 集成",
                exc_info=True,
            )

    async def async_stop(self):
        """取消 MQTT 订阅。"""
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
            _LOGGER.info("Nexhome MQTT 订阅已停止")

    @callback
    def _message_received(self, msg):
        """处理收到的 MQTT 消息。"""
        try:
            topic = msg.topic
            payload = msg.payload

            # 去除主题前缀
            suffix = topic[len(self._topic_prefix) + 1 :]  # +1 for the "/"
            parts = suffix.split("/")

            if len(parts) == 1:
                # 格式1: {prefix}/{address} → 负载为 JSON 数组
                address = parts[0]
                try:
                    properties = json.loads(payload)
                    if not isinstance(properties, list):
                        properties = [properties]
                except (json.JSONDecodeError, TypeError):
                    _LOGGER.debug("MQTT 消息解析失败: %s", payload)
                    return
            elif len(parts) == 2:
                # 格式2: {prefix}/{address}/{identifier} → 负载为值
                address = parts[0]
                identifier = parts[1]
                properties = [{"identifier": identifier, "value": str(payload)}]
            else:
                _LOGGER.debug("未知 MQTT 主题格式: %s", topic)
                return

            _LOGGER.debug(
                "MQTT 推送: 设备 %s, 属性 %s", address, properties
            )

            signal = f"{SIGNAL_PUSH_UPDATE}_{address}"
            async_dispatcher_send(self.hass, signal, properties)

        except Exception:
            _LOGGER.debug("处理 MQTT 消息失败", exc_info=True)
