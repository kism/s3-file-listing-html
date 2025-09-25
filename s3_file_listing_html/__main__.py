"""Console script for s3_file_listing_html."""

import contextlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import dotenv

from .constants import EXPECTED_ENV_VARS, OPTIONAL_ENV_VARS
from .file_list import copy_static_files, render_html
from .s3 import S3Handler

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_s3.type_defs import ObjectTypeDef
else:
    S3Client = object
    ObjectTypeDef = dict


LOG_FORMAT = "%(levelname)s: %(message)s"


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("s3transfer").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("jinja2").setLevel(logging.WARNING)


@dataclass
class Settings:
    """Settings object for nicer typing."""

    s3_bucket_name: str
    base_url: str
    output_path: Path


def _check_env_vars() -> None:
    errors = []

    for var in EXPECTED_ENV_VARS:
        if var not in os.environ:
            errors.append(f"{var} is not set")
        if os.getenv(var) == "":
            errors.append(f"{var} is empty")

    if errors:
        msg = ", ".join(errors)
        logger.error("Environment variable check failed: %s", msg)

        dotenv_example = ""
        for var in EXPECTED_ENV_VARS + OPTIONAL_ENV_VARS:
            dotenv_example += f"{var}=\n"

        logger.info("All environment variables:\n%s", dotenv_example)

        raise OSError(msg)


def main() -> None:
    """Console script for s3_file_listing_html."""
    with contextlib.suppress(KeyError):
        log_level = os.environ["LOG_LEVEL"].upper()
        logger.setLevel(log_level)
        logger.debug("Log level set to %s from environment variable LOG_LEVEL", log_level)

    logger.info("Hello, making your file list!")
    logger.info("S3 Bucket: %s", settings.s3_bucket_name)
    logger.info("Base URL: %s", settings.base_url)
    logger.info("Output Path: %s", settings.output_path.resolve())

    s3_handler = S3Handler(bucket_name=settings.s3_bucket_name)

    file_list = s3_handler.get_file_list()
    render_html(file_list, settings.base_url, settings.output_path)
    copy_static_files(settings.output_path)

    s3_handler.upload_directory(settings.output_path)


dotenv.load_dotenv()
_check_env_vars()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

path_str = os.getenv("OUTPUT_PATH") or ""

if path_str == "":
    logger.warning("Environment variable OUTPUT_PATH is not set, using default value ./output")
    output_path = Path.cwd() / "output"
else:
    output_path = Path(path_str)

settings = Settings(
    s3_bucket_name=os.getenv("S3_BUCKET_NAME") or "",
    base_url=os.getenv("BASE_URL") or "",
    output_path=output_path,
)

if __name__ == "__main__":
    main()
