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
class StoredArtifact:
    object_uri: str
    metadata: dict[str, Any]


class RawArtifactStorage(Protocol):
    backend_name: str

    def store(
        self,
        *,
        source_name: str,
        collected_at: datetime,
        artifact_id: UUID,
        raw_bytes: bytes,
        content_type: str,
        extension: str,
        checksum_sha256: str,
    ) -> StoredArtifact:
        ...


class LocalFilesystemRawArtifactStorage:
    backend_name = "filesystem"

    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir).expanduser().resolve()
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def store(
        self,
        *,
        source_name: str,
        collected_at: datetime,
        artifact_id: UUID,
        raw_bytes: bytes,
        content_type: str,
        extension: str,
        checksum_sha256: str,
    ) -> StoredArtifact:
        relative_path = (
            Path(self._safe_source_name(source_name))
            / f"{collected_at:%Y}"
            / f"{collected_at:%m}"
            / f"{collected_at:%d}"
            / f"{artifact_id}.{extension}"
        )
        absolute_path = self._base_dir / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        with absolute_path.open("xb") as output_file:
            output_file.write(raw_bytes)
        os.chmod(absolute_path, 0o444)

        return StoredArtifact(
            object_uri=absolute_path.as_uri(),
            metadata={
                "backend": self.backend_name,
                "relativePath": str(relative_path),
                "contentType": content_type,
                "sizeBytes": len(raw_bytes),
                "sha256": checksum_sha256,
            },
        )

    def _safe_source_name(self, source_name: str) -> str:
        return source_name.replace("/", "_").replace("\\", "_").replace(" ", "_")


class MinioRawArtifactStorage:
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
        self._bucket = settings.minio_bucket

    def store(
        self,
        *,
        source_name: str,
        collected_at: datetime,
        artifact_id: UUID,
        raw_bytes: bytes,
        content_type: str,
        extension: str,
        checksum_sha256: str,
    ) -> StoredArtifact:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

        object_name = (
            f"raw/{self._safe_source_name(source_name)}/"
            f"{collected_at:%Y/%m/%d}/{artifact_id}.{extension}"
        )
        result = self._client.put_object(
            self._bucket,
            object_name,
            io.BytesIO(raw_bytes),
            length=len(raw_bytes),
            content_type=content_type,
        )
        return StoredArtifact(
            object_uri=f"s3://{self._bucket}/{object_name}",
            metadata={
                "backend": self.backend_name,
                "bucket": self._bucket,
                "objectName": object_name,
                "contentType": content_type,
                "sizeBytes": len(raw_bytes),
                "sha256": checksum_sha256,
                "etag": result.etag,
                "versionId": result.version_id,
            },
        )

    def _safe_source_name(self, source_name: str) -> str:
        return source_name.replace("/", "_").replace("\\", "_").replace(" ", "_")


def create_raw_artifact_storage(settings: Settings) -> RawArtifactStorage:
    if settings.raw_artifact_storage_backend == "minio":
        return MinioRawArtifactStorage(settings)
    return LocalFilesystemRawArtifactStorage(settings.raw_artifact_storage_dir)
