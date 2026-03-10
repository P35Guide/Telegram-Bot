import asyncio
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from bot.config import BOT_TOKEN
from bot.handlers import main_menu, places, settings
from bot.utils.logger import logger
import os

# Простий HTTP сервер щоб Render не вбивав процес через таймаут
async def health(request):
    return web.Response(text="OK")

async def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health server запущено на порту {port}")

COMMANDS = [
    BotCommand(command="start", description="Запустити бота"),
    BotCommand(command="menu", description="Головне меню"),
    BotCommand(command="coordinates", description="Передати координати"),
    BotCommand(command="place_list", description="Список місць"),
    BotCommand(command="rand_place", description="Випадкове місце"),
]


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(main_menu.router)
    dp.include_router(places.router)
    dp.include_router(settings.router)

    await bot.set_my_commands(COMMANDS)
    logger.info("Бот запущено!")

    # Запускаємо health server і polling паралельно
    await start_health_server()

    async with aiohttp.ClientSession() as session:
        await dp.start_polling(bot, session=session)

if __name__ == "__main__":
    asyncio.run(main())
