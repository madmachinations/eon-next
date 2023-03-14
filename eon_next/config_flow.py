"""Config flow to configure Eon Next."""
from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

from .eonnext import EonNext

from . import DOMAIN, CONF_REFRESH_TOKEN

_LOGGER = logging.getLogger(__name__)


class EonNextConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle eon next config flow."""

    VERSION = 1

    def __init__(self) -> None:
        pass


    async def async_step_user(self, user_input=None):
        """Invoked when a user initiates a flow via the user interface."""

        errors = {}
        if user_input is not None:

            en = EonNext()
            success = await en.login_with_username_and_password(
                user_input['email'],
                user_input['password'],
                False
            )

            if success == True:

                return self.async_create_entry(title="Eon Next", data={
                    CONF_REFRESH_TOKEN: en.auth['refresh']['token']
                })
                
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required("email"): cv.string,
            vol.Required("password"): cv.string
        }), errors=errors)