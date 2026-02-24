from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.keyboards import actions_keyboard, cancel_keyboard
from aiogram.filters import StateFilter
from bot.services.settings import update_language, update_radius, update_included_types, update_excluded_types, update_max_result_count, update_rank_preference, get_user_settings
from bot.states import BotState
from bot.utils.logger import logger
from bot.handlers.main_menu import send_main_menu

router = Router()


@router.message(F.text == "🌐 Мова")
async def language_handler(message: Message, state: FSMContext):
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) хоче змінити мову")
    await state.set_state(BotState.selecting_language)
    await message.answer(
        "✏️ Введіть мову пошуку (у форматі: uk, en, pl, ...):",
        reply_markup=cancel_keyboard()
    )


@router.message(F.text == "📏 Радіус")
async def radius_handler(message: Message, state: FSMContext):
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) хоче змінити радіус")
    await state.set_state(BotState.selecting_radius)
    await message.answer(
        "✏️ Введіть радіус пошуку в метрах (1-5000):",
        reply_markup=cancel_keyboard()
    )


@router.message(F.text == "✅ Включити типи")
async def included_types_handler(message: Message, state: FSMContext):
    await state.set_state(BotState.selecting_included_types)
    await message.answer(
        "✏️ Введіть типи місць для пошуку через кому (наприклад: restaurant, cafe):\n"
        "Або надішліть 'clear' щоб очистити.",
        reply_markup=cancel_keyboard()
    )


@router.message(F.text == "❌ Виключити типи")
async def excluded_types_handler(message: Message, state: FSMContext):
    await state.set_state(BotState.selecting_excluded_types)
    await message.answer(
        "✏️ Введіть типи місць, які треба виключити, через кому (наприклад: restaurant, cafe):\n"
        "Або надішліть 'clear' щоб очистити.",
        reply_markup=cancel_keyboard()
    )


@router.message(F.text == "🔢 Кількість")
async def max_result_count_handler(message: Message, state: FSMContext):
    await state.set_state(BotState.selecting_max_result_count)
    await message.answer(
        "✏️ Введіть максимальну кількість результатів (1-20):",
        reply_markup=cancel_keyboard()
    )


@router.message(F.text == "⭐ Сортування")
async def rank_preference_handler(message: Message):
    current_settings = get_user_settings(message.from_user.id)
    current_rank = current_settings.get("rankPreference", "POPULARITY")

    new_rank = "DISTANCE" if current_rank == "POPULARITY" else "POPULARITY"
    update_rank_preference(message.from_user.id, new_rank)

    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) змінив сортування на {new_rank}")
    await send_main_menu(message)

@router.message(F.text == "📡 Сортування отриманого")
async def included_exluded_types_reference_handler(message:Message):
    ########################
    return

@router.message(StateFilter(BotState.selecting_language, BotState.selecting_radius,
                            BotState.selecting_included_types, BotState.selecting_excluded_types,
                            BotState.selecting_max_result_count), F.text == "🔙 Скасувати")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await send_main_menu(message)


@router.message(BotState.selecting_language)
async def set_language_handler(message: Message, state: FSMContext):
    lang = message.text.strip()
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) змінив мову на {lang}")
    update_language(message.from_user.id, lang)
    await state.clear()
    await send_main_menu(message)


@router.message(BotState.selecting_radius)
async def set_radius_handler(message: Message, state: FSMContext):
    radius = message.text.strip()
    if not radius.isdigit():
        await message.answer("⚠️ Будь ласка, введіть число.")
        return
    if not (1 <= int(radius) <= 5000):
        await message.answer("⚠️ Будь ласка, введіть число від 1 до 5000.")
        return

    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) змінив радіус на {radius}")
    update_radius(message.from_user.id, radius)
    await state.clear()
    await send_main_menu(message)


@router.message(BotState.selecting_included_types)
async def set_included_types_handler(message: Message, state: FSMContext):
    text = message.text.strip()
    types = []
    if text.lower() != 'clear':
        types = [t.strip() for t in text.split(',')]

    update_included_types(message.from_user.id, types)
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) змінив включені типи на {types}")
    await state.clear()
    await send_main_menu(message)


@router.message(BotState.selecting_excluded_types)
async def set_excluded_types_handler(message: Message, state: FSMContext):
    text = message.text.strip()
    types = []
    if text.lower() != 'clear':
        types = [t.strip() for t in text.split(',')]

    update_excluded_types(message.from_user.id, types)
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) змінив виключені типи на {types}")
    await state.clear()
    await send_main_menu(message)


@router.message(BotState.selecting_max_result_count)
async def set_max_result_count_handler(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text.isdigit() or not (1 <= int(text) <= 20):
        await message.answer("⚠️ Будь ласка, введіть число від 1 до 20.")
        return

    update_max_result_count(message.from_user.id, int(text))
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) змінив кількість результатів на {int(text)}")
    await state.clear()
    await send_main_menu(message)
