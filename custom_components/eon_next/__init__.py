#!/usr/bin/env python3

from datetime import timedelta
import logging

from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .eonnext import EonNext
from .statistics import HistoricalConsumptionImporter

_LOGGER = logging.getLogger(__name__)

DOMAIN = "eon_next"
CONF_API_KEY = "api_key"
PLATFORMS = [Platform.SENSOR]
HISTORY_UPDATE_INTERVAL = timedelta(hours=12)


async def async_setup_entry(hass, entry):
    """Set up E.ON Next from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api_key = entry.data.get(CONF_API_KEY)
    if not api_key:
        # Entry created by an older version (password or refresh token).
        raise ConfigEntryAuthFailed("An E.ON Next API key is required")

    api = EonNext(async_get_clientsession(hass))
    try:
        success = await api.login_with_api_key(api_key)
    except Exception as err:  # noqa: BLE001 - network/API failure, retry later
        raise ConfigEntryNotReady(f"Unable to reach E.ON Next: {err}") from err

    if not success:
        raise ConfigEntryAuthFailed("E.ON Next rejected the API key")

    hass.data[DOMAIN][entry.entry_id] = api
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    importer = HistoricalConsumptionImporter(hass, api)

    async def async_import_history(_now=None):
        try:
            await importer.async_import()
        except Exception:  # noqa: BLE001 - keep entity updates running on API failure
            _LOGGER.exception("Unable to import E.ON Next consumption history")

    entry.async_create_background_task(
        hass,
        async_import_history(),
        "E.ON Next historical consumption import",
    )
    entry.async_on_unload(
        async_track_time_interval(
            hass, async_import_history, HISTORY_UPDATE_INTERVAL
        )
    )

    return True


async def async_unload_entry(hass, entry) -> bool:
    """Unload an E.ON Next config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    ):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
