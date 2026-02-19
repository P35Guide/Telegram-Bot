from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from bot.keyboards import places_keyboard, place_details_keyboard
from bot.services.api_client import get_places, get_place_details
from bot.services.settings import get_user_settings
from bot.utils.formatter import format_place_text
from bot.utils.logger import logger

router = Router()

@router.message(F.text == "🔍 Знайти місця поруч")
async def find_places_handler(message: Message):
    logger.info(f"Користувач {message.from_user.id} шукає місця поруч")

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
        data = await get_places(settings)

        if not data or "Places" not in data:
            await loading_msg.edit_text(
                "⚠️ <b>Нічого не знайдено</b> або сервер не відповідає.",
                parse_mode="HTML"
            )
            return

        places = data["Places"]
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


@router.callback_query(F.data.startswith("place_view:"))
async def place_details_handler(callback: CallbackQuery):
    """
    Обробляє натискання на кнопку місця зі списку.
    Отримує деталі місця та надсилає їх окремим повідомленням.
    """
    place_id = callback.data.split(":")[1]
    logger.info(
        f"Користувач {callback.from_user.id} переглядає місце {place_id}")

    await callback.answer()

    place = await get_place_details(place_id)

    if not place:
        await callback.message.answer("⚠️ <b>Інформацію про це місце не знайдено.</b>", parse_mode="HTML")
        return

    kb = place_details_keyboard(place.get("WebsiteUri"), place.get("GoogleMapsUri"))
    
    await callback.message.answer(
        format_place_text(place),
        parse_mode="HTML",
        reply_markup=kb,
        disable_web_page_preview=True
    )

    # надсилаємо мапу
    if place.get("Latitude") and place.get("Longitude"):
        await callback.message.answer_location(
            latitude=place["Latitude"],
            longitude=place["Longitude"]
        )
