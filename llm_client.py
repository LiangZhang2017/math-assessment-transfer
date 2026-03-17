"""Azure OpenAI client for problem-solving and assessment conditions."""
from openai import AzureOpenAI

import config

def get_client() -> AzureOpenAI:
    """Build Azure OpenAI client from config."""
    return AzureOpenAI(
        api_key=config.AZURE_OPENAI_API_KEY,
        api_version=config.AZURE_OPENAI_VERSION,
        azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
    )


def _is_reasoning_model(deployment: str) -> bool:
    """True if this deployment is a reasoning-style model (e.g. gpt-5-tp) with different API params."""
    d = (deployment or "").strip().lower()
    return d in config.AZURE_OPENAI_REASONING_MODELS


def chat_completion(
    client: AzureOpenAI,
    messages: list[dict],
    *,
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> str:
    """Call Azure OpenAI chat completion. Uses config.AZURE_OPENAI_MODEL if model is None.
    For reasoning models (e.g. gpt-5-tp): only model, messages, max_completion_tokens (no temperature, no max_tokens).
    For other models: model, messages, temperature, max_tokens.
    """
    deployment = model or config.AZURE_OPENAI_MODEL
    if _is_reasoning_model(deployment):
        # Reasoning model: only params this model supports; use max_completion_tokens via extra_body
        resp = client.chat.completions.create(
            model=deployment,
            messages=messages,
            extra_body={"max_completion_tokens": max_tokens},
        )
    else:
        resp = client.chat.completions.create(
            model=deployment,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    return (resp.choices[0].message.content or "").strip()
