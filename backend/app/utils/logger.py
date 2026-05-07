import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config.settings import settings


# --------------------------------------------------
# Log Directory Setup
# --------------------------------------------------

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"


# --------------------------------------------------
# Formatter (Structured-ish)
# --------------------------------------------------

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)


# --------------------------------------------------
# Console Handler
# --------------------------------------------------

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)


# --------------------------------------------------
# File Handler (Rotating)
# --------------------------------------------------

file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=3
)
file_handler.setFormatter(formatter)


# --------------------------------------------------
# Logger Instance
# --------------------------------------------------

logger = logging.getLogger("food-ordering-app")

# Set level from settings (default INFO)
logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

# Prevent duplicate logs
logger.propagate = False

# Attach handlers
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


# --------------------------------------------------
# Helper Functions (Optional)
# --------------------------------------------------

def get_logger(name: str):
    """
    Create module-specific logger:
    usage → log = get_logger(__name__)
    """
    child_logger = logging.getLogger(f"food-ordering-app.{name}")
    child_logger.setLevel(logger.level)

    if not child_logger.handlers:
        child_logger.addHandler(console_handler)
        child_logger.addHandler(file_handler)

    return child_logger