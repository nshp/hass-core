"""Switch entities for Lucid vehicles."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
import logging
from typing import Any

from lucidmotors import APIError, LucidAPI, Vehicle
from lucidmotors.vehicle import LightState

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LucidBaseEntity
from .const import DOMAIN
from .coordinator import LucidDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class LucidSwitchEntityDescriptionMixin:
    """Mixin to describe a Lucid Switch entity."""

    key_path: list[str]
    turn_on_function: Callable[[LucidAPI, Vehicle], Coroutine[None, None, None]]
    turn_off_function: Callable[[LucidAPI, Vehicle], Coroutine[None, None, None]]
    on_value: Any
    off_value: Any


@dataclass
class LucidSwitchEntityDescription(
    SwitchEntityDescription, LucidSwitchEntityDescriptionMixin
):
    """Describes Lucid switch entity."""


SWITCH_TYPES: list[LucidSwitchEntityDescription] = [
    LucidSwitchEntityDescription(
        key="headlights",
        key_path=["state", "chassis"],
        translation_key="headlights",
        icon="mdi:car-light-high",
        device_class=SwitchDeviceClass.SWITCH,
        turn_on_function=lambda api, vehicle: api.lights_on(vehicle),
        turn_off_function=lambda api, vehicle: api.lights_off(vehicle),
        on_value=LightState.ON,
        off_value=LightState.OFF,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Lucid sensors from config entry."""
    coordinator: LucidDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[LucidSwitch] = []

    for vehicle in coordinator.api.vehicles:
        entities.extend(
            [
                LucidSwitch(coordinator, vehicle, description)
                for description in SWITCH_TYPES
            ]
        )

    async_add_entities(entities)


class LucidSwitch(LucidBaseEntity, SwitchEntity):
    """Representation of a Lucid vehicle switch."""

    entity_description: LucidSwitchEntityDescription
    _attr_has_entity_name: bool = True

    def __init__(
        self,
        coordinator: LucidDataUpdateCoordinator,
        vehicle: Vehicle,
        description: LucidSwitchEntityDescription,
    ) -> None:
        """Initialize Lucid vehicle switch."""
        super().__init__(coordinator, vehicle)
        self.entity_description = description
        self.api = coordinator.api
        self._attr_unique_id = f"{vehicle.config.vin}-{description.key}"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        try:
            await self.entity_description.turn_on_function(self.api, self.vehicle)
        except APIError as ex:
            raise HomeAssistantError(ex) from ex

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        try:
            await self.entity_description.turn_off_function(self.api, self.vehicle)
        except APIError as ex:
            raise HomeAssistantError(ex) from ex

    @property
    def is_on(self) -> bool:
        """Get the current state of the switch."""
        state = self.vehicle
        for attr in self.entity_description.key_path:
            state = getattr(state, attr)
        state = getattr(state, self.entity_description.key)
        return state == self.entity_description.on_value
