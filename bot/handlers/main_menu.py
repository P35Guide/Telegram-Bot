import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.states import BotState
from bot.keyboards import (
    actions_keyboard,
    choose_location_type_keyboard,
    settings_keyboard,
    search_settings_keyboard,
    profile_keyboard,
)
from bot.services.settings import (
    save_coordinates,
    get_user_settings,
    apply_user_data_from_api,
    get_settings_payload_for_api,
)
from bot.services.api_client import (
    get_user as api_get_user,
    save_user as api_save_user,
    save_user_settings as api_save_user_settings,
    get_city_coordinates,
)
from bot.utils.logger import logger
from bot.utils.localization import i18n

router = Router()


async def _save_coordinates_and_sync(user_id: int, latitude: float, longitude: float, session: aiohttp.ClientSession):
    """Зберігає координати локально та відправляє налаштування на сервер."""
    save_coordinates(user_id, latitude, longitude)
    await api_save_user_settings(user_id, get_settings_payload_for_api(user_id), session)


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await send_main_menu(message)


@router.message(F.text.in_(["📍 Передати координати", "📍 Надіслати геолокацію", "📍 Send coordinates", "📍 Envoyer les coordonnées", "📍 Koordinaten senden", "📍 Enviar coordenadas", "📍 Invia coordinate", "📍 Wyślij współrzędne", "📍 Enviar coordenadas", "📍 座標を送信", "📍 发送坐标"]))
async def show_location_choice_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()
    await message.answer(
        i18n.get(user_id, 'choose_location_type',
                 message.from_user.language_code),
        reply_markup=choose_location_type_keyboard(user_id)
    )


def settings_text(user_id: int, telegram_lang_code: str = None) -> str:
    s = get_user_settings(user_id)
    # Використовуємо мову з налаштувань користувача
    lang_code = s.get('language', 'uk')

    included = ", ".join(s.get("includedTypes", [])) if s.get(
        "includedTypes") else i18n.get(user_id, 'all', lang_code)
    excluded = ", ".join(s.get("excludedTypes", [])) if s.get(
        "excludedTypes") else i18n.get(user_id, 'none', lang_code)

    open_now = s.get("openNow", False)
    open_status = i18n.get(user_id, 'yes', lang_code) if open_now else i18n.get(
        user_id, 'no', lang_code)

    return (
        f"{i18n.get(user_id, 'settings_title', lang_code)}\n"
        f"├ {i18n.get(user_id, 'settings_lang_label', lang_code, language=s.get('language', 'uk'))}\n"
        f"├ {i18n.get(user_id, 'settings_radius_label', lang_code, radius=s.get('radius', 1000))}\n"
        f"├ {i18n.get(user_id, 'settings_included_label', lang_code, included=included)}\n"
        f"├ {i18n.get(user_id, 'settings_excluded_label', lang_code, excluded=excluded)}\n"
        f"├ {i18n.get(user_id, 'settings_count_label', lang_code, count=s.get('maxResultCount', 20))}\n"
        f"├ {i18n.get(user_id, 'settings_rank_label', lang_code, rank=s.get('rankPreference', 'POPULARITY'))}\n"
        f"└ {i18n.get(user_id, 'settings_open_label', lang_code, status=open_status)}"
    )


def search_settings_text(user_id: int, telegram_lang_code: str = None) -> str:
    """Текст блоку «Налаштування пошуку»: тільки радіус, категорії, кількість, сортування, відкрите зараз."""
    s = get_user_settings(user_id)
    lang_code = s.get('language', 'uk')
    included = ", ".join(s.get("includedTypes", [])) if s.get("includedTypes") else i18n.get(user_id, 'all', lang_code)
    excluded = ", ".join(s.get("excludedTypes", [])) if s.get("excludedTypes") else i18n.get(user_id, 'none', lang_code)
    open_now = s.get("openNow", False)
    open_status = i18n.get(user_id, 'yes', lang_code) if open_now else i18n.get(user_id, 'no', lang_code)
    return (
        f"{i18n.get(user_id, 'search_settings_title', lang_code)}\n"
        f"├ {i18n.get(user_id, 'settings_radius_label', lang_code, radius=s.get('radius', 1000))}\n"
        f"├ {i18n.get(user_id, 'settings_included_label', lang_code, included=included)}\n"
        f"├ {i18n.get(user_id, 'settings_excluded_label', lang_code, excluded=excluded)}\n"
        f"├ {i18n.get(user_id, 'settings_count_label', lang_code, count=s.get('maxResultCount', 20))}\n"
        f"├ {i18n.get(user_id, 'settings_rank_label', lang_code, rank=s.get('rankPreference', 'POPULARITY'))}\n"
        f"└ {i18n.get(user_id, 'settings_open_label', lang_code, status=open_status)}"
    )


async def send_main_menu(message: Message, user_id: int | None = None, telegram_lang_code: str = None):
    target_user_id = user_id or message.from_user.id
    s = get_user_settings(target_user_id)
    # Використовуємо мову з налаштувань користувача
    lang_code = s.get('language', 'uk')

    main_description = i18n.get(
        target_user_id, 'main_description', lang_code)

    reply_kb = actions_keyboard(target_user_id, lang_code)

    await message.answer(
        f"{i18n.get(target_user_id, 'welcome', lang_code)}\n\n"
        f"{main_description}",
        parse_mode="HTML",
        reply_markup=reply_kb,
    )


async def send_profile_menu(message: Message, user_id: int | None = None, telegram_lang_code: str = None):
    """Показує профіль користувача з усіма поточними налаштуваннями."""
    target_user_id = user_id or message.from_user.id
    s = get_user_settings(target_user_id)
    lang_code = s.get('language', 'uk')
    coords = s.get("coordinates")

    profile_title = i18n.get(target_user_id, 'profile_title', lang_code)
    settings_block = settings_text(target_user_id, lang_code)

    if coords:
        coords_block = i18n.get(
            target_user_id,
            'coordinates_label',
            lang_code,
            latitude=coords['latitude'],
            longitude=coords['longitude'],
        )
        text = f"{profile_title}\n\n{settings_block}\n\n{coords_block}"
    else:
        text = f"{profile_title}\n\n{settings_block}"

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=profile_keyboard(target_user_id, lang_code),
    )


async def send_settings_menu(message: Message, user_id: int | None = None, telegram_lang_code: str = None, state: FSMContext | None = None):
    """Показує головний екран налаштувань (координати, мова, налаштування пошуку, зберегти). Якщо передано state, встановлює viewing_settings."""
    if state is not None:
        await state.set_state(BotState.viewing_settings)
    target_user_id = user_id or message.from_user.id
    s = get_user_settings(target_user_id)
    lang_code = s.get('language', 'uk')
    await message.answer(
        settings_text(target_user_id, lang_code),
        parse_mode="HTML",
        reply_markup=settings_keyboard(target_user_id, lang_code),
    )


async def send_search_settings_menu(message: Message, user_id: int | None = None, telegram_lang_code: str = None, state: FSMContext | None = None):
    """Показує підменю «Налаштування пошуку» (радіус, категорії, настрій, сортування, відкрите зараз, кількість). Встановлює viewing_search_settings."""
    if state is not None:
        await state.set_state(BotState.viewing_search_settings)
    target_user_id = user_id or message.from_user.id
    s = get_user_settings(target_user_id)
    lang_code = s.get('language', 'uk')
    await message.answer(
        search_settings_text(target_user_id, lang_code),
        parse_mode="HTML",
        reply_markup=search_settings_keyboard(target_user_id, lang_code),
    )


@router.message(F.text.in_(["⚙️ Налаштування", "⚙️ Settings", "⚙️ Einstellungen", "⚙️ Paramètres", "⚙️ Ajustes", "⚙️ Impostazioni", "⚙️ Ustawienia", "⚙️ Configurações", "⚙️ 設定", "⚙️ 设置"]))
async def show_settings_menu(message: Message, state: FSMContext):
    await send_settings_menu(message, state=state)


@router.message(F.text.in_(["🔍 Налаштування пошуку", "🔍 Search settings", "🔍 Sucheinstellungen", "🔍 Paramètres de recherche", "🔍 Ajustes de búsqueda", "🔍 Impostazioni di ricerca", "🔍 Ustawienia wyszukiwania", "🔍 Configurações de pesquisa", "🔍 検索設定", "🔍 搜索设置"]))
async def show_search_settings_menu(message: Message, state: FSMContext):
    await send_search_settings_menu(message, state=state)


@router.message(F.text.in_(["👤 Профіль", "👤 Profile", "👤 Profil", "👤 Profilo"]))
async def show_profile_menu(message: Message):
    await send_profile_menu(message)


@router.message(F.text.in_(["💾 Зберегти на сервер", "💾 Save to server", "💾 Auf Server speichern", "💾 Sauvegarder sur le serveur", "💾 Guardar en servidor", "💾 Salva sul server", "💾 Zapisz na serwerze", "💾 Salvar no servidor", "💾 サーバーに保存", "💾 保存到服务器"]))
async def settings_save_handler(message: Message, session: aiohttp.ClientSession):
    """Обробник кнопки «Зберегти на сервер» — відправляє поточні налаштування на API."""
    user_id = message.from_user.id
    s = get_user_settings(user_id)
    lang_code = s.get('language', 'uk')
    payload = get_settings_payload_for_api(user_id)
    result = await api_save_user_settings(user_id, payload, session)
    if result is not None:
        await message.answer(i18n.get(user_id, 'settings_saved', lang_code))
    else:
        await message.answer(i18n.get(user_id, 'settings_save_failed', lang_code))


@router.message(F.text.in_(["🔙 Назад", "🔙 Back", "🔙 Zurück", "🔙 Retour", "🔙 Atrás", "🔙 Indietro", "🔙 Wstecz", "🔙 Voltar", "🔙 戻る", "🔙 返回"]))
async def back_to_main_menu(message: Message, state: FSMContext):
    if await state.get_state() == BotState.viewing_search_settings:
        await send_settings_menu(message, state=state)
        return
    if await state.get_state() == BotState.viewing_settings:
        await state.clear()
        await send_profile_menu(message)
        return
    await send_main_menu(message)


@router.message(CommandStart())
async def cmd_start(message: Message, session: aiohttp.ClientSession):
    user_id = message.from_user.id
    lang_code = message.from_user.language_code

    # Автоматично визначаємо мову користувача
    detected_lang = i18n.get_user_language(user_id, lang_code)
    logger.info(f"/start: user_id={user_id}, detected_lang={detected_lang}")

    # Отримуємо дані користувача з API
    data, status = await api_get_user(user_id, session)
    if status == 200 and data:
        apply_user_data_from_api(user_id, data)
    elif status == 404:
        created = await api_save_user(user_id, session)
        if created is not None:
            apply_user_data_from_api(user_id, created)

    # Встановлюємо визначену мову з Telegram, якщо у налаштуваннях ще не встановлена
    settings = get_user_settings(user_id)
    current_language = settings.get("language")

    # Якщо мова не була збережена на сервері (None, порожній рядок), встановлюємо detected_lang
    if not current_language:
        settings["language"] = detected_lang
        i18n.set_user_language(user_id, detected_lang)

        # Зберігаємо налаштування на сервер
        payload = get_settings_payload_for_api(user_id)
        await api_save_user_settings(user_id, payload, session)
        logger.info(
            f"Set user language to detected and saved to server: {detected_lang}")
    else:
        # Використовуємо мову з сервера
        detected_lang = current_language
        logger.info(f"Using language from server: {current_language}")

    # Показуємо запит про зміну мови (двома мовами: detected + English)
    lang_name = i18n.get_available_languages().get(detected_lang, detected_lang)

    # Формуємо повідомлення двома мовами - використовуємо метод get_translation
    prompt_detected = i18n.get_translation(detected_lang, 'language_prompt')
    prompt_en = i18n.get_translation('en', 'language_prompt')

    # Якщо мова не англійська, показуємо обидві
    if detected_lang != 'en':
        message_text = f"{prompt_detected}\n{prompt_en}"
    else:
        message_text = prompt_en

    # Кнопки - використовуємо метод get_translation
    builder = InlineKeyboardBuilder()
    continue_text_detected = i18n.get_translation(
        detected_lang, 'continue_with_language', language=lang_name)
    change_text_detected = i18n.get_translation(
        detected_lang, 'change_language_btn')

    builder.button(
        text=continue_text_detected,
        callback_data="start_continue"
    )
    builder.button(
        text=change_text_detected,
        callback_data="start_change_lang"
    )
    builder.adjust(1)

    await message.answer(
        message_text,
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "start_continue")
async def start_continue_callback(callback: CallbackQuery):
    """Продовжити з автоматично визначеною мовою"""
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.delete()
    await send_main_menu(callback.message, user_id=user_id)


@router.callback_query(F.data == "start_change_lang")
async def start_change_lang_callback(callback: CallbackQuery):
    """Показати вибір мови"""
    user_id = callback.from_user.id
    lang_code = callback.from_user.language_code

    # Показуємо доступні мови через inline клавіатуру
    builder = InlineKeyboardBuilder()

    for code, name in i18n.get_available_languages().items():
        builder.button(
            text=name,
            callback_data=f"start_set_lang:{code}"
        )

    builder.adjust(2)

    await callback.answer()
    await callback.message.edit_text(
        i18n.get(user_id, 'select_language', lang_code),
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("start_set_lang:"))
async def start_set_language_callback(callback: CallbackQuery, session: aiohttp.ClientSession):
    """Обробка вибору мови при старті"""
    user_id = callback.from_user.id
    lang_code = callback.data.split(":")[1]

    # Встановлюємо мову в системі локалізації (user_languages)
    if i18n.set_user_language(user_id, lang_code):
        # Оновлюємо мову в user_settings
        settings = get_user_settings(user_id)
        settings["language"] = lang_code

        # Зберігаємо налаштування на сервер
        payload = get_settings_payload_for_api(user_id)
        await api_save_user_settings(user_id, payload, session)
        logger.info(
            f"Language saved to server at start: {lang_code} for user {user_id}")

        lang_name = i18n.get_available_languages().get(lang_code, lang_code)
        await callback.answer(f"✅ {lang_name}")
        await callback.message.delete()
        # Показуємо головне меню
        await send_main_menu(callback.message, user_id=user_id, telegram_lang_code=lang_code)
    else:
        await callback.answer("❌ Error")


@router.message(F.location)
async def handle_location_main_menu(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    user_id = message.from_user.id
    lang_code = message.from_user.language_code
    lat, lon = message.location.latitude, message.location.longitude
    logger.info(
        f"Користувач {message.from_user.username}({user_id}) надіслав локацію: {lat}, {lon}")
    await _save_coordinates_and_sync(user_id, lat, lon, session)
    await state.clear()
    await message.answer(
        i18n.get(user_id, 'location_received', lang_code),
        reply_markup=actions_keyboard(user_id, lang_code),
    )


@router.message(F.text.in_(["🏙️ Знайти потрібне місто", "🏙️ Find a city", "🏙️ Stadt finden", "🏙️ Trouver une ville", "🏙️ Encontrar ciudad", "🏙️ Trova città", "🏙️ Znajdź miasto", "🏙️ Encontrar cidade", "🏙️ 都市を検索", "🏙️ 查找城市"]))
async def ask_for_city_name_main_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang_code = message.from_user.language_code
    await state.set_state(BotState.entering_coordinates)
    await message.answer(
        i18n.get(user_id, 'enter_city_name', lang_code)
    )


@router.message(StateFilter(BotState.entering_coordinates))
async def handle_city_input_main_menu(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    text = message.text.strip()
    user_id = message.from_user.id
    lang_code = message.from_user.language_code
    settings = get_user_settings(user_id)
    language = settings.get("language", "uk")

    await message.answer(i18n.get(user_id, 'searching_city', lang_code, city=text))
    coords = await get_city_coordinates(text, session, language)
    if coords and coords.get("latitude") is not None and coords.get("longitude") is not None:
        await _save_coordinates_and_sync(
            user_id, coords["latitude"], coords["longitude"], session
        )
        await state.clear()
        await message.answer(
            i18n.get(user_id, 'city_found', lang_code, city=text)
        )
        await send_main_menu(message, telegram_lang_code=lang_code)
    else:
        await message.answer(
            i18n.get(user_id, 'city_not_found', lang_code, city=text)
        )
