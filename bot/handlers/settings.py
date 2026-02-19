from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.keyboards import actions_keyboard, cancel_keyboard
from bot.services.settings import update_language, update_radius
from bot.states import BotState
from bot.utils.logger import logger
from bot.handlers.main_menu import send_main_menu

router = Router()

@router.message(F.text == "🌐 Мова")
async def language_handler(message: Message, state: FSMContext):
    logger.info(f"Користувач {message.from_user.id} хоче змінити мову")
    await state.set_state(BotState.selecting_language)
    await message.answer(
        "✏️ Введіть мову пошуку:",
        reply_markup=cancel_keyboard()
    )


@router.message(F.text == "📏 Радіус")
async def radius_handler(message: Message, state: FSMContext):
    logger.info(f"Користувач {message.from_user.id} хоче змінити радіус")
    await state.set_state(BotState.selecting_radius)
    await message.answer(
        "✏️ Введіть радіус пошуку в метрах:",
        reply_markup=cancel_keyboard()
    )


@router.message(BotState.selecting_language, F.text == "🔙 Скасувати")
async def cancel_language(message: Message, state: FSMContext):
    await state.clear()
    await send_main_menu(message)


@router.message(BotState.selecting_language)
async def set_language_handler(message: Message, state: FSMContext):
    lang = message.text.strip()
    logger.info(f"Користувач {message.from_user.id} змінив мову на {lang}")
    update_language(message.from_user.id, lang)
    await state.clear()
    await message.answer(f"✅ Мову змінено на {lang}", reply_markup=actions_keyboard())
    await send_main_menu(message)


@router.message(BotState.selecting_radius, F.text == "🔙 Скасувати")
async def cancel_radius(message: Message, state: FSMContext):
    await state.clear()
    await send_main_menu(message)


@router.message(BotState.selecting_radius)
async def set_radius_handler(message: Message, state: FSMContext):
    radius = message.text.strip()
    logger.info(f"Користувач {message.from_user.id} змінив радіус на {radius}")
    update_radius(message.from_user.id, radius)
    await state.clear()
    await send_main_menu(message)
