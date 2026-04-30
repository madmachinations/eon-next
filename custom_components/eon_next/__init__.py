#!/usr/bin/env python3

import logging
from .eonnext import EonNext

_LOGGER = logging.getLogger(__name__)

DOMAIN = "eon_next"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"


async def async_setup_entry(hass, entry):
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    api = EonNext()
    success = await api.login_with_username_and_password(entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])

    if success == True:
        # Load account data from EON API (use name-mangled private method)
        await api._EonNext__init_accounts()
        
        hass.data[DOMAIN][entry.entry_id] = api

        await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

        return True
    
    else:
        return False