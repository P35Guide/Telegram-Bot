from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from bot.keyboards import cancel_keyboard, add_place_redirect_keyboard
from aiogram.filters import StateFilter
from bot.services.settings import update_language, update_radius, update_included_types, update_excluded_types, update_max_result_count, update_rank_preference, get_user_settings
from bot.states import BotState
from bot.utils.logger import logger
from bot.handlers.main_menu import send_settings_menu,send_main_menu
from bot.utils.localization import i18n
from bot.services import settings as settings_service
from bot.config import ADD_PLACE_BOT_USERNAME

router = Router()


@router.message(F.text.in_(["🔗 Додати місце", "🔗 Add place", "🔗 Ort hinzufügen", "🔗 Ajouter un lieu", "🔗 Añadir lugar", "🔗 Aggiungi luogo", "🔗 Dodaj miejsce", "🔗 Adicionar local", "🔗 場所を追加", "🔗 添加地点"]))
async def add_place_redirect_handler(message: Message):
    """Пояснює, що додавання місць доступне в іншому боті, і пропонує перейти."""
    user_id = message.from_user.id
    lang_code = message.from_user.language_code
    username = ADD_PLACE_BOT_USERNAME if ADD_PLACE_BOT_USERNAME.startswith(
        "@") else f"@{ADD_PLACE_BOT_USERNAME}"
    await message.answer(
        i18n.get(user_id, 'add_place_title', lang_code, username=username),
        parse_mode="HTML",
        reply_markup=add_place_redirect_keyboard(user_id, lang_code),
    )


@router.message(F.text.in_(["🌐 Мова", "🌐 Language", "🌐 Sprache", "🌐 Langue", "🌐 Idioma", "🌐 Lingua", "🌐 Język", "🌐 Idioma", "🌐 言語", "🌐 语言"]))
async def language_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang_code = message.from_user.language_code
    logger.info(f"Користувач {message.from_user.username}({user_id}) хоче змінити мову")
    
    # Показуємо доступні мови через inline клавіатуру
    builder = InlineKeyboardBuilder()
    
    for code, name in i18n.get_available_languages().items():
        builder.button(
            text=name,
            callback_data=f"set_lang:{code}"
        )
    
    builder.adjust(2)
    
    await message.answer(
        i18n.get(user_id, 'select_language', lang_code),
        reply_markup=builder.as_markup()
    )
    await state.clear()


@router.callback_query(F.data.startswith("set_lang:"))
async def set_language_callback(callback: CallbackQuery):
    """Обробка вибору мови"""
    user_id = callback.from_user.id
    lang_code = callback.data.split(":")[1]
    
    # Встановлюємо мову в системі локалізації
    if i18n.set_user_language(user_id, lang_code):
        lang_name = i18n.get_available_languages().get(lang_code, lang_code)
        await callback.answer(f"✅ {lang_name}")
        await callback.message.edit_text(
            i18n.get(user_id, 'language_changed', lang_code, language=lang_name)
        )
        # Показуємо оновлене меню налаштувань
        await send_settings_menu(callback.message, user_id=user_id, telegram_lang_code=lang_code)
    else:
        await callback.answer("❌ Error")


@router.message(F.text.in_(["📏 Радіус", "📏 Radius", "📏 Rayon", "📏 Radio", "📏 Raggio", "📏 Promień", "📏 Raio", "📏 半径"]))
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
    
    for label,code in popular_types:
        builder.button(
            text=label,
            callback_data=f"add_included_type:{code}"
        )

    builder.button(text="🧹 Скинути категорії",
                   callback_data="cancel_included_types")


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

@router.callback_query(F.data.startswith("add_included_type:"))
async def add_included_type_callback(callback: CallbackQuery, state: FSMContext):
    type_code = callback.data.split(":")[1]
    settings_service.add_included_type(callback.from_user.id, type_code)
    await callback.answer("✅ Категорію додано!")
    await state.clear()
    await send_settings_menu(callback.message, user_id=callback.from_user.id)

@router.callback_query(F.data.startswith("add_included_list_type:"))

async def add_list_included(callback:CallbackQuery,state:FSMContext):
    type_code = callback.data.split(":")[1]
    settings_service.add_included_type(callback.from_user.id, type_code)

    await callback.answer("✅ Категорії додані!")
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
    await send_settings_menu(message)


@router.callback_query(F.data == "cancel_included_types")
async def clear_included_types_callback(callback: CallbackQuery, state: FSMContext):
    settings_service.clear_included_types(callback.from_user.id)
    await callback.answer("✅ Категорії скинуто!")
    await state.clear()
    await send_settings_menu(callback.message, user_id=callback.from_user.id)


@router.message(F.text == "🧹 Скинути категорії", BotState.waiting_for_category)
async def clear_included_types_handler(message: Message, state: FSMContext):
    settings_service.clear_included_types(message.from_user.id)
    await message.answer("✅ Категорії скинуто!")
    await state.clear()
    await send_settings_menu(message)


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
    await send_settings_menu(message)
    await send_settings_menu(message)


@router.message(StateFilter(BotState.selecting_language, BotState.selecting_radius,
                            BotState.selecting_included_types, BotState.selecting_excluded_types,
                            BotState.selecting_max_result_count), F.text == "🔙 Скасувати")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await send_settings_menu(message)


@router.message(F.text == "⏰ Відкрите зараз")
async def open_now_handler(message: Message):
    current_settings = get_user_settings(message.from_user.id)
    current_open_now = current_settings.get("openNow", False)

    new_open_now = not current_open_now
    settings_service.update_open_now(message.from_user.id, new_open_now)

    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) змінив налаштування 'відкрите зараз' на {new_open_now}")
    await send_settings_menu(message)


@router.message(BotState.selecting_language)
async def set_language_handler(message: Message, state: FSMContext):
    lang = message.text.strip()
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) змінив мову на {lang}")
    update_language(message.from_user.id, lang)
    await state.clear()
    await send_settings_menu(message)
    await send_settings_menu(message)


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
    await send_settings_menu(message)
    await send_settings_menu(message)


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
    await send_settings_menu(message)
    await send_settings_menu(message)


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
    await send_settings_menu(message)
    await send_settings_menu(message)


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
    await send_settings_menu(message)
