from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .api import TapoTriggerClient, async_is_klap
from .const import (
    CONF_CLOUD_PASSWORD,
    CONF_KLAP,
    CONF_UPDATE_INTERVAL,
    DEFAULT_CONTROL_PORT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)


class CannotConnect(Exception):
    pass


class InvalidAuth(Exception):
    pass


async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    if not data.get(CONF_CLOUD_PASSWORD) and not (
        data.get(CONF_USERNAME) and data.get(CONF_PASSWORD)
    ):
        raise ValueError("missing_auth")

    port = data[CONF_PORT]
    klap = False
    if port == DEFAULT_CONTROL_PORT and await async_is_klap(hass, data[CONF_HOST], 80):
        port = 80
        klap = True
    elif port == 80:
        klap = True
    elif port != DEFAULT_CONTROL_PORT:
        klap = await async_is_klap(hass, data[CONF_HOST], port)

    validated = {
        CONF_HOST: data[CONF_HOST],
        CONF_PORT: port,
        CONF_KLAP: klap,
        CONF_USERNAME: data.get(CONF_USERNAME, ""),
        CONF_PASSWORD: data.get(CONF_PASSWORD, ""),
        CONF_CLOUD_PASSWORD: data.get(CONF_CLOUD_PASSWORD, ""),
    }

    client = await hass.async_add_executor_job(TapoTriggerClient, hass, validated)
    try:
        await hass.async_add_executor_job(client.get_privacy_enabled)
    except Exception as err:
        await hass.async_add_executor_job(client.close)
        message = str(err).lower()
        if "auth" in message or "password" in message:
            raise InvalidAuth from err
        raise CannotConnect from err

    await hass.async_add_executor_job(client.close)
    return validated


class TapoTriggerConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        return TapoTriggerOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            try:
                data = await validate_input(self.hass, user_input)
            except ValueError:
                errors["base"] = "missing_auth"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=data[CONF_HOST], data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_CONTROL_PORT): int,
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
                vol.Optional(CONF_USERNAME): str,
                vol.Optional(CONF_PASSWORD): str,
                vol.Optional(CONF_CLOUD_PASSWORD): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class TapoTriggerOptionsFlow(OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self._config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            self._config_entry.data.get(
                CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
            ),
        )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=current_interval
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600))
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)