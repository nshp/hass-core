"""The Lucid Motors integration."""
from __future__ import annotations

from typing import Any

from lucidmotors import LucidAPI, Vehicle

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import LucidDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Lucid Motors from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    api = LucidAPI()
    await api.login(entry.data["username"], entry.data["password"])
    assert api.user is not None

    coordinator = LucidDataUpdateCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class LucidBaseEntity(CoordinatorEntity[LucidDataUpdateCoordinator]):
    """Common base for Lucid vehicle entities."""

    coordinator: LucidDataUpdateCoordinator
    vehicle: Vehicle

    _attr_attribution: str = ATTRIBUTION
    _attr_has_entity_name: bool = True
    _attrs: dict[str, Any]

    def __init__(
        self, coordinator: LucidDataUpdateCoordinator, vehicle: Vehicle
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator)

        self.vehicle = vehicle

        self._attrs = {
            "car": self.vehicle.config.nickname,
            "vin": self.vehicle.config.vin,
        }
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.vehicle.config.vin)},
            manufacturer="Lucid",
            model=self.vehicle.config.model,
            name=self.vehicle.config.nickname,
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()
