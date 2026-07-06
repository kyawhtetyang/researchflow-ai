from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings
from app.services.errors import ConfigurationError, GenerationError, ResearchFlowError


def _get_openai_client():
    if not settings.openai_api_key.strip():
        raise ConfigurationError("OPENAI_API_KEY is missing for planner and report generation.")
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise ConfigurationError("OpenAI SDK is not installed in the current runtime.") from exc
    return OpenAI(api_key=settings.openai_api_key)


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


def _run_openai(system_prompt: str, user_prompt: str) -> str:
    try:
        response = _get_openai_client().responses.create(
            model=settings.model_name,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = (response.output_text or "").strip()
        if not text:
            raise GenerationError("The language model returned an empty response.")
        return text
    except ResearchFlowError:
        raise
    except Exception as exc:
        error_type = type(exc).__name__
        if error_type in {"OpenAIError", "APIError", "AuthenticationError", "RateLimitError", "BadRequestError"}:
            raise GenerationError(
                "OpenAI request failed while generating the research workflow output.",
                str(exc),
            ) from exc
        raise GenerationError(
            "Unexpected language model failure while generating the research workflow output.",
            str(exc),
        ) from exc


def _run_gemini(system_prompt: str, user_prompt: str) -> str:
    if not settings.gemini_api_key.strip():
        raise ConfigurationError("GEMINI_API_KEY is missing for Gemini-based generation.")

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "text/plain",
        },
    }
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.model_name}:generateContent?key={settings.gemini_api_key}",
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


def _run_llm(system_prompt: str, user_prompt: str) -> str:
    provider = settings.llm_provider.strip().lower()
    if provider == "openai":
        return _run_openai(system_prompt, user_prompt)
    if provider == "gemini":
        return _run_gemini(system_prompt, user_prompt)
    raise ConfigurationError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


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
