"""S3 Handler module for listing and uploading files to an S3 bucket."""

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

from .logger import logger

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_s3.type_defs import ObjectTypeDef
else:
    S3Client = object
    ObjectTypeDef = dict


class S3Handler:
    """Handler for S3 operations, assumes you have set up AWS credentials in the environment."""

    def __init__(self, bucket_name: str) -> None:
        """Initialise the S3 handler with the target bucket name."""
        self.bucket_name = bucket_name
        self._client = boto3.client("s3")
        self._all_objects: list[ObjectTypeDef] = []
        self._hash_cache: dict[str, str] = {}
        self._try_refresh_contents()

    def _try_refresh_contents(self, *, force_refresh: bool = False) -> None:
        if len(self._all_objects) == 0 or force_refresh:
            logger.debug("Refreshing S3 contents, items=%s, force_refresh=%s", len(self._all_objects), force_refresh)
            self._refresh_contents()
            self._cleanup()
            self._refresh_contents()
        else:
            logger.debug(
                "Skipping S3 contents refresh, items=%s, force_refresh=%s", len(self._all_objects), force_refresh
            )

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

    def get_file_list(self, *, force_refresh: bool = False) -> list[str]:
        """Get a nice list of all files in the bucket."""
        self._try_refresh_contents(force_refresh=force_refresh)

        contents_nice_list: list[str] = []
        if len(self._all_objects) > 0:
            contents_nice_list = [obj["Key"] for obj in self._all_objects]
        return contents_nice_list

    def upload_directory(self, base_directory: Path, prefix: str = "") -> None:
        """Upload a directory to S3, skipping files that are unchanged based on SHA256 hash."""

        def _get_sha256(file_path: Path) -> str:
            """Calculate the SHA256 hash of a file."""
            if str(file_path) in self._hash_cache and "filelist.html" not in str(file_path):
                return self._hash_cache[str(file_path)]

            sha256_hash = hashlib.sha256()
            with file_path.open("rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            hash_str = sha256_hash.hexdigest()
            self._hash_cache[str(file_path)] = hash_str
            return hash_str

        def _get_remote_sha256(key: str) -> str:
            """Get the SHA256 hash from the S3 object's metadata."""
            if key in self._hash_cache:
                return self._hash_cache[key]

            try:
                hash_str = self._client.head_object(Bucket=self.bucket_name, Key=key).get("Metadata", {}).get("sha256", "")
            except ClientError:
                hash_str = ""
            self._hash_cache[key] = hash_str
            return hash_str

        skipped_count = 0
        for path in base_directory.rglob("*"):
            if path.is_file():
                key = prefix + str(path.relative_to(base_directory)).replace("\\", "/")

                local_sha256 = _get_sha256(path)
                remote_sha256 = _get_remote_sha256(key)

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
