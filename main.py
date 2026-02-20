import asyncio
import aiohttp
from aiogram import Bot, Dispatcher

from bot.config import BOT_TOKEN
from bot.handlers import main_menu, places, settings
from bot.utils.logger import logger


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(main_menu.router)
    dp.include_router(places.router)
    dp.include_router(settings.router)

    logger.info("Бот запущено!")

    async with aiohttp.ClientSession() as session:
        await dp.start_polling(bot, session=session)

if __name__ == "__main__":
    asyncio.run(main())
