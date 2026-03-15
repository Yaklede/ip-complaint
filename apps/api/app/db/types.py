from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import TypeDecorator


JSONType = JSON().with_variant(postgresql.JSONB(), "postgresql")


class IPAddressType(TypeDecorator[str]):
    impl = String(64)
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[no-untyped-def]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.INET())
        return dialect.type_descriptor(String(64))

    def process_bind_param(self, value, dialect):  # type: ignore[no-untyped-def]
        if value is None:
            return None
        return str(value)


class MacAddressType(TypeDecorator[str]):
    impl = String(32)
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[no-untyped-def]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.MACADDR())
        return dialect.type_descriptor(String(32))

    def process_bind_param(self, value, dialect):  # type: ignore[no-untyped-def]
        if value is None:
            return None
        return str(value)
