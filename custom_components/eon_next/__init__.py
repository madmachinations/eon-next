#!/usr/bin/env python3

from datetime import timedelta
import logging

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .eonnext import EonNext
from .statistics import HistoricalConsumptionImporter

_LOGGER = logging.getLogger(__name__)

DOMAIN = "eon_next"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
PLATFORMS = [Platform.SENSOR]
HISTORY_UPDATE_INTERVAL = timedelta(hours=12)


async def async_setup_entry(hass, entry):
    """Set up E.ON Next from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api = EonNext(async_get_clientsession(hass))
    if not await api.login_with_username_and_password(
        entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD]
    ):
        return False

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
