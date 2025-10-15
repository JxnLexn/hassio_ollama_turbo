# Home Assistant Ollama Cloud Integration

This custom integration allows Home Assistant to talk to the Ollama Cloud (formerly Ollama Turbo) API so that Assist, conversation agents, and AI-powered automations can use Ollama hosted language models.

## Features

- Conversation agent that plugs into Home Assistant Assist.
- Config flow with OAuth-like API key entry.
- Support for choosing the Ollama Cloud model, endpoint, and system prompt.
- Conversation memory per conversation session.

## Installation

### HACS (recommended)

1. Ensure you have [HACS](https://hacs.xyz/) installed in your Home Assistant instance.
2. In HACS, add this repository as a **Custom Repository** of type *Integration* and download **Ollama Cloud**.
3. Restart Home Assistant once the download completes.
4. Add the **Ollama Cloud** integration from the Settings → Devices & Services screen.
5. Provide your Ollama Cloud API key, optional endpoint, model, and system prompt.

### Manual

1. Copy the `custom_components/ollama_cloud` folder into your Home Assistant `config/custom_components` directory.
2. Restart Home Assistant.
3. Add the **Ollama Cloud** integration from the Settings → Devices & Services screen.
4. Provide your Ollama Cloud API key, optional endpoint, model, and system prompt.

## Usage

Once configured, the integration registers an Ollama-powered conversation agent that can be used with Assist, voice assistants, and automations using the `conversation.process` service.

The integration uses the [`ollama` Python library](https://pypi.org/project/ollama/) to communicate with the cloud endpoint.
