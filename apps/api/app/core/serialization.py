from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID


def json_default(value: Any) -> str | int | float | bool | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    return str(value)


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=json_default,
    ).encode("utf-8")


def make_json_safe(payload: Any) -> Any:
    return json.loads(canonical_json_bytes(payload).decode("utf-8"))


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
