"""Console script for s3_file_listing_html."""

import contextlib
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import dotenv

from .constants import EXPECTED_ENV_VARS, OPTIONAL_ENV_VARS
from .file_list import render_file_list
from .helpers import copy_static_files
from .logger import logger
from .markdown import render_markdown_files
from .s3 import S3Handler

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_s3.type_defs import ObjectTypeDef
else:
    S3Client = object
    ObjectTypeDef = dict

start_time = time.time()


@dataclass
class Settings:
    """Settings object for nicer typing."""

    s3_bucket_name: str
    base_url: str
    output_path: Path
    markdown_path: Path


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


def time_split(name: str) -> None:
    global start_time
    logger.warning("%s took %.2f seconds", name, time.time() - start_time)
    start_time = time.time()


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
    time_split("S3Handler initialisation")

    # Do this twice so it gets itself in the listing
    force_refresh = False
    for i in range(2):
        if i > 0:
            force_refresh = True
        file_list = s3_handler.get_file_list(force_refresh=force_refresh)
        time_split(f"S3Handler get_file_list pass {i + 1}")

        render_file_list(file_list, settings.base_url, settings.output_path)
        time_split(f"render_file_list pass {i + 1}")

        render_markdown_files(settings.markdown_path, settings.output_path)
        time_split(f"render_markdown_files pass {i + 1}")

        copy_static_files(settings.output_path)
        time_split(f"copy_static_files pass {i + 1}")

        s3_handler.upload_directory(settings.output_path)
        time_split(f"S3Handler upload_directory pass {i + 1}")


dotenv.load_dotenv()
_check_env_vars()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
logger.handlers[0].setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

output_path_str = os.getenv("OUTPUT_PATH") or ""
if output_path_str == "":
    logger.warning("Environment variable OUTPUT_PATH is not set, using default value ./output")
    output_path = Path.cwd() / "output"
else:
    output_path = Path(output_path_str)

markdown_path_str = os.getenv("MARKDOWN_PATH") or ""
markdown_path = Path(markdown_path_str) if markdown_path_str != "" else Path.cwd() / "md"

settings = Settings(
    s3_bucket_name=os.getenv("S3_BUCKET_NAME") or "",
    base_url=os.getenv("BASE_URL") or "",
    output_path=output_path,
    markdown_path=markdown_path,
)

if __name__ == "__main__":
    main()
