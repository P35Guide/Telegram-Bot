import aiohttp
from aiogram import Router, F
from aiogram.types import KeyboardButton, Message, CallbackQuery, InputMediaPhoto, ReplyKeyboardMarkup,BufferedInputFile
from bot.handlers.main_menu import send_main_menu
from bot.keyboards import places_keyboard, place_details_keyboard,custom_places_keyboard
from bot.services.api_client import get_photos, get_places, get_place_details,add_custom_place,get_all_custom_places,get_custom_place_by_id
from bot.services.settings import get_user_settings
from bot.utils.formatter import format_place_text,format_custom_place_text
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import aiohttp
import random
from ssl import SSLContext

from bot.handlers.main_menu import send_main_menu
from bot.keyboards import (
    place_navigation_keyboard,
    search_keyboard,
    places_keyboard,
    place_details_keyboard,
    choose_location_type_keyboard,
)
from bot.services.api_client import get_photos, get_places, get_place_details
from bot.services.settings import (
    add_favorite_place,
    get_favorite_places,
    get_user_settings,
    is_favorite_place,
    remove_favorite_place,
)
from bot.states import BotState
from bot.utils.formatter import format_place_text
from bot.utils.logger import logger
from bot.model.place import Place
from bot.states import AddPlace
from aiogram import Bot
import base64




router = Router()
_place_name_cache: dict[str, str] = {}

@router.message(F.text == "📌 Додати своє місце")
async def add_place_handler(message:Message,state:FSMContext):
    logger.info(
        f"Користувач {message.from_user.username} ({message.from_user.id}) додає своє місце"
    )
    await message.answer('Введи назву міця')
    await state.set_state(AddPlace.wait_for_title)
@router.message(AddPlace.wait_for_title)
async def add_title(message:Message,state:FSMContext):
    info = message.text
    await state.update_data(title=info)
    data = await state.get_data()
    saved = data.get("title")

    if(saved == info):
        logger.info("title local saved")
        await message.answer("[Назва збережена]\nВведи опис місця")
        await state.set_state(AddPlace.wait_for_discription)
    else:
        await message.answer("[помилка в збережені]")
        send_main_menu()
@router.message(AddPlace.wait_for_discription)
async def add_discription(message:Message,state:FSMContext):
    info = message.text
    await state.update_data(discription=info)
    data = await state.get_data()
    saved = data.get("discription")

    if(saved == info):
        logger.info("discription local saved")
        await message.answer("[Опис збережений]\nВведи адресу місця")
        await state.set_state(AddPlace.wait_for_shor_adress)
    else:
        await message.answer("[помилка в збережені]")
        send_main_menu()
@router.message(AddPlace.wait_for_shor_adress)
async def add_adress(message:Message,state:FSMContext):
    info = message.text
    await state.update_data(adress=info)
    data = await state.get_data()
    saved =  data.get("adress")

    if(saved == info):
        logger.info("adress local saved")
        await message.answer("[Адреса збережена]\nНадай 5 фото місцевості")
        await state.set_state(AddPlace.wait_for_foto)
    else:
        await message.answer("[помилка в збережені]")
        send_main_menu()
@router.message(AddPlace.wait_for_foto,F.photo)
async def add_photo(message:Message,state:FSMContext,bot:Bot,session:aiohttp.ClientSession):
    data = await state.get_data()
    photos_ids = data.get("photos",[])

    photos_ids.append(message.photo[-1].file_id)

    await state.update_data(photos = photos_ids)

    number_photo = len(photos_ids)

    if(number_photo<5):
        return

    encoded_phtos = []

    for photo_id in photos_ids:
        file = await bot.get_file(photo_id)

        photo_buffer = await bot.download_file(file.file_path)

        photo_byts = photo_buffer.read()
        base64photo = base64.b64encode(photo_byts).decode("utf-8")
        encoded_phtos.append(base64photo)
    
    place = Place()

    place.NameOfPlace =  data.get("title")
    place.Description =  data.get("discription")
    place.Address =  data.get("adress")

    place.Photo1 = encoded_phtos[0]
    place.Photo2 = encoded_phtos[1]
    place.Photo3 = encoded_phtos[2]
    place.Photo4 = encoded_phtos[3]
    place.Photo5 = encoded_phtos[4]

    result = await add_custom_place(place,session)

    if(result == True):
        await message.answer("Place added")
        await send_main_menu(message)
    else:
        await message.answer("We got error")
        await send_main_menu(message)


# Обробник кнопки "📍 Надіслати геолокацію" (показує вибір способу)
@router.message(F.text == "📍 Надіслати геолокацію")
async def choose_location_method(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(BotState.choosing_location_type)
    await message.answer(
        "Оберіть спосіб передачі координат:",
        reply_markup=choose_location_type_keyboard()
    )


# Обробка вибору типу локації
@router.message(BotState.choosing_location_type)
async def handle_location_type_choice(message: Message, state: FSMContext):
    if message.text == "📍 Передати мою локацію":
        await message.answer("Будь ласка, надішліть свою геолокацію через кнопку нижче.")
    elif message.text == "🏙️ Знайти потрібне місто":
        await state.set_state(BotState.entering_coordinates)
        await message.answer("Введіть назву міста, для якого потрібно знайти координати:")
    else:
        await message.answer("Будь ласка, оберіть один із варіантів.", reply_markup=choose_location_type_keyboard())


# Команда /coordinates для отримання координат користувача
@router.message(Command("coordinates"))
async def show_user_coordinates(message: Message):
    coords = get_user_settings(message.from_user.id).get("coordinates")
    if coords:
        await message.answer(
            f"Ваші координати:\nШирота: {coords['latitude']}\nДовгота: {coords['longitude']}"
        )
    else:
        await message.answer("Координати не встановлено. Спочатку оберіть місто або надішліть свою геолокацію.")


def filter_open_now(places, open_now):
    if not open_now:
        return places
    return [p for p in places if (p.get("openNow") is True or p.get("OpenNow") is True)]


@router.message(F.text == "🎲 Випадкове місце")
async def random_place_handler(message: Message, session: aiohttp.ClientSession):
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) шукає випадкове місце")

    await message.answer_dice(emoji="🎲")

    loading_msg = await message.answer(
        "⏳ <b>Крутимо рулетку...</b>\n"
        "Зачекайте, виконується запит до API...",
        parse_mode="HTML"
    )

    settings = get_user_settings(message.from_user.id)

    if not settings.get("coordinates"):
        await loading_msg.delete()
        await message.answer(
            "❌ <b>Помилка:</b> Не встановлено геолокацію!\n"
            "Будь ласка, надішліть геолокацію або введіть координати:",
            parse_mode="HTML",
            reply_markup=choose_location_type_keyboard()
        )
        return




@router.message(F.text == "🧾 Дістати місця користувачів")
async def get_custom_places(message:Message,session:aiohttp.ClientSession):
    alert = await message.answer("🔍 <b>Пошук місць створених користувачами...</b>\n\n"
                           "⏳ Зачекайте, виконується запит до API...")
    try:

        info = await get_all_custom_places(session)
        if(info == None):
            await alert.edit_text("⚠️ <b>Нічого не знайдено</b> або сервер не відповідає.")
            return
        
        places = info
        
        await alert.edit_text(
            f"✅ <b>Знайдено {len(places)} місць:</b>\n"
            "Оберіть місце, щоб відкрити його на карті:",
            reply_markup=custom_places_keyboard(places)
        )

    except Exception as e:
        logger.error(f"Error in find_places_handler: {e}")

@router.message(F.text == "🔍 Знайти місця поруч")
async def find_places_handler(message: Message, session: aiohttp.ClientSession):
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) шукає місця поруч")

    loading_msg = await message.answer(
        "🔍 <b>Пошук місць поруч...</b>\n\n"
        "⏳ Зачекайте, виконується запит до API...",
        parse_mode="HTML"
    )

    settings = get_user_settings(message.from_user.id)

    if not settings.get("coordinates"):
        await loading_msg.edit_text(
            "❌ <b>Помилка:</b> Не встановлено геолокацію!\n"
            "Будь ласка, натисніть кнопку '📍 Надіслати геолокацію', щоб ми знали де шукати.",
            parse_mode="HTML"
        )
        return

    try:
        data = await get_places(settings, session)

        if not data or "places" not in data:
            await loading_msg.edit_text(
                "⚠️ <b>Нічого не знайдено</b> або сервер не відповідає.",
                parse_mode="HTML"
            )
            return

        places = data["places"]
        if not places:
            await loading_msg.edit_text(
                "📭 <b>На жаль, місць поруч не знайдено.</b>\n"
                "Спробуйте збільшити радіус пошуку.",
                parse_mode="HTML"
            )
            return

        await loading_msg.edit_text(
            f"✅ <b>Знайдено {len(places)} місць:</b>\n"
            "Оберіть місце, щоб відкрити його на карті:",
            parse_mode="HTML",
            reply_markup=places_keyboard(places)
        )

    except Exception as e:
        logger.error(f"Error in find_places_handler: {e}")
        await loading_msg.edit_text(
            "❌ <b>Сталася помилка при обробці запиту.</b>",
            parse_mode="HTML"
        )


@router.message(F.text == "🔙 Скасувати")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await send_main_menu(message)


async def show_places_list(loading_msg, places, title: str = "Знайдено {count} місць"):
    """
    Оновлює повідомлення списком місць: клавіатура з назвами або текстовий fallback.
    title — рядок з плейсхолдером {count}.
    """
    count = len(places)
    heading = title.format(count=count)
    kb = places_keyboard(places)
    if not kb.inline_keyboard or len(kb.inline_keyboard) == 0:
        preview = []
        for idx, place in enumerate(places[:10], 1):
            name = place.get("displayName") or place.get("name") or "Без назви"
            address = place.get("shortFormattedAddress") or ""
            rating = place.get("rating")
            rating_str = f" | ⭐ {rating}" if rating else ""
            preview.append(
                f"<b>{idx}.</b> {name}{rating_str}\n<code>{address}</code>")
        text = "\n\n".join(preview)
        await loading_msg.edit_text(
            f"✅ <b>{heading}:</b>\n\n{text}",
            parse_mode="HTML"
        )
    else:
        await loading_msg.edit_text(
            f"✅ <b>{heading}:</b>\nОберіть місце, щоб відкрити його на карті:",
            parse_mode="HTML",
            reply_markup=kb
        )


async def perform_search(message: Message, session: aiohttp.ClientSession, show_list: bool = True):
    """
    Логіка пошуку місць поруч.
    Повертає (loading_msg, places) кортеж.
    У разі помилки обробляє UI оновлення та повертає (loading_msg, None).
    """
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) шукає місця поруч")

    loading_msg = await message.answer(
        "🔍 <b>Пошук місць поруч...</b>\n\n"
        "⏳ Зачекайте, виконується запит до API...",
        parse_mode="HTML"
    )

    settings = get_user_settings(message.from_user.id)

    if not settings.get("coordinates"):
        await loading_msg.edit_text(
            "❌ <b>Помилка:</b> Не встановлено геолокацію!\n"
            "Оберіть спосіб передачі координат:",
            parse_mode="HTML",
            reply_markup=choose_location_type_keyboard()
        )
        return

    try:
        data = await get_places(settings, session)

        if not data or "places" not in data:
            await loading_msg.edit_text(
                "⚠️ <b>Нічого не знайдено</b> або сервер не відповідає.",
                parse_mode="HTML"
            )
            return

        places = data["places"]
        if not places:
            await loading_msg.edit_text(
                "📭 <b>На жаль, місць поруч не знайдено.</b>\n"
                "Спробуйте збільшити радіус пошуку.",
                parse_mode="HTML"
            )
            return

        if show_list:
            await show_places_list(loading_msg, places)

        return loading_msg, places

    except Exception as e:
        logger.error(f"Error in find_places_handler: {e}")
        await loading_msg.edit_text(
            "❌ <b>Сталася помилка при обробці запиту.</b>",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("custom_place_view:"))
async def custom_place_details_handler(callback:CallbackQuery,session:aiohttp.ClientSession):
    """
    Обробляє натискання на кнопку місця зі списку.
    Отримує деталі місця та надсилає їх окремим повідомленням.
    """
    place_id = callback.data.split(":")[1]
    logger.info(
        f"Користувач {callback.from_user.username}({callback.from_user.id}) переглядає місце {place_id}")
    await callback.answer()

    place = await get_custom_place_by_id(int(place_id),session)

    if(place == None):
        await callback.answer("⚠️ <b>Інформацію про це місце не знайдено.</b>", parse_mode="HTML")
        return
    
    await callback.message.answer(
        format_custom_place_text(place),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

    media_group = []
    phtos = [place.get("photo1"),place.get("photo2"),place.get("photo3"),place.get("photo4"),place.get("photo5")]

    for i,photos_base64 in enumerate(phtos):
        if(photos_base64 != None):
            photo_bytes = base64.b64decode(photos_base64)
            file = BufferedInputFile(photo_bytes,filename = f"photo{i}.jpg")
            media_group.append(InputMediaPhoto(media=file,caption=place.get("nameOfPlace") if i==0 else ""))
    await callback.message.answer_media_group(media=media_group)

async def send_place_info(
    message: Message,
    session: aiohttp.ClientSession,
    place_id: str,
    language: str,
    user_id: int | None = None,
):
    """
    Отримує деталі місця за його ID та відправляє їх користувачу.
    """
    uid = user_id if user_id is not None else (
        message.from_user.id if message.from_user else None)
    try:
        place = await get_place_details(place_id, session, language)
        if not place:
            return False

        photos = await get_photos(place_id, session)

        if photos:
            try:
                media_group = [InputMediaPhoto(media=photo)
                               for photo in photos[:10]]
                if media_group:
                    await message.answer_media_group(media_group)
            except Exception as e:
                logger.error(
                    f"Failed to send photos for place {place_id}: {e}")

        _place_name_cache[place_id] = place.get(
            "displayName") or place.get("name") or "Без назви"

        favorite_callback = f"fav_toggle:{place_id}" if place_id else None
        text = format_place_text(place)
        is_fav = is_favorite_place(uid, place_id) if uid else False
        kb = place_details_keyboard(
            place.get("websiteUri"),
            place.get("googleMapsUri"),
            favorite_callback,
            is_fav,
        )

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=kb,
            disable_web_page_preview=True
        )

        if place.get("latitude") and place.get("longitude"):
            await message.answer_location(
                latitude=place["latitude"],
                longitude=place["longitude"]
            )

        return True

    except Exception as e:
        logger.error(f"Error sending place info: {e}")
        return False
    
@router.message(F.text == "🔍 Список")
async def find_places_handler(message: Message, session: aiohttp.ClientSession):
    loading_msg, places = await perform_search(message, session)

    if not places:
        return


@router.message(F.text == "🚀 Пошук маршрутів")
async def search_menu_handler(message: Message, session: aiohttp.ClientSession):
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) запускає пошук маршрутів")

    await message.answer(
        "<b>Оберіть варіант пошуку:</b>\n"
        "🚀 <b>Місця</b> - зручно оцінити місця\n"
        "🔍 <b>Список</b> - переглянути список знайдених місць.\n"
        "🎲 <b>Випадкове місце</b> - випадково вибрати місце",
        parse_mode="HTML",
        reply_markup=search_keyboard()
    )

@router.message(F.text == "🌟 Улюблені")
async def favorite_places_handler(message: Message, session: aiohttp.ClientSession):
    """Показує список улюблених. Назви зберігаються разом з id — API не викликається."""
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) переглядає улюблені місця")

    favorites = get_favorite_places(message.from_user.id)
    if not favorites:
        await message.answer("🌟 Улюблених місць поки немає.")
        return

    places = [{"id": p["id"], "displayName": p["name"]} for p in favorites]
    loading_msg = await message.answer("🌟 Улюблені місця...", parse_mode="HTML")
    await show_places_list(loading_msg, places, "Улюблені місця ({count})")


async def show_place_card(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    data = await state.get_data()
    places = data.get("places", [])
    index = data.get("current_index", 0)

    if not places:
        await message.answer("⚠️ Список місць порожній.")
        await state.clear()
        return

    if index < 0:
        index = 0
    if index >= len(places):
        await message.answer("✅ Це було останнє місце.")
        index = len(places) - 1
        await state.update_data(current_index=index)

    place_summary = places[index]
    place_id = place_summary.get("id") or place_summary.get("Id")

    settings = get_user_settings(message.from_user.id)
    language = settings.get("language", "uk")

    loading_msg = await message.answer("⏳ Завантаження інформації...")

    success = await send_place_info(message, session, place_id, language)

    if not success:
        await loading_msg.edit_text("⚠️ Не вдалося отримати деталі місця.")
        return

    await loading_msg.delete()
    await message.answer(
        f"📍 <b>Місце {index + 1} з {len(places)}</b>",
        parse_mode="HTML",
        reply_markup=place_navigation_keyboard()
    )


@router.message(F.text == "🚀 Місця")
async def search_places_handler(message: Message, session: aiohttp.ClientSession, state: FSMContext):
    loading_msg, places = await perform_search(message, session, show_list=False)

    if not places:
        return

    await state.set_state(BotState.browsing_places)
    await state.update_data(places=places, current_index=0)

    await loading_msg.delete()

    await show_place_card(message, state, session)


@router.message(BotState.browsing_places, F.text == "➡️ Далі")
async def next_place_handler(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    places = data.get("places", [])

    if current_index < len(places) - 1:
        await state.update_data(current_index=current_index + 1)
        await show_place_card(message, state, session)
    else:
        await message.answer("✅ Це останнє місце у списку.")


@router.message(BotState.browsing_places, F.text == "⬅️ Назад")
async def prev_place_handler(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    data = await state.get_data()
    current_index = data.get("current_index", 0)

    if current_index > 0:
        await state.update_data(current_index=current_index - 1)
        await show_place_card(message, state, session)
    else:
        await message.answer("ℹ️ Це перше місце.")


@router.message(BotState.browsing_places, F.text == "🛑 Стоп")
async def stop_browsing_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("⏹ Перегляд завершено.", reply_markup=search_keyboard())


@router.callback_query(F.data.startswith("place_view:"))
async def place_details_handler(callback: CallbackQuery, session: aiohttp.ClientSession):
    """
    Обробляє натискання на кнопку місця зі списку.
    Отримує деталі місця та надсилає їх окремим повідомленням.
    """
    place_id = callback.data.split(":")[1]
    logger.info(
        f"Користувач {callback.from_user.username}({callback.from_user.id}) переглядає місце {place_id}")

    await callback.answer()

    settings = get_user_settings(callback.from_user.id)
    language = settings.get("language", "uk")

    success = await send_place_info(
        callback.message, session, place_id, language, user_id=callback.from_user.id
    )

    if not success:
        await callback.message.answer("⚠️ <b>Інформацію про це місце не знайдено.</b>", parse_mode="HTML")
        return


@router.callback_query(F.data.startswith("fav_toggle:"))
async def fav_toggle_handler(callback: CallbackQuery):
    """Додає або вилучає місце з улюблених. Назва береться з кешу — без API-запиту."""
    place_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    if is_favorite_place(user_id, place_id):
        remove_favorite_place(user_id, place_id)
        await callback.answer("❌ Вилучено з улюблених")
        return

    name = _place_name_cache.get(place_id, "Без назви")
    add_favorite_place(user_id, place_id, name)
    await callback.answer("✅ Додано до улюблених")
