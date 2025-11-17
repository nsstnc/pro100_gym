import logging
import colorlog
from dotenv import load_dotenv
import os
import time

os.environ['TZ'] = 'Europe/Moscow'
time.tzset()

load_dotenv()

log_level = 'DEBUG'

# Определяем формат с цветами
log_colors = {
    'DEBUG': 'white',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

formatter = colorlog.ColoredFormatter(
    "%(log_color)s - %(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors=log_colors,
)

# Настраиваем обработчик с цветным форматтером
console_handler = colorlog.StreamHandler()
console_handler.setFormatter(formatter)

# Настраиваем обработчик для записи в файл
file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

logger = logging.getLogger("app")

logger.setLevel(log_level)
logger.propagate = False

if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


# Настраиваем SQLAlchemy, чтобы логи не засоряли вывод
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)

# Настраиваем Uvicorn
logging.getLogger("uvicorn.access").setLevel(logging.INFO)

__all__ = ["logger"]
