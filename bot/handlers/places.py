import aiohttp
from aiogram import Router, F
from aiogram.types import KeyboardButton, Message, CallbackQuery, InputMediaPhoto, ReplyKeyboardMarkup
from bot.handlers.main_menu import send_main_menu
from bot.keyboards import places_keyboard, place_details_keyboard,custom_places_keyboard
from bot.services.api_client import get_photos, get_places, get_place_details,add_custom_place,get_all_custom_places,get_custom_place_by_id
from bot.services.settings import get_user_settings
from bot.utils.formatter import format_place_text,format_custom_place_text
from aiogram.fsm.context import FSMContext
from bot.utils.logger import logger
from bot.model.place import Place
from bot.states import AddPlace




router = Router()

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
        await message.answer("[Адреса збережена]\nНадай фото місцевості")
        await state.set_state(AddPlace.wait_for_foto)
    else:
        await message.answer("[помилка в збережені]")
        send_main_menu()
@router.message(AddPlace.wait_for_foto,(F.photo | F.document))
async def add_photo(message:Message,state:FSMContext,session: aiohttp.ClientSession):
    info_photo = message.photo
    info_doc = message.document

    data = await state.get_data()

    place = Place()
    place.NameOfPlace =  data.get("title")
    place.Description =  data.get("discription")
    place.Address =  data.get("adress")
    
    if(info_photo!=None):
        place.PhotoUrl = "photo"
    else :
        place.PhotoUrl = "photo"

    result = await add_custom_place(place,session)

    if(result == True):
        await message.answer("Place added")
        await send_main_menu(message)
    else:
        await message.answer("We got error")
        await send_main_menu(message)

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

    place = await get_place_details(place_id, session, language)
    photos = await get_photos(place_id, session)

    if not place:
        await callback.message.answer("⚠️ <b>Інформацію про це місце не знайдено.</b>", parse_mode="HTML")
        return

    kb = place_details_keyboard(
        place.get("websiteUri"),
        place.get("googleMapsUri")
    )

    # надсилаємо фото
    if photos:
        try:
            media_group = [InputMediaPhoto(media=photo)
                           for photo in photos[:10]]
            if media_group:
                await callback.message.answer_media_group(media_group)
        except Exception as e:
            logger.error(f"Failed to send photos for place {place_id}: {e}")

    await callback.message.answer(
        format_place_text(place),
        parse_mode="HTML",
        reply_markup=kb,
        disable_web_page_preview=True
    )

    # надсилаємо мапу
    if place.get("latitude") and place.get("longitude"):
        await callback.message.answer_location(
            latitude=place["latitude"],
            longitude=place["longitude"]
        )
