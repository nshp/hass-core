"""Test fixtures for caldav."""
from collections.abc import Awaitable, Callable
from unittest.mock import Mock, patch

import pytest

from homeassistant.components.caldav.const import DOMAIN
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    Platform,
)
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry

TEST_URL = "https://example.com/url-1"
TEST_USERNAME = "username-1"
TEST_PASSWORD = "password-1"


@pytest.fixture(name="platforms")
def mock_platforms() -> list[Platform]:
    """Fixture to specify platforms to test."""
    return []


@pytest.fixture(name="calendars")
def mock_calendars() -> list[Mock]:
    """Fixture to provide calendars returned by CalDAV client."""
    return []


@pytest.fixture(name="dav_client", autouse=True)
def mock_dav_client(calendars: list[Mock]) -> Mock:
    """Fixture to mock the DAVClient."""
    with patch(
        "homeassistant.components.caldav.calendar.caldav.DAVClient"
    ) as mock_client:
        mock_client.return_value.principal.return_value.calendars.return_value = (
            calendars
        )
        yield mock_client


@pytest.fixture(name="config_entry")
def mock_config_entry() -> MockConfigEntry:
    """Fixture for a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_URL: TEST_URL,
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
            CONF_VERIFY_SSL: True,
        },
    )


@pytest.fixture(name="setup_integration")
async def mock_setup_integration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    platforms: list[str],
) -> Callable[[], Awaitable[bool]]:
    """Fixture to set up the integration."""
    config_entry.add_to_hass(hass)

    async def run() -> bool:
        with patch(f"homeassistant.components.{DOMAIN}.PLATFORMS", platforms):
            result = await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()
            return result

    return run
