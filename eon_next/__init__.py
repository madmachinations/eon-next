#!/usr/bin/env python3

import logging
from .eonnext import EonNext

_LOGGER = logging.getLogger(__name__)

DOMAIN = "eon_next"
CONF_REFRESH_TOKEN = "refresh_token"


async def async_setup_entry(hass, entry):
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    api = EonNext()
    success = await api.login_with_refresh_token(entry.data[CONF_REFRESH_TOKEN])

    if success == True:

        hass.data[DOMAIN][entry.entry_id] = api

        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, "sensor")
        )

        return True
    
    else:
        return False