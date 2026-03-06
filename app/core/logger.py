import logging
import sys
from app.core.config import settings

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging():
    level = logging.DEBUG if settings.ENV == "development" else logging.INFO
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter(
            LOG_FORMAT,
            datefmt=DATE_FORMAT))
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.ENV == "development" else logging.WARNING
    )
    logging.info(f"Logging initialized. Level={logging.getLevelName(level)}")