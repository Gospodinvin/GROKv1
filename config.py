import os
import logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
STATE_TTL_SECONDS = 15 * 60
MIN_QUALITY_SCORE = 0.35  # Снижено для лучшей совместимости с разреженными графиками
