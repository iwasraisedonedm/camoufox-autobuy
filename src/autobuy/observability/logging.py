"""Production-safe structured logging."""

import logging
from collections.abc import MutableMapping
from typing import Any

import structlog

REDACT_KEYS = {
    "password",
    "authorization",
    "cookie",
    "session",
    "token",
    "card_number",
    "cvv",
    "cvc",
    "account_number",
    "routing_number",
}


def _redact(
    _: object,
    __: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    for key in tuple(event_dict):
        if key.lower() in REDACT_KEYS:
            event_dict[key] = "[REDACTED]"
    return event_dict


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _redact,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        cache_logger_on_first_use=True,
    )
