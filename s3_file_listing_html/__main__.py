"""Console script for s3_file_listing_html."""

import contextlib
from dataclasses import dataclass
import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import boto3
import dotenv
import jinja2

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_s3.type_defs import ObjectTypeDef
else:
    S3Client = object
    ObjectTypeDef = dict


LOG_FORMAT = "%(levelname)s: %(message)s"

STATIC_PATH = Path(__file__).parent / "static"
TEMPLATES_PATH = Path(__file__).parent / "templates"


EXPECTED_ENV_VARS = [
    "S3_BUCKET_NAME",
    "AWS_ENDPOINT_URL",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "BASE_URL",
]

OPTIONAL_ENV_VARS = [
    "OUTPUT_PATH",
    "LOG_LEVEL",
]


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


def _get_file_list() -> list[str]:
    s3_client = boto3.client("s3")
    paginator = s3_client.get_paginator("list_objects_v2")

    page_iterator = paginator.paginate(Bucket=settings.s3_bucket_name)

    all_objects: list[ObjectTypeDef] = []
    for page in page_iterator:
        contents = page.get("Contents", [])
        all_objects.extend(contents)

    contents_nice_list: list[str] = []
    if len(all_objects) > 0:
        for obj in all_objects:
            contents_nice_list.append(obj["Key"])
            if obj["Size"] == 0:  # This is for application/x-directory files, but no files should be empty
                logger.warning("⛅ S3 Object is empty: %s DELETING", obj["Key"])
                s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=obj["Key"])
            if obj["Key"].startswith("/"):
                logger.warning("⛅ S3 Path starts with a /, this is not expected: %s DELETING", obj["Key"])
                s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=obj["Key"])
            if "//" in obj["Key"]:
                logger.warning("⛅ S3 Path contains a //, this is not expected: %s DELETING", obj["Key"])
                s3_client.delete_object(Bucket=settings.s3_bucket_name, Key=obj["Key"])
        logger.debug("⛅ S3 Bucket Contents >>>\n%s", "\n ".join(contents_nice_list))
    else:
        logger.info("⛅ No objects found in the bucket.")

    return contents_nice_list


def _render_html(file_list: list[str]) -> None:
    base_url = settings.base_url.removesuffix("/")
    template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=TEMPLATES_PATH), autoescape=True)

    template = template_env.get_template("filelist.html.j2")
    rendered = template.render(file_list=file_list, base_url=base_url)

    output_path = settings.output_path / "filelist.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(rendered)


def _copy_static_files() -> None:
    if STATIC_PATH.exists():
        shutil.copytree(STATIC_PATH, settings.output_path / "static", dirs_exist_ok=True)


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
            dotenv_example += f"{var}=""\n"

        logger.info("All environment variables:\n%s", dotenv_example)

        raise OSError(msg)


def main() -> None:
    """Console script for s3_file_listing_html."""
    with contextlib.suppress(KeyError):
        log_level = os.environ["LOG_LEVEL"].upper()
        logger.setLevel(log_level)
        logger.info("Log level set to %s from environment variable LOG_LEVEL", log_level)

    logger.info("Hello from s3-file-listing-html!")
    file_list = _get_file_list()
    _render_html(file_list)
    _copy_static_files()


dotenv.load_dotenv()
_check_env_vars()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

if os.getenv("OUTPUT_PATH") is None:
    logger.warning("Environment variable OUTPUT_PATH is not set, using default value ./output")
    output_path = Path.cwd() / "output"
else:
    output_path = Path(os.getenv("OUTPUT_PATH"))

settings = Settings(
    s3_bucket_name=os.getenv("S3_BUCKET_NAME") or "",
    base_url=os.getenv("BASE_URL") or "",
    output_path=output_path,
)

if __name__ == "__main__":
    main()
