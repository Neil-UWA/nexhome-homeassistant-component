import asyncio
import logging
from .const import DOMAIN, DEVICES, SIGNAL_PUSH_UPDATE
from .utils import format_upd_mes
from homeassistant.helpers.dispatcher import async_dispatcher_send

_LOGGER = logging.getLogger(__name__)


class UDPListener(asyncio.DatagramProtocol):
    """UDP 监听器，接收网关推送的设备状态变化通知。"""

    def __init__(self, hass):
        self.hass = hass
        self._transport = None

    async def start(self):
        """启动 UDP 监听。"""
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: self, local_addr=("0.0.0.0", 1912), reuse_port=True
        )
        self._transport = transport
        _LOGGER.info("Nexhome UDP 推送监听已启动（端口 1912）")

    def close(self):
        """关闭 UDP 监听。"""
        if self._transport is not None:
            self._transport.close()
            self._transport = None
        _LOGGER.info("Nexhome UDP 推送监听已关闭")

    def datagram_received(self, data, addr):
        """处理收到的 UDP 数据报，解析设备状态并分发给实体。"""
        try:
            _content, headers = format_upd_mes(data)
            model_info = headers.get("MODEL")
            if not model_info:
                return

            # 解析 MODEL 中的键值对: address=xxx&identifier=yyy&value=zzz
            model_params = {}
            for param in model_info.split("&"):
                if "=" not in param:
                    continue
                key, value = param.split("=", 1)
                model_params[key] = value

            address = model_params.get("address")
            identifier = model_params.get("identifier")
            value = model_params.get("value")

            if not address or not identifier:
                return

            _LOGGER.debug(
                "UDP 推送: 设备 %s, %s = %s", address, identifier, value
            )

            # 通过 dispatcher 分发状态更新信号给对应设备的所有实体
            signal = f"{SIGNAL_PUSH_UPDATE}_{address}"
            async_dispatcher_send(
                self.hass,
                signal,
                [{"identifier": identifier, "value": value}],
            )
        except Exception:
            _LOGGER.debug("解析 UDP 推送数据失败", exc_info=True)