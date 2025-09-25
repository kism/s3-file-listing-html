"""Constants for the S3 file listing HTML generator."""

from pathlib import Path

import jinja2

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
    "MARKDOWN_PATH",
    "LOG_LEVEL",
]

TEMPLATE_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=TEMPLATES_PATH), autoescape=False)
