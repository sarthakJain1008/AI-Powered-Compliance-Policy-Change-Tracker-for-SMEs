"""Thin wrapper over the Anthropic SDK for structured extraction. Everything else depends on the `Extractor` protocol, so tests use a fake."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .schemas import ExtractedInstrument

DEFAULT_MODEL = "claude-opus-5-5"
PRICES = {  # USD per 1M tokens (input, output) - cached from the Anthropic model table
    "claude-opus-5-5": (4.0, 20.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-haiku-5-5": (0.10, 0.50),
}


@dataclass
class ExtractResult:
    parsed: ExtractedInstrument | None
    input_tokens: int = 0
    output_tokens: int = 0
    refusal: str | None = None       # stop_details category when the model declined


class Extractor(Protocol):
    model: str

    def extract(self, system: str, user: str) -> ExtractResult: ...


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    pin, pout = PRICES.get(model, (0.0, 0.0))
    return round((input_tokens * pin + output_tokens * pout) / 1_000_000, 5)


class ClaudeExtractor:
    """Uses client.messages.parse with a Pydantic output_format. Reads ANTHROPIC_API_KEY (or `ant auth login`) from the environment."""

    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = 16000):
        import anthropic
        self.model, self.max_tokens = model, max_tokens
        self.client = anthropic.Anthropic()

    def extract(self, system: str, user: str) -> ExtractResult:
        r = self.client.messages.parse(
            model=self.model, max_tokens=self.max_tokens, system=system,
            messages=[{"role": "user", "content": user}], output_format=ExtractedInstrument,
        )
        usage = (r.usage.input_tokens, r.usage.output_tokens)
        if r.stop_reason == "refusal":
            cat = getattr(getattr(r, "stop_details", None), "category", None)
            return ExtractResult(None, *usage, refusal=cat or "refusal")
        if r.stop_reason == "max_tokens" or r.parsed_output is None:
            raise RuntimeError(f"no parseable output (stop_reason={r.stop_reason})")
        return ExtractResult(r.parsed_output, *usage)
