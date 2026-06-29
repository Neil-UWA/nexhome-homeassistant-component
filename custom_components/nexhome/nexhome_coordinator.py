import asyncio
import logging
from datetime import timedelta
import async_timeout

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, TIME_NUMBER, TIME_NUMBER_PUSH_FALLBACK

_LOGGER = logging.getLogger(__name__)

class NexhomeCoordinator(DataUpdateCoordinator):
    """Manages polling for state changes from the device.
    
    When push mode is enabled (UDP), the poll interval is increased to
    TIME_NUMBER_PUSH_FALLBACK (60s) as a heartbeat/sync mechanism.
    When push mode is disabled, the original TIME_NUMBER (3s) interval is used.
    """

    def __init__(self, hass, tool, params, update_interval=None, push_enabled=False):
        """Initialize the data update coordinator.
        
        Args:
            hass: Home Assistant instance
            tool: ServiceTool instance
            params: Parameters for device property query
            update_interval: Update interval in seconds (default: auto based on push_enabled)
            push_enabled: Whether push-based updates are active
        """
        if update_interval is None:
            update_interval = TIME_NUMBER_PUSH_FALLBACK if push_enabled else TIME_NUMBER
        DataUpdateCoordinator.__init__(
            self,
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        self._tool = tool
        self._params = params
        self._results = {}

    async def _async_update_data(self):
        try:
            device_property = await self._tool.getProperties(self.hass, self._params)
            if device_property:
                return device_property
            else:
                return False
        except Exception as err:
            return False
