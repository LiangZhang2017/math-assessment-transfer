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

def chat_completion(
    client: AzureOpenAI,
    messages: list[dict],
    *,
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> str:
    """Call Azure OpenAI chat completion. Uses config.AZURE_OPENAI_MODEL if model is None."""
    deployment = model or config.AZURE_OPENAI_MODEL
    resp = client.chat.completions.create(
        model=deployment,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()
