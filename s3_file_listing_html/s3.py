import logging
from pathlib import Path
from typing import TYPE_CHECKING
import hashlib

import boto3

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_s3.type_defs import ObjectTypeDef
else:
    S3Client = object
    ObjectTypeDef = dict


class S3Handler:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self._client = boto3.client("s3")
        self._all_objects: list[ObjectTypeDef] = []
        self.refresh_contents()

    def refresh_contents(self) -> None:
        self._refresh_contents()
        self._cleanup()
        self._refresh_contents()

    def _refresh_contents(self) -> None:
        paginator = self._client.get_paginator("list_objects_v2")

        page_iterator = paginator.paginate(Bucket=self.bucket_name)

        all_objects: list[ObjectTypeDef] = []
        for page in page_iterator:
            contents = page.get("Contents", [])
            all_objects.extend(contents)

        self._all_objects = all_objects

    def _cleanup(self) -> None:
        for obj in self._all_objects:
            if obj["Size"] == 0:  # This is for application/x-directory files, but no files should be empty
                logger.warning("⛅ S3 Object is empty: %s DELETING", obj["Key"])
                self._client.delete_object(Bucket=self.bucket_name, Key=obj["Key"])
            if obj["Key"].startswith("/"):
                logger.warning("⛅ S3 Path starts with a /, this is not expected: %s DELETING", obj["Key"])
                self._client.delete_object(Bucket=self.bucket_name, Key=obj["Key"])
            if "//" in obj["Key"]:
                logger.warning("⛅ S3 Path contains a //, this is not expected: %s DELETING", obj["Key"])
                self._client.delete_object(Bucket=self.bucket_name, Key=obj["Key"])

    def get_file_list(self) -> list[str]:
        contents_nice_list: list[str] = []
        if len(self._all_objects) > 0:
            for obj in self._all_objects:
                contents_nice_list.append(obj["Key"])
        return contents_nice_list

    def upload_directory(self, base_directory: Path, prefix: str = "") -> None:
        def _get_sha256(file_path: Path) -> str:
            """Calculate the SHA256 hash of a file."""
            sha256_hash = hashlib.sha256()
            with file_path.open("rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()

        skipped_count = 0
        for path in base_directory.rglob("*"):
            if path.is_file():
                key = prefix + str(path.relative_to(base_directory)).replace("\\", "/")

                local_sha256 = _get_sha256(path)
                remote_sha256 = (
                    self._client.head_object(Bucket=self.bucket_name, Key=key).get("Metadata", {}).get("sha256", "")
                )

                if local_sha256 != remote_sha256:
                    logger.info("Uploading %s to s3://%s/%s", path, self.bucket_name, key)
                    self._client.upload_file(
                        Filename=str(path),
                        Bucket=self.bucket_name,
                        Key=key,
                        ExtraArgs={"Metadata": {"sha256": local_sha256}},
                    )
                else:
                    skipped_count += 1

        if skipped_count > 0:
            logger.info("Skipped uploading %d files that were unchanged", skipped_count)
