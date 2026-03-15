from __future__ import annotations

from enum import Enum


class SourceType(str, Enum):
    WEB = "WEB"
    WAF = "WAF"
    VPN = "VPN"
    AD = "AD"
    EDR = "EDR"
    DHCP = "DHCP"
    NAT = "NAT"
    FW = "FW"
    DB = "DB"
    APP = "APP"
    OTHER = "OTHER"


class ActorType(str, Enum):
    INTERNAL_USER = "INTERNAL_USER"
    EXTERNAL_UNKNOWN = "EXTERNAL_UNKNOWN"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"
    SYSTEM = "SYSTEM"


class CaseStatus(str, Enum):
    NEW = "NEW"
    TRIAGED = "TRIAGED"
    INVESTIGATING = "INVESTIGATING"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    READY_FOR_EXPORT = "READY_FOR_EXPORT"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"


class EvidenceStatus(str, Enum):
    PENDING = "PENDING"
    FROZEN = "FROZEN"
    EXPORTED = "EXPORTED"


class DocumentStatus(str, Enum):
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
