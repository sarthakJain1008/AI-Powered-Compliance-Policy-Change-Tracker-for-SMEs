"""Structured output schema for stage 3 (extract). The LLM fills this; SQL and rules decide what to do with it."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Frequency = Literal["one-time", "annual", "quarterly", "monthly", "ad-hoc"]


class ExtractedObligation(BaseModel):
    description: str = Field(description="One actionable requirement imposed on regulated entities, plain language, <= 40 words")
    frequency: Frequency
    deadline_text: Optional[str] = Field(None, description="Deadline exactly as stated in the document, else null")
    responsible_role: Optional[str] = Field(None, description="Role that would own it, e.g. CFO, Company Secretary, HR Manager")
    penalty_severity: int = Field(3, ge=1, le=5, description="1 = minor/administrative ... 5 = licence loss, prosecution or large penalty")


class ExtractedInstrument(BaseModel):
    is_regulatory: bool = Field(description="False for market operations, auction results, speeches, rate announcements, press items that impose no rule")
    instrument_type: Literal["act", "rule", "regulation", "notification", "circular", "order", "judgment", "other"]
    change_type: Literal["new", "amendment", "clarification", "repeal", "none"]
    title: str
    issuing_authority: Optional[str] = None
    issued_on: Optional[str] = Field(None, description="ISO date YYYY-MM-DD of issue, only if stated")
    effective_from: Optional[str] = Field(None, description="ISO date YYYY-MM-DD from which it applies, only if stated or directly computable; never guess")
    effective_date_quote: Optional[str] = Field(None, description="Verbatim sentence supporting effective_from")
    target_regulation: Optional[str] = Field(None, description="Full name of the Act/Direction/regulation this document creates, amends, clarifies or repeals")
    affected_sectors: list[str] = Field(default_factory=list, description="Names chosen ONLY from the provided sector list")
    summary_plain: str = Field(description="Plain-language summary for a non-lawyer small-business owner, <= 100 words")
    obligations: list[ExtractedObligation] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, description="Your overall confidence that every field above is correct")
