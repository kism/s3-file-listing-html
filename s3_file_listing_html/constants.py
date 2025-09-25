
from pathlib import Path

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
