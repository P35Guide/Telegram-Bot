from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from bot.keyboards import actions_keyboard, cancel_keyboard, add_place_redirect_keyboard
from aiogram.filters import StateFilter
from bot.services.settings import update_language, update_radius, update_included_types, update_excluded_types, update_max_result_count, update_rank_preference, get_user_settings
from bot.states import BotState
from bot.utils.logger import logger
from bot.handlers.main_menu import send_main_menu
from bot.services import settings as settings_service
from bot.config import ADD_PLACE_BOT_USERNAME

router = Router()


@router.message(F.text == "🔗 Додати місце")
async def add_place_redirect_handler(message: Message):
    """Пояснює, що додавання місць доступне в іншому боті, і пропонує перейти."""
    username = ADD_PLACE_BOT_USERNAME if ADD_PLACE_BOT_USERNAME.startswith("@") else f"@{ADD_PLACE_BOT_USERNAME}"
    await message.answer(
        "📌 <b>Додавання власних місць</b>\n\n"
        "У цьому боті можна лише <b>шукати</b> місця поруч.\n"
        "Щоб <b>додати своє місце</b> до карти, скористайтесь окремим ботом:\n\n"
        f"👉 {username}",
        parse_mode="HTML",
        reply_markup=add_place_redirect_keyboard(),
    )


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


@router.message(F.text == "🍴 Вибрати категорії")
async def included_types_handler(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()

    popular_types = [
        ("🍕 Ресторан",  "restaurant"),
        ("☕ Кав'ярня", "cafe"),
        ("🍺 Бар", "bar"),
        ("🍔 Фастфуд", "fast_food_restaurant"),
        ("💊 Аптека", "pharmacy"),
        ("🛒 Магазин", "store")



    ]

    for label, code in popular_types:
        builder.button(
            text=label,
            callback_data=f"add_included_type:{code}"
        )

    builder.button(text="🧹 Скинути категорії",
                   callback_data="cancel_included_types")

    builder.adjust(2)

    current_settings = get_user_settings(message.from_user.id)
    included = current_settings.get("includedTypes", [])
    current_line = f"Поточні: <code>{', '.join(included)}</code>\n\n" if included else ""

    await message.answer(
        "🔎 <b>Оберіть популярну категорію</b> зі списку нижче:\n\n"
        f"{current_line}"
        "✍️ <b>Або просто напишіть</b> свій варіант (наприклад: шаурма, кінотеатр, парк).",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

    await state.set_state(BotState.waiting_for_category)


@router.message(F.text == "✅ Включити типи")
async def included_types_handler(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()

    popular_types = [
        ("🍕 Ресторан",  "restaurant"),
        ("☕ Кав'ярня", "cafe"),
        ("🍺 Бар", "bar"),
        ("🍔 Фастфуд", "fast_food_restaurant"),
        ("💊 Аптека", "pharmacy"),
        ("🛒 Магазин", "store")



    ]

    for label, code in popular_types:
        builder.button(
            text=label,
            callback_data=f"add_included_type:{code}"
        )

    builder.button(text="🧹 Скинути категорії",
                   callback_data="cancel_included_types")

    builder.adjust(2)

    current_settings = get_user_settings(message.from_user.id)
    included = current_settings.get("includedTypes", [])
    current_line = f"Поточні: <code>{', '.join(included)}</code>\n\n" if included else ""

    await message.answer(
        "🔎 <b>Оберіть популярну категорію</b> зі списку нижче:\n\n"
        f"{current_line}"
        "✍️ <b>Або просто напишіть</b> свій варіант (наприклад: шаурма, кінотеатр, парк).",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

    await state.set_state(BotState.waiting_for_category)


@router.callback_query(F.data.startswith("add_included_type:"))
async def add_included_type_callback(callback: CallbackQuery, state: FSMContext):
    type_code = callback.data.split(":")[1]
    settings_service.add_included_type(callback.from_user.id, type_code)
    await callback.answer("✅ Категорію додано!")
    await state.clear()
    await send_main_menu(callback.message, user_id=callback.from_user.id)


@router.message(BotState.waiting_for_category)
async def add_custom_category_handler(message: Message, state: FSMContext):
    user_text = (message.text or "").strip()

    if len(user_text) < 3:
        await message.answer("⚠️ Занадто коротка назва. Спробуйте ще раз або оберіть кнопку.")
        return

    settings_service.add_included_type(message.from_user.id, user_text)
    await message.answer(f"✅ Прийнято! Шукаю нестандартну категорію: **{user_text}**")
    await state.clear()
    await send_main_menu(message)


@router.callback_query(F.data == "cancel_included_types")
async def clear_included_types_callback(callback: CallbackQuery, state: FSMContext):
    settings_service.clear_included_types(callback.from_user.id)
    await callback.answer("✅ Категорії скинуто!")
    await state.clear()
    await send_main_menu(callback.message, user_id=callback.from_user.id)


@router.message(F.text == "🧹 Скинути категорії", BotState.waiting_for_category)
async def clear_included_types_handler(message: Message, state: FSMContext):
    settings_service.clear_included_types(message.from_user.id)
    await message.answer("✅ Категорії скинуто!")
    await state.clear()
    await send_main_menu(message)


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


@router.message(StateFilter(BotState.selecting_language, BotState.selecting_radius,
                            BotState.selecting_included_types, BotState.selecting_excluded_types,
                            BotState.selecting_max_result_count), F.text == "🔙 Скасувати")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await send_main_menu(message)


@router.message(F.text == "⏰ Відкрите зараз")
async def open_now_handler(message: Message):
    current_settings = get_user_settings(message.from_user.id)
    current_open_now = current_settings.get("openNow", False)

    new_open_now = not current_open_now
    settings_service.update_open_now(message.from_user.id, new_open_now)

    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) змінив налаштування 'відкрите зараз' на {new_open_now}")
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
