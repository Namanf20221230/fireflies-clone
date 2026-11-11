from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings


class AIUnavailableError(RuntimeError):
    pass


class GeneratedSummary(BaseModel):
    overview: str = Field(min_length=1)
    key_points: list[dict[str, Any]] = Field(default_factory=list)
    decisions: list[dict[str, Any]] = Field(default_factory=list)


def _client() -> Any:
    if not settings.gemini_api_key:
        raise AIUnavailableError("Gemini is not configured. Set GEMINI_API_KEY on the backend.")
    from google import genai

    return genai.Client(api_key=settings.gemini_api_key)


def generate_summary(transcript: str) -> GeneratedSummary:
    if not transcript.strip():
        raise ValueError("A transcript is required to generate a summary")
    client = _client()
    prompt = (
        "Use only this meeting transcript. Return JSON with overview (string), key_points "
        "(array of objects with a point field), and decisions (array of objects with a decision field). "
        "Do not infer facts absent from the transcript.\n\nTRANSCRIPT:\n" + transcript[:100_000]
    )
    try:
        response = client.models.generate_content(model=settings.gemini_model, contents=prompt)
        payload = json.loads(response.text or "")
        return GeneratedSummary.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError("Gemini returned an invalid structured summary") from exc
    except AIUnavailableError:
        raise
    except Exception as exc:  # provider exceptions are deliberately not exposed
        raise AIUnavailableError("Gemini could not generate a summary right now") from exc


def answer_question(context: str, question: str) -> str:
    client = _client()
    prompt = (
        "Answer only from the meeting context below. If the information is absent, say so plainly. "
        "Do not make up people, commitments, or dates.\n\nMEETING CONTEXT:\n"
        f"{context[:110_000]}\n\nQUESTION: {question}"
    )
    try:
        response = client.models.generate_content(model=settings.gemini_model, contents=prompt)
        answer = (response.text or "").strip()
        if not answer:
            raise AIUnavailableError("Gemini returned an empty response")
        return answer
    except AIUnavailableError:
        raise
    except Exception as exc:
        raise AIUnavailableError("Gemini could not answer this question right now") from exc
