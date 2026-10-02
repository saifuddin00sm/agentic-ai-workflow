"""Stage result wrapper model."""

from __future__ import annotations

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class StageStatus(str, Enum):
    """Status of a stage execution."""

    SUCCESS = "success"
    DEGRADED = "degraded"
    FAILED = "failed"


class StageResult(BaseModel, Generic[T]):
    """Wrapper for a stage's output with metadata."""

    status: StageStatus
    data: T | None = None
    error: str | None = None
    duration_ms: int = 0
    token_usage: dict[str, int] = Field(default_factory=dict)
    attempts: int = 1

    @classmethod
    def success(cls, data: T, duration_ms: int = 0, attempts: int = 1, **kwargs: object) -> StageResult[T]:
        return cls(status=StageStatus.SUCCESS, data=data, duration_ms=duration_ms, attempts=attempts, **kwargs)  # type: ignore[arg-type]

    @classmethod
    def degraded(cls, data: T, error: str, duration_ms: int = 0, **kwargs: object) -> StageResult[T]:
        return cls(status=StageStatus.DEGRADED, data=data, error=error, duration_ms=duration_ms, **kwargs)  # type: ignore[arg-type]

    @classmethod
    def failed(cls, error: str, duration_ms: int = 0, **kwargs: object) -> StageResult[T]:
        return cls(status=StageStatus.FAILED, error=error, duration_ms=duration_ms, **kwargs)  # type: ignore[arg-type]
