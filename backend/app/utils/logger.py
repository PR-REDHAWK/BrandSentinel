import logging
import sys

from app.config import settings

logger = logging.getLogger("brandsentinel")
logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
