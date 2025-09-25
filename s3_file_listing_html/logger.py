"""Logger setup with colored output for different log levels."""
import logging

from colorama import Fore, init

init(autoreset=True)
LOG_FORMAT = "%(levelname)s: %(message)s"


COLOURS = {
    "TRACE": Fore.CYAN,
    "DEBUG": Fore.GREEN,
    "INFO": Fore.WHITE,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.RED,
}


class ColorFormatter(logging.Formatter):
    """Formatter for coloring the log messages."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log message."""
        if isinstance(record.msg, tuple):
            record.msg = "  ".join(map(str, record.msg))

        elif record.msg is None:
            record.msg = "<NoneType>"

        elif isinstance(record.msg, list):
            record.msg = "  \n".join(map(str, record.msg))

        if record.levelno == logging.INFO:  # No need to colourise/format INFO messages
            return f"{record.getMessage()}"

        colour = COLOURS.get(record.levelname, "")
        if colour:
            record.name = f"{colour}{record.name}"
            record.levelname = f"{colour}{record.levelname}"
            record.msg = f"{colour}{record.msg}"
        return super().format(record)


logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("s3transfer").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("jinja2").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.propagate = False
root_console_handler = logging.StreamHandler()
root_console_handler.setLevel(logging.INFO)
root_formatter = ColorFormatter(LOG_FORMAT)
root_console_handler.setFormatter(root_formatter)
logger.addHandler(root_console_handler)
