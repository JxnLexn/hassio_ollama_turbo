"""Home Assistant integration for Ollama Cloud."""
from __future__ import annotations

import logging

from ollama import Client

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_HOST,
    CONF_MODEL,
    CONF_SYSTEM_PROMPT,
    DEFAULT_HOST,
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_PROMPT,
    DOMAIN,
)
from .conversation import OllamaCloudAgent

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Ollama Cloud component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ollama Cloud from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    data = entry.data
    options = entry.options

    host = options.get(CONF_HOST, data.get(CONF_HOST, DEFAULT_HOST))
    model = options.get(CONF_MODEL, data.get(CONF_MODEL, DEFAULT_MODEL))
    system_prompt = options.get(
        CONF_SYSTEM_PROMPT, data.get(CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT)
    )

    api_key = data[CONF_API_KEY]

    client = Client(
        host=host,
        headers={"Authorization": f"Bearer {api_key}"},
    )

    agent = OllamaCloudAgent(
        hass=hass,
        entry=entry,
        client=client,
        model=model,
        system_prompt=system_prompt,
    )

    hass.data[DOMAIN][entry.entry_id] = agent

    await agent.async_initialize()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Ollama Cloud config entry."""
    agent: OllamaCloudAgent | None = hass.data[DOMAIN].pop(entry.entry_id, None)
    if agent is None:
        return True

    await agent.async_unload()
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle updates to the config entry options."""
    agent: OllamaCloudAgent | None = hass.data[DOMAIN].get(entry.entry_id)
    if agent is None:
        return

    data = entry.data
    options = entry.options

    host = options.get(CONF_HOST, data.get(CONF_HOST, DEFAULT_HOST))
    model = options.get(CONF_MODEL, data.get(CONF_MODEL, DEFAULT_MODEL))
    system_prompt = options.get(
        CONF_SYSTEM_PROMPT, data.get(CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT)
    )

    api_key = data[CONF_API_KEY]

    client = Client(
        host=host,
        headers={"Authorization": f"Bearer {api_key}"},
    )

    agent.update_client(client)
    agent.update_model(model)
    agent.update_system_prompt(system_prompt)
