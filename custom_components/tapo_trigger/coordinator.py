from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TapoTriggerClient, parse_privacy_enabled
from .const import CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, LOGGER


class TapoTriggerCoordinator(DataUpdateCoordinator[dict]):
    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: TapoTriggerClient
    ) -> None:
        update_interval = entry.options.get(
            CONF_UPDATE_INTERVAL,
            entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )
        super().__init__(
            hass,
            LOGGER,
            name="Tapo Trigger",
            update_interval=timedelta(seconds=update_interval),
        )
        self.entry = entry
        self.client = client

    async def _async_update_data(self) -> dict:
        try:
            raw = await self.hass.async_add_executor_job(self.client.get_privacy_raw)
        except Exception as err:
            raise UpdateFailed(f"Failed to update privacy status: {err}") from err

        return {
            "raw": raw,
            "enabled": parse_privacy_enabled(raw),
        }

    async def async_set_privacy_enabled(self, enabled: bool) -> None:
        await self.hass.async_add_executor_job(self.client.set_privacy_enabled, enabled)
        await self.async_refresh()