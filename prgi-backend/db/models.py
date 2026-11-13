"""
Pydantic models for MongoDB documents.
These define the schema stored in each collection.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Audit Log ────────────────────────────────────────────────────────────────

class AuditLogDoc(BaseModel):
    id:            str       = Field(default_factory=_uuid, alias="_id")
    title:         str
    periodicity:   str       = ""
    language:      str       = "en"
    state:         str       = ""
    verdict:       str
    verify_prob:   int
    max_sim:       float
    issues:        List[Any] = []
    pipeline_steps: List[Any] = []
    checks:        List[Any] = []
    suggestions:   List[str] = []
    source:        str       = "api"   # "api" | "bulk" | "ocr"
    lang_detected: dict      = {}
    trend:         dict      = {}
    created_at:    datetime  = Field(default_factory=_now)

    model_config = {"populate_by_name": True}


# ── Webhook Config ────────────────────────────────────────────────────────────

class WebhookDoc(BaseModel):
    id:         str      = Field(default_factory=_uuid, alias="_id")
    url:        str
    events:     List[str] = ["APPROVED", "REJECTED", "REVIEW"]
    secret:     str      = ""
    active:     bool     = True
    created_at: datetime = Field(default_factory=_now)

    model_config = {"populate_by_name": True}


# ── Bulk Job ──────────────────────────────────────────────────────────────────

class BulkJobDoc(BaseModel):
    id:         str      = Field(default_factory=_uuid, alias="_id")
    filename:   str
    total:      int      = 0
    processed:  int      = 0
    results:    List[Any] = []
    status:     str      = "pending"   # "pending" | "running" | "done" | "error"
    created_at: datetime = Field(default_factory=_now)
    finished_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}
