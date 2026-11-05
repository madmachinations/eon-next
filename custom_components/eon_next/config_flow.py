"""Config flow to configure Eon Next."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .eonnext import EonNext
from . import DOMAIN, CONF_API_KEY

_LOGGER = logging.getLogger(__name__)

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        )
    }
)


class EonNextConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle eon next config flow."""

    VERSION = 1

    async def _async_validate(self, api_key: str) -> str | None:
        """Return an error key, or None if the API key is accepted."""
        en = EonNext(async_get_clientsession(self.hass))
        try:
            if await en.login_with_api_key(api_key.strip(), initialise=False):
                return None
            return "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected exception during E.ON Next API key authentication")
            return "cannot_connect"

    async def async_step_user(self, user_input=None):
        """Invoked when a user initiates a flow via the user interface."""
        errors = {}
        if user_input is not None:
            error = await self._async_validate(user_input[CONF_API_KEY])
            if error is None:
                return self.async_create_entry(
                    title="E.ON Next",
                    data={CONF_API_KEY: user_input[CONF_API_KEY].strip()},
                )
            errors["base"] = error

        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)

    async def async_step_reauth(self, entry_data):
        """Start re-authentication (e.g. an old entry without an API key)."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Ask for a new API key."""
        errors = {}
        if user_input is not None:
            error = await self._async_validate(user_input[CONF_API_KEY])
            if error is None:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data={CONF_API_KEY: user_input[CONF_API_KEY].strip()},
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="reauth_confirm", data_schema=SCHEMA, errors=errors
        )
