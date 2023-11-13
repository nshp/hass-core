"""Support for reading vehicle status from Lucid API."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
import logging
from typing import cast

from lucidmotors import Vehicle

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import LENGTH, PERCENTAGE, UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import LucidBaseEntity
from .const import DOMAIN
from .coordinator import LucidDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class LucidSensorEntityDescription(SensorEntityDescription):
    """Describes Lucid sensor entity."""

    key_path: list[str] = field(default_factory=list)
    unit_type: str | None = None
    value: Callable = lambda x, y: x


SENSOR_TYPES: dict[str, LucidSensorEntityDescription] = {
    "charging_target": LucidSensorEntityDescription(
        key="charge_limit_percent",
        key_path=["state", "charging"],
        translation_key="charging_target",
        icon="mdi:battery-charging-high",
        unit_type=PERCENTAGE,
        suggested_display_precision=0,
    ),
    "remaining_battery_percent": LucidSensorEntityDescription(
        key="charge_percent",
        key_path=["state", "battery"],
        translation_key="remaining_battery_percent",
        unit_type=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    "remaining_range": LucidSensorEntityDescription(
        key="range_miles",
        key_path=["state", "battery"],
        translation_key="remaining_range",
        icon="mdi:map-marker-distance",
        unit_type=LENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.MILES,
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Lucid sensors from config entry."""
    coordinator: LucidDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[LucidSensor] = []

    for vehicle in coordinator.api.vehicles:
        entities.extend(
            [
                LucidSensor(coordinator, vehicle, description)
                for (attribute_name, description) in SENSOR_TYPES.items()
            ]
        )

    async_add_entities(entities)


class LucidSensor(LucidBaseEntity, SensorEntity):
    """Representation of a Lucid vehicle sensor."""

    entity_description: LucidSensorEntityDescription
    _attr_has_entity_name: bool = True

    def __init__(
        self,
        coordinator: LucidDataUpdateCoordinator,
        vehicle: Vehicle,
        description: LucidSensorEntityDescription,
    ) -> None:
        """Initialize Lucid vehicle sensor."""
        super().__init__(coordinator, vehicle)
        self.entity_description = description
        self._attr_unique_id = f"{vehicle.config.vin}-{description.key}"

        # Set the correct unit of measurement based on the unit_type
        if description.unit_type:
            self._attr_native_unit_of_measurement = (
                coordinator.hass.config.units.as_dict().get(description.unit_type)
                or description.unit_type
            )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug(
            "Updating sensor '%s' of %s",
            self.entity_description.key,
            self.vehicle.config.nickname,
        )
        state = self.vehicle
        for attr in self.entity_description.key_path:
            state = getattr(state, attr)
        state = getattr(state, self.entity_description.key)
        self._attr_native_value = cast(
            StateType, self.entity_description.value(state, self.hass)
        )
        super()._handle_coordinator_update()

    @property
    def translation_key(self) -> str | None:
        """Return the translation key to translate the entity's states."""
        return self.entity_description.translation_key
