from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.serialization import canonical_json_bytes
from app.models.enums import SourceType


@dataclass(slots=True, frozen=True)
class ParsedArtifact:
    parser_name: str
    parser_version: str
    payload_kind: str
    content_type: str
    extension: str
    raw_bytes: bytes
    records: list[dict[str, Any]]


class BaseEventParser:
    parser_name = "generic-json-v1"
    parser_version = "1.0.0"

    def parse(
        self, payload: str | list[dict[str, Any]], collected_at: datetime
    ) -> ParsedArtifact:
        raise NotImplementedError

    def _extract_records(self, payload: str | list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bytes, str]:
        if isinstance(payload, list):
            records = [item if isinstance(item, dict) else {"message": str(item)} for item in payload]
            return records, canonical_json_bytes(payload), "record_list"

        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            return [{"message": payload}], payload.encode("utf-8"), "string"

        if isinstance(decoded, list):
            records = [item if isinstance(item, dict) else {"message": str(item)} for item in decoded]
            return records, payload.encode("utf-8"), "json_string_list"
        if isinstance(decoded, dict):
            return [decoded], payload.encode("utf-8"), "json_string_object"
        return [{"message": str(decoded)}], payload.encode("utf-8"), "json_scalar"


class JsonPassThroughParser(BaseEventParser):
    parser_name = "generic-json-v1"

    def parse(
        self, payload: str | list[dict[str, Any]], collected_at: datetime
    ) -> ParsedArtifact:
        records, raw_bytes, payload_kind = self._extract_records(payload)
        content_type = "text/plain" if payload_kind == "string" else "application/json"
        extension = "log" if payload_kind == "string" else "json"
        return ParsedArtifact(
            parser_name=self.parser_name,
            parser_version=self.parser_version,
            payload_kind=payload_kind,
            content_type=content_type,
            extension=extension,
            raw_bytes=raw_bytes,
            records=records,
        )


class NginxAccessParser(JsonPassThroughParser):
    parser_name = "nginx-json-v1"


class WafRequestParser(JsonPassThroughParser):
    parser_name = "waf-json-v1"


class VpnSessionParser(JsonPassThroughParser):
    parser_name = "vpn-json-v1"


class ParserRegistry:
    def __init__(self) -> None:
        self._parsers: dict[str, BaseEventParser] = {
            "generic-json-v1": JsonPassThroughParser(),
            "nginx-json-v1": NginxAccessParser(),
            "waf-json-v1": WafRequestParser(),
            "vpn-json-v1": VpnSessionParser(),
        }
        self._default_by_source_type: dict[SourceType, str] = {
            SourceType.WEB: "nginx-json-v1",
            SourceType.WAF: "waf-json-v1",
            SourceType.VPN: "vpn-json-v1",
        }

    def default_parser_name(self, source_type: SourceType) -> str:
        return self._default_by_source_type.get(source_type, "generic-json-v1")

    def resolve(self, parser_name: str | None, source_type: SourceType) -> BaseEventParser:
        resolved_name = parser_name or self.default_parser_name(source_type)
        return self._parsers.get(resolved_name, self._parsers["generic-json-v1"])
