from __future__ import annotations

import io
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse
from uuid import UUID

from minio import Minio

from app.core.config import Settings


@dataclass(slots=True, frozen=True)
class StoredGeneratedOutput:
    object_uri: str
    metadata: dict[str, Any]


class GeneratedOutputStorage(Protocol):
    backend_name: str

    def store(
        self,
        *,
        category: str,
        case_no: str,
        generated_at: datetime,
        output_id: UUID,
        payload_bytes: bytes,
        content_type: str,
        extension: str,
        checksum_sha256: str,
    ) -> StoredGeneratedOutput:
        ...


class LocalFilesystemGeneratedOutputStorage:
    backend_name = "filesystem"

    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir).expanduser().resolve()
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def store(
        self,
        *,
        category: str,
        case_no: str,
        generated_at: datetime,
        output_id: UUID,
        payload_bytes: bytes,
        content_type: str,
        extension: str,
        checksum_sha256: str,
    ) -> StoredGeneratedOutput:
        relative_path = (
            Path(self._safe_name(category))
            / self._safe_name(case_no)
            / f"{generated_at:%Y}"
            / f"{generated_at:%m}"
            / f"{generated_at:%d}"
            / f"{output_id}.{extension}"
        )
        absolute_path = self._base_dir / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        with absolute_path.open("xb") as output_file:
            output_file.write(payload_bytes)
        os.chmod(absolute_path, 0o444)

        return StoredGeneratedOutput(
            object_uri=absolute_path.as_uri(),
            metadata={
                "backend": self.backend_name,
                "relativePath": str(relative_path),
                "contentType": content_type,
                "sizeBytes": len(payload_bytes),
                "sha256": checksum_sha256,
            },
        )

    def _safe_name(self, value: str) -> str:
        return value.replace("/", "_").replace("\\", "_").replace(" ", "_")


class MinioGeneratedOutputStorage:
    backend_name = "minio"

    def __init__(self, settings: Settings) -> None:
        parsed = urlparse(settings.minio_endpoint)
        endpoint = parsed.netloc or parsed.path
        secure = settings.minio_secure
        if parsed.scheme == "https":
            secure = True
        elif parsed.scheme == "http":
            secure = False

        self._client = Minio(
            endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=secure,
        )
        self._bucket = settings.generated_output_bucket

    def store(
        self,
        *,
        category: str,
        case_no: str,
        generated_at: datetime,
        output_id: UUID,
        payload_bytes: bytes,
        content_type: str,
        extension: str,
        checksum_sha256: str,
    ) -> StoredGeneratedOutput:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

        object_name = (
            f"generated/{self._safe_name(category)}/{self._safe_name(case_no)}/"
            f"{generated_at:%Y/%m/%d}/{output_id}.{extension}"
        )
        result = self._client.put_object(
            self._bucket,
            object_name,
            io.BytesIO(payload_bytes),
            length=len(payload_bytes),
            content_type=content_type,
        )
        return StoredGeneratedOutput(
            object_uri=f"s3://{self._bucket}/{object_name}",
            metadata={
                "backend": self.backend_name,
                "bucket": self._bucket,
                "objectName": object_name,
                "contentType": content_type,
                "sizeBytes": len(payload_bytes),
                "sha256": checksum_sha256,
                "etag": result.etag,
                "versionId": result.version_id,
            },
        )

    def _safe_name(self, value: str) -> str:
        return value.replace("/", "_").replace("\\", "_").replace(" ", "_")


def create_generated_output_storage(settings: Settings) -> GeneratedOutputStorage:
    if settings.raw_artifact_storage_backend == "minio":
        return MinioGeneratedOutputStorage(settings)
    return LocalFilesystemGeneratedOutputStorage(settings.generated_output_storage_dir)
