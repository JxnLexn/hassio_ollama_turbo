"""Conversation agent for the Ollama Cloud integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List

from ollama import Client

from homeassistant.components import conversation
from homeassistant.components.conversation import (  # noqa: F401
    AbstractConversationAgent,
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import CONF_MODEL, CONF_SYSTEM_PROMPT, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class ConversationMemory:
    """Keep the state of a conversation."""

    messages: List[Dict[str, str]] = field(default_factory=list)


class OllamaCloudAgent(AbstractConversationAgent):
    """Represent an Ollama Cloud powered conversation agent."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: Client,
        model: str,
        system_prompt: str,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self._client = client
        self._model = model
        self._system_prompt = system_prompt
        self._memories: dict[str, ConversationMemory] = {}

    async def async_initialize(self) -> None:
        """Register the agent with Home Assistant."""
        conversation.async_set_agent(self.hass, self.entry, self)
        _LOGGER.debug("Ollama Cloud agent initialized for entry %s", self.entry.entry_id)

    async def async_unload(self) -> None:
        """Unload the agent and clean up resources."""
        conversation.async_unset_agent(self.hass, self.entry.entry_id)
        self._memories.clear()
        _LOGGER.debug("Ollama Cloud agent unloaded for entry %s", self.entry.entry_id)

    @property
    def attribution(self) -> str | None:
        return "Powered by Ollama Cloud"

    @property
    def supported_languages(self) -> list[str] | None:
        return None

    @property
    def model(self) -> str | None:  # type: ignore[override]
        return self._model

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        """Process a conversation turn."""
        conversation_id = user_input.conversation_id or self.entry.entry_id
        memory = self._memories.setdefault(conversation_id, ConversationMemory())

        messages: list[dict[str, str]] = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})

        messages.extend(memory.messages)
        messages.append({"role": "user", "content": user_input.text})

        _LOGGER.debug(
            "Sending %s messages to Ollama Cloud model %s", len(messages), self._model
        )

        response = await self.hass.async_add_executor_job(
            self._client.chat,
            self._model,
            messages,
        )

        content: str = response.get("message", {}).get("content", "")
        if not content:
            _LOGGER.warning("Received empty response from Ollama Cloud")
            content = "I was unable to generate a response right now."

        memory.messages.extend(
            [
                {"role": "user", "content": user_input.text},
                {"role": "assistant", "content": content},
            ]
        )

        return conversation.ConversationResult(
            response=conversation.ConversationResponse(text=content)
        )

    @callback
    def update_client(self, client: Client) -> None:
        """Replace the underlying Ollama client."""
        self._client = client

    @callback
    def update_model(self, model: str) -> None:
        """Update the model used by the agent."""
        self._model = model

    @callback
    def update_system_prompt(self, system_prompt: str) -> None:
        """Update the system prompt."""
        self._system_prompt = system_prompt

