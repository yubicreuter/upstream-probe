from __future__ import annotations

import json
import logging
import sys
from typing import Any


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        stream=sys.stdout,
        format="%(message)s",
    )


def log_event(message: str, **fields: Any) -> None:
    payload = {"msg": message, **fields}
    logging.getLogger("upstream-probe").info(json.dumps(payload, sort_keys=True))
