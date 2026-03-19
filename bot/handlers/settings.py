from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from bot.keyboards import actions_keyboard, add_place_redirect_keyboard, choose_location_type_keyboard, build_mood_inline_keyboard
from aiogram.filters import StateFilter
from bot.services.settings import update_language, update_radius, update_included_types, update_excluded_types, update_max_result_count, update_rank_preference, get_user_settings, get_settings_payload_for_api
from bot.states import BotState
from bot.utils.logger import logger
from bot.handlers.main_menu import send_settings_menu,send_main_menu
from bot.utils.localization import i18n
from bot.services import settings as settings_service
from bot.config import ADD_PLACE_BOT_USERNAME
from bot.services.api_client import save_user_settings
import aiohttp

router = Router()


# @router.message(F.text.in_(["🔗 Додати місце", "🔗 Add place", "🔗 Ort hinzufügen", "🔗 Ajouter un lieu", "🔗 Añadir lugar", "🔗 Aggiungi luogo", "🔗 Dodaj miejsce", "🔗 Adicionar local", "🔗 場所を追加", "🔗 添加地点"]))
# async def add_place_redirect_handler(message: Message):
#     """Пояснює, що додавання місць доступне в іншому боті, і пропонує перейти."""
#     user_id = message.from_user.id
#     lang_code = message.from_user.language_code
#     username = ADD_PLACE_BOT_USERNAME if ADD_PLACE_BOT_USERNAME.startswith("@") else f"@{ADD_PLACE_BOT_USERNAME}"
#     await message.answer(
#         "📌 <b>Додавання власних місць</b>\n\n"
#         "У цьому боті можна лише <b>шукати</b> місця поруч.\n"
#         "Щоб <b>додати своє місце</b> до карти, скористайтесь окремим ботом:\n\n"
#         f"👉 {username}",
#         parse_mode="HTML",
#         reply_markup=add_place_redirect_keyboard(user_id, lang_code),
#     )


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
async def set_language_callback(callback: CallbackQuery, session: aiohttp.ClientSession):
    """Обробка вибору мови"""
    user_id = callback.from_user.id
    lang_code = callback.data.split(":")[1]
    
    # Встановлюємо мову в системі локалізації (user_languages)
    if i18n.set_user_language(user_id, lang_code):
        # Оновлюємо мову в user_settings
        settings = get_user_settings(user_id)
        settings["language"] = lang_code
        
        # Зберігаємо налаштування на сервер
        payload = get_settings_payload_for_api(user_id)
        await save_user_settings(user_id, payload, session)
        logger.info(f"Language saved to server: {lang_code} for user {user_id}")
        
        lang_name = i18n.get_available_languages().get(lang_code, lang_code)
        await callback.answer(f"✅ {lang_name}")
        await callback.message.edit_text(
            i18n.get(user_id, 'language_changed', lang_code, language=lang_name)
        )
        # Показуємо оновлене меню налаштувань
        await send_settings_menu(callback.message, user_id=user_id)
    else:
        await callback.answer("❌ Error")


@router.message(F.text.in_(["📏 Радіус", "📏 Radius", "📏 Rayon", "📏 Radio", "📏 Raggio", "📏 Promień", "📏 Raio", "📏 半径"]))
async def radius_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    logger.info(
        f"Користувач {message.from_user.username}({user_id}) хоче змінити радіус")
    await state.set_state(BotState.selecting_radius)
    await message.answer(
        i18n.get(user_id, 'enter_radius_prompt', lang_code),
        reply_markup=cancel_keyboard()
    )







@router.message(F.text.in_(["🎧 Вибрати за настроєм", "🎧 Select by mood", "🎧 Nach Stimmung wählen", "🎧 Sélectionner par humeur", "🎧 Seleccionar por ánimo", "🎧 Seleziona per umore", "🎧 Wybierz według nastroju", "🎧 Selecionar por humor", "🎧 気分で選択", "🎧 按心情选择"]))
async def mood_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    current_mood = (settings.get("mood") or "").strip().lower() or None
    await message.answer(
        i18n.get(user_id, "choose_mood", lang_code, current=""),
        parse_mode="HTML",
        reply_markup=build_mood_inline_keyboard(user_id, lang_code, current_mood=current_mood, add_clear=True),
    )


@router.callback_query(F.data.startswith("set_mood:"))
async def set_mood_callback(callback: CallbackQuery, state: FSMContext, session: aiohttp.ClientSession):
    user_id = callback.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")

    mood = callback.data.split(":", 1)[1]
    current = (settings.get("mood") or "").strip().lower()
    # Перемикач: натиснули ту саму кнопку — знімаємо галочку
    if current == mood:
        settings_service.update_mood(user_id, "")
        new_current = None
        await callback.answer(i18n.get(user_id, "categories_reset", lang_code))
    else:
        settings_service.update_mood(user_id, mood)
        new_current = mood
        await callback.answer(i18n.get(user_id, "category_added", lang_code))

    fsm_data = await state.get_data()
    first_start = fsm_data.get("first_start", False)
    reply_markup = build_mood_inline_keyboard(
        user_id, lang_code, current_mood=new_current, add_clear=not first_start
    )
    await callback.message.edit_reply_markup(reply_markup=reply_markup)


@router.callback_query(F.data == "clear_mood")
async def clear_mood_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")

    settings_service.update_mood(user_id, "")

    await callback.answer(i18n.get(user_id, "categories_reset", lang_code))
    reply_markup = build_mood_inline_keyboard(user_id, lang_code, current_mood=None, add_clear=True)
    await callback.message.edit_reply_markup(reply_markup=reply_markup)


@router.message(F.text.in_(["🍴 Вибрати категорії", "🍴 Select categories", "🍴 Kategorien auswählen", "🍴 Sélectionner les catégories", "🍴 Seleccionar categorías", "🍴 Seleziona categorie", "🍴 Wybierz kategorie", "🍴 Selecionar categorias", "🍴 カテゴリーを選択", "🍴 选择类别"]))
async def included_types_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    
    builder = InlineKeyboardBuilder()

    popular_types = [
        (i18n.get(user_id, 'category_restaurant', lang_code), "restaurant"),
        (i18n.get(user_id, 'category_cafe', lang_code), "cafe"),
        (i18n.get(user_id, 'category_bar', lang_code), "bar"),
        (i18n.get(user_id, 'category_fastfood', lang_code), "fast_food_restaurant"),
        (i18n.get(user_id, 'category_pharmacy', lang_code), "pharmacy"),
        (i18n.get(user_id, 'category_store', lang_code), "store")
    ]

    for label, code in popular_types:
        builder.button(
            text=label,
            callback_data=f"add_included_type:{code}"
        )

    builder.button(text=i18n.get(user_id, 'category_reset', lang_code),
                   callback_data="cancel_included_types")

    builder.adjust(2)

    included = settings.get("includedTypes", [])
    current_line = i18n.get(user_id, 'current_categories', lang_code, categories=', '.join(included)) if included else ""

    await message.answer(
        i18n.get(user_id, 'choose_category', lang_code, current=current_line),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

    await state.set_state(BotState.waiting_for_category)

@router.message(F.text == "✅ Включити типи")
async def included_types_handler(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()


    popular_types = [
        ("🍝 Ресторан",  "restaurant"),
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
    user_id = callback.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    type_code = callback.data.split(":")[1]
    settings_service.add_included_type(user_id, type_code)
    await callback.answer(i18n.get(user_id, 'category_added', lang_code))
    await state.clear()
    await send_settings_menu(callback.message, user_id=user_id)

@router.callback_query(F.data.startswith("add_included_list_type:"))
async def add_list_included(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    type_code = callback.data.split(":")[1]
    settings_service.add_included_type(user_id, type_code)
    await callback.answer(i18n.get(user_id, 'categories_added', lang_code))
    await state.clear()
    await send_main_menu(callback.message, user_id=user_id)

@router.message(BotState.waiting_for_category)
async def add_custom_category_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    user_text = (message.text or "").strip()

    if len(user_text) < 3:
        await message.answer(i18n.get(user_id, 'category_too_short', lang_code))
        return

    settings_service.add_included_type(user_id, user_text)
    await message.answer(i18n.get(user_id, 'custom_category_accepted', lang_code, category=user_text))
    await state.clear()
    await send_main_menu(message)


@router.callback_query(F.data == "cancel_included_types")
async def clear_included_types_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    # Reset both manual categories and mood preset to avoid stale mood label in settings.
    settings_service.update_mood(user_id, "")
    await callback.answer(i18n.get(user_id, 'categories_reset', lang_code))
    await state.clear()
    await send_settings_menu(callback.message, user_id=user_id)


@router.message(F.text == "🧹 Скинути категорії", BotState.waiting_for_category)
async def clear_included_types_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    # Reset both manual categories and mood preset to avoid stale mood label in settings.
    settings_service.update_mood(user_id, "")
    await message.answer(i18n.get(user_id, 'categories_reset', lang_code))
    await state.clear()
    await send_main_menu(message)


# @router.message(F.text.in_(["🔢 Кількість", "🔢 Count", "🔢 Anzahl", "🔢 Nombre", "🔢 Cantidad", "🔢 Quantità", "🔢 Liczba", "🔢 Quantidade", "🔢 件数", "🔢 数量"]))
# async def max_result_count_handler(message: Message, state: FSMContext):
#     user_id = message.from_user.id
#     settings = get_user_settings(user_id)
#     lang_code = settings.get("language", "uk")
#     await state.set_state(BotState.selecting_max_result_count)
#     await message.answer(
#         i18n.get(user_id, 'enter_count_prompt', lang_code),
#         reply_markup=cancel_keyboard()
#     )


@router.message(F.text.in_([
    "🔀 Сортування", "🔀 Sorting", "🔀 Sortierung", "🔀 Tri", "🔀 Ordenar", "🔀 Ordinamento", "🔀 Sortowanie", "🔀 Ordenação", "🔀 並び替え", "🔀 排序",
    
]))
async def rank_preference_handler(message: Message):
    current_settings = get_user_settings(message.from_user.id)
    current_rank = current_settings.get("rankPreference", "POPULARITY")

    new_rank = "DISTANCE" if current_rank == "POPULARITY" else "POPULARITY"
    update_rank_preference(message.from_user.id, new_rank)

    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) змінив сортування на {new_rank}")
    await send_settings_menu(message)
    


@router.message(StateFilter(BotState.selecting_language, BotState.selecting_radius,
                            BotState.selecting_included_types, BotState.selecting_excluded_types,
                            BotState.selecting_max_result_count), F.text.in_(["🔙 Скасувати", "🔙 Cancel", "🔙 Abbrechen", "🔙 Annuler", "🔙 Cancelar", "🔙 Annulla", "🔙 Anuluj", "🔙 Cancelar", "🔙 キャンセル", "🔙 取消"]))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await send_settings_menu(message, user_id=message.from_user.id)


@router.message(F.text.in_(["⏰ Відкрите зараз", "⏰ Open now", "⏰ Jetzt geöffnet", "⏰ Ouvert maintenant", "⏰ Abierto ahora", "⏰ Aperto ora", "⏰ Otwarte teraz", "⏰ Aberto agora", "⏰ 営業中", "⏰ 现在营业"]))
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
    await send_settings_menu(message)
    await send_settings_menu(message)


@router.message(BotState.selecting_radius)
async def set_radius_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    radius = message.text.strip()
    if not radius.isdigit():
        await message.answer(i18n.get(user_id, 'enter_number_error', lang_code))
        return
    if not (1 <= int(radius) <= 5000):
        await message.answer(i18n.get(user_id, 'enter_radius_range_error', lang_code))
        return

    logger.info(
        f"Користувач {message.from_user.username}({user_id}) змінив радіус на {radius}")
    update_radius(user_id, radius)
    await state.clear()
    await send_settings_menu(message, user_id=user_id)
    


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


# @router.message(BotState.selecting_max_result_count)
# async def set_max_result_count_handler(message: Message, state: FSMContext):
#     user_id = message.from_user.id
#     settings = get_user_settings(user_id)
#     lang_code = settings.get("language", "uk")
#     text = message.text.strip()
#     if not text.isdigit() or not (1 <= int(text) <= 20):
#         await message.answer(i18n.get(user_id, 'enter_count_range_error', lang_code))
#         return
#
#     update_max_result_count(user_id, int(text))
#     logger.info(
#         f"Користувач {message.from_user.username}({user_id}) змінив кількість результатів на {int(text)}")
#     await state.clear()
#     await send_settings_menu(message, user_id=user_id)
