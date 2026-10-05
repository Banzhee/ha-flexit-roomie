"""Config flow for Flexit Roomie (EcoVent v1)."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME, CONF_PORT

from .api import RoomieClient, RoomieError
from .const import DEFAULT_NAME, DEFAULT_PORT, DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
    }
)


class FlexitRoomieConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ask for the fan's address, then check that it answers before adding it."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_IP_ADDRESS]
            port = user_input[CONF_PORT]
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()
            try:
                # One retry only, so a wrong address fails the form in ~6s.
                await RoomieClient(host, port, retries=1).get_status()
            except RoomieError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_SCHEMA, user_input
            ),
            errors=errors,
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> ConfigFlowResult:
        """Take over a device from a legacy configuration.yaml block.

        The fan is not contacted here: the YAML setup already worked, so a fan
        that happens to be offline during a restart must not block the move.
        """
        host = import_data[CONF_IP_ADDRESS]
        port = import_data.get(CONF_PORT, DEFAULT_PORT)
        await self.async_set_unique_id(f"{host}:{port}")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=import_data[CONF_NAME],
            data={
                CONF_NAME: import_data[CONF_NAME],
                CONF_IP_ADDRESS: host,
                CONF_PORT: port,
            },
        )
