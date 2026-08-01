from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings
from app.services.errors import ConfigurationError, GenerationError, ResearchFlowError


def _usable_secret(value: str | None) -> str:
    secret = (value or "").strip()
    placeholder_markers = ("your_", "replace_", "example", "placeholder")
    if not secret or any(marker in secret.lower() for marker in placeholder_markers):
        return ""
    return secret


def _get_openai_compatible_client():
    api_key = _usable_secret(settings.openai_compatible_api_key) or _usable_secret(settings.openai_api_key)
    if not api_key:
        raise ConfigurationError("OPENAI_COMPATIBLE_API_KEY or OPENAI_API_KEY is missing for OpenAI-compatible generation.")
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise ConfigurationError("OpenAI SDK is not installed in the current runtime.") from exc

    base_url = settings.openai_compatible_base_url.strip() or None
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _extract_json_block(text: str) -> str:
    fenced_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced_match:
        return fenced_match.group(1).strip()

    text = text.strip()
    for opening, closing in (("{", "}"), ("[", "]")):
        start = text.find(opening)
        end = text.rfind(closing)
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
    return text


def _run_openai_compatible(system_prompt: str, user_prompt: str) -> str:
    model = settings.openai_compatible_model.strip() or settings.model_name
    try:
        response = _get_openai_compatible_client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise GenerationError("The language model returned an empty response.")
        return text
    except ResearchFlowError:
        raise
    except Exception as exc:
        error_type = type(exc).__name__
        if error_type in {"OpenAIError", "APIError", "AuthenticationError", "RateLimitError", "BadRequestError"}:
            raise GenerationError(
                "OpenAI-compatible request failed while generating the research workflow output.",
                str(exc),
            ) from exc
        raise GenerationError(
            "Unexpected OpenAI-compatible language model failure while generating the research workflow output.",
            str(exc),
        ) from exc


def _run_gemini(system_prompt: str, user_prompt: str) -> str:
    gemini_api_key = _usable_secret(settings.gemini_api_key)
    if not gemini_api_key:
        raise ConfigurationError("GEMINI_API_KEY is missing for Gemini-based generation.")

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "text/plain",
        },
    }
    model = settings.gemini_model.strip() or settings.model_name
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.provider_timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        normalized_detail = detail.lower()
        if exc.code == 429 or "quota exceeded" in normalized_detail or "resource_exhausted" in normalized_detail:
            raise GenerationError(
                "Gemini quota exceeded. Please wait and retry, or switch to another key/provider.",
                detail or str(exc),
            ) from exc
        raise GenerationError(
            "Gemini request failed while generating the research workflow output.",
            detail or str(exc),
        ) from exc
    except URLError as exc:
        raise GenerationError(
            "Gemini request could not reach the provider endpoint.",
            str(exc),
        ) from exc
    except Exception as exc:
        raise GenerationError(
            "Unexpected language model failure while generating the research workflow output.",
            str(exc),
        ) from exc

    candidates = body.get("candidates") or []
    if not candidates:
        raise GenerationError("Gemini returned no candidate content.")

    parts = []
    for part in candidates[0].get("content", {}).get("parts", []):
        text = str(part.get("text") or "").strip()
        if text:
            parts.append(text)

    text = "\n".join(parts).strip()
    if not text:
        raise GenerationError("Gemini returned an empty response.")
    return text


def _provider_order() -> list[str]:
    provider = settings.llm_provider.strip().lower()
    if provider == "gemini":
        return ["gemini", "openai_compatible"]
    if provider in {"openai", "openai_compatible", "openai-compatible"}:
        return ["openai_compatible", "gemini"]
    if provider == "auto":
        return ["gemini", "openai_compatible"]
    raise ConfigurationError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


def _provider_configured(provider: str) -> bool:
    if provider == "gemini":
        return bool(_usable_secret(settings.gemini_api_key))
    if provider == "openai_compatible":
        return bool(_usable_secret(settings.openai_compatible_api_key) or _usable_secret(settings.openai_api_key))
    return False


def _run_provider(provider: str, system_prompt: str, user_prompt: str) -> str:
    if provider == "gemini":
        return _run_gemini(system_prompt, user_prompt)
    if provider == "openai_compatible":
        return _run_openai_compatible(system_prompt, user_prompt)
    raise ConfigurationError(f"Unsupported LLM provider adapter: {provider}")


def _run_llm(system_prompt: str, user_prompt: str) -> str:
    errors: list[str] = []
    user_messages: list[str] = []
    for provider in _provider_order():
        if not _provider_configured(provider):
            errors.append(f"{provider}: not configured")
            continue
        try:
            return _run_provider(provider, system_prompt, user_prompt)
        except ResearchFlowError as exc:
            errors.append(f"{provider}: {exc.user_message}")
            if exc.user_message not in user_messages:
                user_messages.append(exc.user_message)

    if errors:
        if user_messages:
            primary = user_messages[0]
            if "quota" in primary.lower():
                primary = f"{primary} ResearchFlow could not complete this job because no fallback provider is currently available."
            else:
                primary = f"{primary} ResearchFlow tried the configured fallback providers but none completed the request."
        else:
            primary = "No usable LLM provider is configured. Add GEMINI_API_KEY or OPENAI_COMPATIBLE_API_KEY."
        raise GenerationError(
            primary,
            "; ".join(errors),
        )
    raise ConfigurationError("No LLM provider is configured. Add GEMINI_API_KEY or OPENAI_COMPATIBLE_API_KEY.")


def generate_json(system_prompt: str, user_prompt: str) -> dict | list:
    text = _run_llm(system_prompt, user_prompt)
    raw_json = _extract_json_block(text)
    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise GenerationError(
            "The language model returned invalid structured output.",
            f"Could not parse JSON: {exc}",
        ) from exc


def generate_markdown(system_prompt: str, user_prompt: str) -> str:
    return _run_llm(system_prompt, user_prompt)
