import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from bot.keyboards import places_keyboard, place_details_keyboard
from bot.services.api_client import get_photos, get_places, get_place_details
from bot.services.settings import get_user_settings
from bot.utils.formatter import format_place_text
from bot.utils.logger import logger

router = Router()


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

        kb = places_keyboard(places)
        # Якщо клавіатура порожня (немає жодної кнопки) — fallback: просто текстовий список
        if not kb.inline_keyboard or len(kb.inline_keyboard) == 0:
            preview = []
            for idx, place in enumerate(places[:10], 1):
                name = place.get('displayName') or place.get('name') or 'Без назви'
                address = place.get('shortFormattedAddress') or ''
                rating = place.get('rating')
                rating_str = f" | ⭐ {rating}" if rating else ""
                preview.append(f"<b>{idx}.</b> {name}{rating_str}\n<code>{address}</code>")
            text = "\n\n".join(preview)
            await loading_msg.edit_text(
                f"✅ <b>Знайдено {len(places)} місць:</b>\n\n{text}",
                parse_mode="HTML"
            )
        else:
            await loading_msg.edit_text(
                f"✅ <b>Знайдено {len(places)} місць:</b>\n"
                "Оберіть місце, щоб відкрити його на карті:",
                parse_mode="HTML",
                reply_markup=kb
            )

    except Exception as e:
        logger.error(f"Error in find_places_handler: {e}")
        await loading_msg.edit_text(
            "❌ <b>Сталася помилка при обробці запиту.</b>",
            parse_mode="HTML"
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




