from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, SWITCH_NAME
from .coordinator import TapoTriggerCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TapoTriggerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TapoPrivacySwitch(entry, coordinator)])


class TapoPrivacySwitch(CoordinatorEntity[TapoTriggerCoordinator], SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = SWITCH_NAME

    def __init__(self, entry: ConfigEntry, coordinator: TapoTriggerCoordinator) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_privacy"

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            "manufacturer": MANUFACTURER,
            "configuration_url": f"http://{self._entry.data[CONF_HOST]}",
        }

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data["enabled"])

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_privacy_enabled(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_privacy_enabled(False)