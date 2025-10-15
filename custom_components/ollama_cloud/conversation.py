"""Conversation platform for the Ollama Cloud integration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from ollama import Client

from homeassistant.components import assist_pipeline, conversation
from homeassistant.components.conversation import (
    AbstractConversationAgent,
    ConversationEntity,
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

from . import OllamaCloudRuntimeData
from .const import DOMAIN, SIGNAL_RUNTIME_DATA_UPDATED, TITLE


@dataclass
class ConversationMemory:
    """Keep the state of a conversation."""

    messages: List[Dict[str, str]] = field(default_factory=list)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Ollama Cloud conversation entity."""
    runtime_data: OllamaCloudRuntimeData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OllamaCloudConversationEntity(entry, runtime_data)])


class OllamaCloudConversationEntity(
    ConversationEntity, AbstractConversationAgent
):
    """Represent an Ollama Cloud powered conversation entity."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self, entry: ConfigEntry, runtime_data: OllamaCloudRuntimeData
    ) -> None:
        self.entry = entry
        self._client = runtime_data.client
        self._model = runtime_data.model
        self._system_prompt = runtime_data.system_prompt
        self._memories: dict[str, ConversationMemory] = {}
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Ollama",
            model=self._model,
            name=TITLE,
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def supported_languages(self) -> list[str] | str:
        """Return supported languages."""
        return MATCH_ALL

    @property
    def model(self) -> str | None:  # type: ignore[override]
        """Return the active model identifier."""
        return self._model

    async def async_added_to_hass(self) -> None:
        """Handle entity being added to Home Assistant."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_{self.entry.entry_id}_{SIGNAL_RUNTIME_DATA_UPDATED}",
                self._async_handle_runtime_update,
            )
        )
        assist_pipeline.async_migrate_engine(
            self.hass, conversation.DOMAIN, self.entry.entry_id, self.entity_id
        )
        conversation.async_set_agent(self.hass, self.entry, self)

    async def async_will_remove_from_hass(self) -> None:
        """Handle removal from Home Assistant."""
        conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        """Process a conversation turn."""
        conversation_id = user_input.conversation_id or ulid.ulid_now()
        memory = self._memories.setdefault(conversation_id, ConversationMemory())

        messages: list[dict[str, str]] = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})

        messages.extend(memory.messages)
        messages.append({"role": "user", "content": user_input.text})

        response = await self.hass.async_add_executor_job(
            _chat_with_client,
            self._client,
            self._model,
            messages,
        )

        content: str = response.get("message", {}).get("content", "")
        if not content:
            content = "I was unable to generate a response right now."

        memory.messages.extend(
            [
                {"role": "user", "content": user_input.text},
                {"role": "assistant", "content": content},
            ]
        )

        return conversation.ConversationResult(
            response=conversation.ConversationResponse(text=content),
            conversation_id=conversation_id,
        )

    @callback
    def _async_handle_runtime_update(
        self, runtime_data: OllamaCloudRuntimeData
    ) -> None:
        """Handle runtime data updates from the config entry."""
        self._client = runtime_data.client
        self._model = runtime_data.model
        self._system_prompt = runtime_data.system_prompt


def _chat_with_client(client: Client, model: str, messages: list[dict[str, str]]) -> dict:
    """Call the Ollama client chat API synchronously."""
    return client.chat(model, messages=messages)
