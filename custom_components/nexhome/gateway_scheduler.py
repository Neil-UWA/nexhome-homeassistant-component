"""网关请求调度器 - 控制优先，轮询让路。

网关吞吐有限，HA 侧即使全部异步，大量轮询请求仍会在网关侧与控制请求竞争。
本调度器负责：
1. 控制请求进行中及结束后的短时间内暂停轮询（控制优先）；
2. 轮询请求全局串行，并在相邻轮询之间留出间隔（错峰，避免同一时刻突发）。
"""
import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor

from .const import (
    DOMAIN, CONTROL_EXECUTOR, POLL_EXECUTOR, GATEWAY_SCHEDULER,
    CONTROL_POLL_PAUSE_SECONDS, POLL_MIN_GAP_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

# 轮询因控制优先而被跳过时的返回值
POLL_SKIPPED = object()


class GatewayScheduler:
    def __init__(self, hass):
        self.hass = hass
        self._poll_lock = asyncio.Lock()
        self._controls_in_flight = 0
        self._pause_until = 0.0

    def polls_paused(self) -> bool:
        return self._controls_in_flight > 0 or time.monotonic() < self._pause_until

    async def async_control(self, func, *args):
        """以最高优先级发送控制请求，期间及之后短时间内暂停轮询。"""
        self._controls_in_flight += 1
        self._pause_until = time.monotonic() + CONTROL_POLL_PAUSE_SECONDS
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(self._control_executor(), func, *args)
        finally:
            self._controls_in_flight -= 1
            # 从控制完成时刻重新计时，给连续操作（如拖动滑块）留出窗口
            self._pause_until = time.monotonic() + CONTROL_POLL_PAUSE_SECONDS

    async def async_poll(self, func, *args):
        """串行执行轮询请求；若有控制请求正在进行/刚结束则跳过，返回 POLL_SKIPPED。"""
        if self.polls_paused():
            return POLL_SKIPPED
        async with self._poll_lock:
            # 排队等待期间可能有控制请求插入，需再次检查
            if self.polls_paused():
                return POLL_SKIPPED
            loop = asyncio.get_running_loop()
            try:
                return await loop.run_in_executor(self._poll_executor(), func, *args)
            finally:
                # 相邻轮询间留出空隙，避免占满网关
                await asyncio.sleep(POLL_MIN_GAP_SECONDS)

    def _control_executor(self) -> ThreadPoolExecutor:
        return self._executor(CONTROL_EXECUTOR, 4, "nexhome-control")

    def _poll_executor(self) -> ThreadPoolExecutor:
        return self._executor(POLL_EXECUTOR, 1, "nexhome-poll")

    def _executor(self, key, max_workers, prefix) -> ThreadPoolExecutor:
        domain_data = self.hass.data.setdefault(DOMAIN, {})
        executor = domain_data.get(key)
        if executor is None:
            executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix=prefix)
            domain_data[key] = executor
        return executor


def get_gateway_scheduler(hass) -> GatewayScheduler:
    domain_data = hass.data.setdefault(DOMAIN, {})
    scheduler = domain_data.get(GATEWAY_SCHEDULER)
    if scheduler is None:
        scheduler = GatewayScheduler(hass)
        domain_data[GATEWAY_SCHEDULER] = scheduler
    return scheduler
