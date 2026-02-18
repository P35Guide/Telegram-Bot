import asyncio
from aiogram import Bot, Dispatcher

from bot.config import BOT_TOKEN
from bot.handlers import router
from bot.utils.logger import logger


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    logger.info("Бот запущено!")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
