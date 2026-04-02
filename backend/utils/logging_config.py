from __future__ import annotations

import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "extra_payload", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload)


def configure_logging() -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
