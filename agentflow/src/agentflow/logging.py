"""Structured JSON logging setup."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from agentflow.config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter with structured fields."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields from the record
        for key in ("run_id", "stage", "agent", "tool", "latency_ms"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable log formatter."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )


def setup_logging() -> None:
    """Configure logging based on settings."""
    settings = get_settings()

    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Clear existing handlers
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    if settings.log_format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root.addHandler(handler)

    # Quiet noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def log_event(
    logger_name: str,
    message: str,
    *,
    run_id: str = "",
    stage: str = "",
    agent: str = "",
    tool: str = "",
    latency_ms: int = 0,
    level: int = logging.INFO,
) -> None:
    """Emit a structured log entry."""
    lg = logging.getLogger(logger_name)
    lg.log(
        level,
        message,
        extra={
            "run_id": run_id,
            "stage": stage,
            "agent": agent,
            "tool": tool,
            "latency_ms": latency_ms,
        },
    )
