from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from config import settings


Confidence = Literal["high", "medium", "low"]
DocumentStatus = Literal["indexed", "pending", "error"]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    topK: int = Field(default=settings.top_k, ge=1, le=20)
    model: Optional[str] = None


class RebuildRequest(BaseModel):
    download: bool = True


class SourceResponse(BaseModel):
    id: str
    document: str
    reference: str
    page: int
    score: float
    denseScore: float
    keywordScore: float
    excerpt: str


class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    confidence: Confidence
    sources: list[SourceResponse]
    generatedAt: str
    noAnswer: bool = False
    reason: Optional[str] = None
    durationMs: int


class RuntimeStatus(BaseModel):
    ready: bool
    ollamaOnline: bool
    baseDir: str
    docsDir: str
    cacheFile: str
    cacheExists: bool
    documents: int
    chunks: int
    embedModel: str
    chatModel: str
    activeChatModel: Optional[str] = None
    availableModels: list[str] = []
    categories: list[str]
    domainGate: dict[str, object] = {}
    error: Optional[str] = None


class ReadinessResponse(BaseModel):
    ready: bool
    checks: dict[str, bool]
    status: RuntimeStatus
    reasons: list[str] = []


class DocumentResponse(BaseModel):
    id: str
    title: str
    source: str
    pages: int
    chunks: int
    status: DocumentStatus
    updated: float
    filename: str


class DocumentsResponse(BaseModel):
    documents: list[DocumentResponse]


class RebuildResponse(BaseModel):
    ok: bool
    status: RuntimeStatus


class ErrorResponse(BaseModel):
    detail: str
