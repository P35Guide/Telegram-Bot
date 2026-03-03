from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import ADD_PLACE_BOT_USERNAME


def choose_location_type_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Передати мою локацію",
                            request_location=True)],
            [KeyboardButton(text="🏙️ Знайти потрібне місто")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def actions_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Передати координати")],
            [KeyboardButton(text="🚀 Пошук маршрутів")],
            [
                KeyboardButton(text="🌐 Мова"),
                KeyboardButton(text="📏 Радіус"),
            ],
            [
                KeyboardButton(text="🍴 Вибрати категорії"),
                KeyboardButton(text="🔢 Кількість"),
            ],
            [
                KeyboardButton(text="⭐ Сортування"),
                KeyboardButton(text="⏰ Відкрите зараз"),
            ],
            [KeyboardButton(text="🔗 Додати місце")]
        ],
        resize_keyboard=True
    )
    return keyboard


def add_place_redirect_keyboard():
    """Інлайн-клавіатура з посиланням на бота для додавання місць."""
    username = ADD_PLACE_BOT_USERNAME.lstrip("@")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Перейти до бота",
                              url=f"https://t.me/{username}")],
    ])


def search_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Місця"), KeyboardButton(text="🔍 Список")],
            [KeyboardButton(text="🎲 Випадкове місце"),
             KeyboardButton(text="🌟 Улюблені")],
            [KeyboardButton(text="🔙 Скасувати")],
        ],
        resize_keyboard=True
    )
    return keyboard


def random_choice_keyboard():
    """Клавіатура вибору типу випадкового місця (з пошуку чи з улюблених)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎲 Випадкове місце"), KeyboardButton(
                text="❤️ Випадкове з улюблених")],
            [KeyboardButton(text="🔙 Скасувати")],
        ],
        resize_keyboard=True
    )


def cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Скасувати")]],
        resize_keyboard=True
    )
    return keyboard


def places_keyboard(places):
   
    builder = InlineKeyboardBuilder()

    for place in places:
        place_id = place.get("id") or place.get("Id")
        if place_id:
            name = place.get("displayName") or place.get(
                "DisplayName") or place.get("name") or place.get("Name") or place.get("NameOfPlace")

            # Додаємо статус відчинено/зачинено
            open_now = place.get("openNow") or place.get("OpenNow")
            if open_now is True:
                name = f"🟢 {name}"
            elif open_now is False:
                name = f"🔴 {name}"

            builder.button(
                text=name,
                callback_data=f"place_view:{place_id}"
            )

    builder.adjust(2)
    return builder.as_markup()


def place_details_keyboard(place_url=None, google_maps_url=None, favorite_callback=None, is_favorite=False):
    """
    Генерує клавіатуру для детального перегляду місця.
    """
    builder = InlineKeyboardBuilder()

    if place_url:
        builder.button(text="🌍 Сайт", url=place_url)

    if google_maps_url:
        builder.button(text="📍 Карта", url=google_maps_url)

    if favorite_callback:
        builder.button(
            text="🌟 Додати до улюблених" if not is_favorite else "🌟 Вилучити з улюблених",
            callback_data=favorite_callback
        )

    return builder.as_markup()


def place_navigation_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="➡️ Далі")],
            [KeyboardButton(text="🛑 Стоп")],
        ],
        resize_keyboard=True
    )

    return keyboard


def favorites_action_keyboard():
    """Клавіатура для вибору дії з улюбленими місцями."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🌟 Переглянути"), KeyboardButton(text="⚖️ Порівняти")],
            [KeyboardButton(text="🔙 Скасувати")],
        ],
        resize_keyboard=True
    )


def select_favorites_for_comparison_keyboard(favorites, selected_ids: list = None):
    """
    Генерує інлайн-клавіатуру для вибору закладів до порівняння.
    Показує галочки для обраних закладів.
    """
    if selected_ids is None:
        selected_ids = []
    
    builder = InlineKeyboardBuilder()
    
    for favorite in favorites:
        place_id = favorite.get("id")
        name = favorite.get("name", "Без назви")
        is_selected = place_id in selected_ids
        
        # Додаємо галочку якщо обрано
        checkbox = "✅" if is_selected else "⬜"
        display_name = f"{checkbox} {name}"
        
        builder.button(
            text=display_name,
            callback_data=f"compare_toggle:{place_id}"
        )
    
   
    builder.adjust(1)
    
    
    if len(selected_ids) >= 2:
        builder.button(
            text="⚖️ Порівняти обрані",
            callback_data="perform_comparison"
        )
    else:
        builder.button(
            text="⚖️ Обрати мінімум 2 (обрано: {})".format(len(selected_ids)),
            callback_data="comparison_help"
        )
    
    builder.button(
        text="🔙 Скасувати",
        callback_data="cancel_comparison"
    )
    
    return builder.as_markup()
