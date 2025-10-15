"""Config flow for Ollama Cloud integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from ollama import Client

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_HOST,
    CONF_MODEL,
    CONF_SYSTEM_PROMPT,
    DEFAULT_HOST,
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_PROMPT,
    DOMAIN,
    TITLE,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    host: str = data.get(CONF_HOST, DEFAULT_HOST)
    api_key: str = data[CONF_API_KEY]
    model: str = data.get(CONF_MODEL, DEFAULT_MODEL)

    def _do_validation() -> None:
        client = Client(host=host, headers={"Authorization": f"Bearer {api_key}"})
        response = client.chat(
            model,
            [
                {
                    "role": "user",
                    "content": "Say 'connected' if you can read this.",
                }
            ],
        )
        message = response.get("message", {}).get("content", "")
        if "connected" not in message.lower():
            raise ValueError("unexpected_response")

    await hass.async_add_executor_job(_do_validation)

    return {"title": TITLE}


class OllamaCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ollama Cloud."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await _validate_input(self.hass, user_input)
            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error validating Ollama Cloud input")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_HOST, default=DEFAULT_HOST): str,
                vol.Optional(CONF_MODEL, default=DEFAULT_MODEL): str,
                vol.Optional(CONF_SYSTEM_PROMPT, default=DEFAULT_SYSTEM_PROMPT): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    async def async_step_reauth(self, user_input: dict[str, Any]) -> FlowResult:
        """Handle re-authentication if credentials fail."""
        return await self.async_step_user(user_input)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return OllamaCloudOptionsFlow(config_entry)


class OllamaCloudOptionsFlow(config_entries.OptionsFlow):
    """Handle an options flow for Ollama Cloud."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            data = {**self.config_entry.data, **user_input}
            try:
                await _validate_input(self.hass, data)
            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error validating Ollama Cloud options")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_HOST,
                    default=self.config_entry.options.get(
                        CONF_HOST,
                        self.config_entry.data.get(CONF_HOST, DEFAULT_HOST),
                    ),
                ): str,
                vol.Optional(
                    CONF_MODEL,
                    default=self.config_entry.options.get(
                        CONF_MODEL,
                        self.config_entry.data.get(CONF_MODEL, DEFAULT_MODEL),
                    ),
                ): str,
                vol.Optional(
                    CONF_SYSTEM_PROMPT,
                    default=self.config_entry.options.get(
                        CONF_SYSTEM_PROMPT,
                        self.config_entry.data.get(
                            CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT
                        ),
                    ),
                ): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema, errors=errors)
