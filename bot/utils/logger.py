import logging
import sys


def setup_logger():
    """
    Налаштування логгера для проекту.
    Виводить повідомлення в консоль з форматуванням:
    Час - Рівень - Повідомлення
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    return logging.getLogger("bot")


logger = setup_logger()
