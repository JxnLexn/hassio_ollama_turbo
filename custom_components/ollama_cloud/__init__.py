"""Home Assistant integration for Ollama Cloud."""
from __future__ import annotations

from dataclasses import dataclass

from ollama import Client

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_HOST,
    CONF_MODEL,
    CONF_SYSTEM_PROMPT,
    DEFAULT_HOST,
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_PROMPT,
    DOMAIN,
    SIGNAL_RUNTIME_DATA_UPDATED,
)

PLATFORMS = [Platform.CONVERSATION]


@dataclass
class OllamaCloudRuntimeData:
    """Runtime data for an Ollama Cloud entry."""

    client: Client
    model: str
    system_prompt: str


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Ollama Cloud component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ollama Cloud from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    runtime_data = _build_runtime_data(entry)
    hass.data[DOMAIN][entry.entry_id] = runtime_data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Ollama Cloud config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle updates to the config entry options."""
    runtime_data = _build_runtime_data(entry)
    hass.data[DOMAIN][entry.entry_id] = runtime_data
    async_dispatcher_send(
        hass, f"{DOMAIN}_{entry.entry_id}_{SIGNAL_RUNTIME_DATA_UPDATED}", runtime_data
    )


def _build_runtime_data(entry: ConfigEntry) -> OllamaCloudRuntimeData:
    """Build runtime data for a config entry."""
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

    return OllamaCloudRuntimeData(client=client, model=model, system_prompt=system_prompt)
