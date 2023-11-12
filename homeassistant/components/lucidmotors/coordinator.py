"""Coordinator for Lucid."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from lucidmotors import APIError, LucidAPI

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)


class LucidDataUpdateCoordinator(DataUpdateCoordinator):
    """Lucid API update coordinator."""

    api: LucidAPI

    def __init__(self, hass: HomeAssistant, api: LucidAPI) -> None:
        """Initialize the Lucid data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"Lucid account {api.user.username}",
            update_interval=timedelta(seconds=30),
        )
        self.api = api

    async def _async_update_data(self) -> None:
        """Fetch new data from API."""
        try:
            async with asyncio.timeout(10):
                return await self.api.fetch_vehicles()
        except APIError as err:
            if err.code == 16:  # token expired
                raise ConfigEntryAuthFailed from err
            raise UpdateFailed(f"Error communicating with API: {err}") from err
