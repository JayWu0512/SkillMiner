import logging
import json
from datetime import datetime


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Optional: include extra fields (trace ID, user, etc.)
        if hasattr(record, "extra"):
            log_record.update(record.extra)

        return json.dumps(log_record)


def init_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    # Avoid duplicate handlers on reload (e.g., uvicorn reload mode)
    if not root.handlers:
        root.addHandler(handler)
