def error_action_inline_keyboard(user_id: int = None, lang_code: str = None):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=i18n.get(user_id or 0, 'menu_back', lang_code), callback_data="error_back_to_menu")]
        ]
    )
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import ADD_PLACE_BOT_USERNAME
from bot.utils.localization import i18n
from bot.utils.localization import i18n


def choose_location_type_keyboard(user_id: int = None, lang_code: str = None):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.get(user_id or 0, 'send_location', lang_code),
                            request_location=True)],
            [KeyboardButton(text=i18n.get(
                user_id or 0, 'find_city', lang_code))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def actions_keyboard(user_id: int = None, lang_code: str = None):
    """Головне меню: локація, пошук, налаштування."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.get(
                user_id or 0, 'send_coordinates', lang_code)),
             KeyboardButton(text=i18n.get(
                user_id or 0, 'search_routes', lang_code))],
            
            [KeyboardButton(text=i18n.get(user_id or 0, 'settings', lang_code))],
            # [KeyboardButton(text=i18n.get(user_id or 0, 'settings', lang_code)),
            #  KeyboardButton(text=i18n.get(user_id or 0, 'add_place', lang_code))],
        ],
        resize_keyboard=True,
    )


def settings_keyboard(user_id: int = None, lang_code: str = None):
    """Меню налаштувань пошуку (відкривається по кнопці «Налаштування»)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=i18n.get(
                    user_id or 0, 'settings_language', lang_code)),
                KeyboardButton(text=i18n.get(
                    user_id or 0, 'settings_radius', lang_code)),
            ],
            [
                KeyboardButton(text=i18n.get(
                    user_id or 0, 'settings_categories', lang_code)),
                KeyboardButton(text=i18n.get(
                    user_id or 0, 'settings_mood', lang_code)),
            ],
            [
                KeyboardButton(text=i18n.get(
                    user_id or 0, 'settings_sorting', lang_code)),
                KeyboardButton(text=i18n.get(
                    user_id or 0, 'settings_open_now', lang_code)),
            ],
            [KeyboardButton(text=i18n.get(user_id or 0, 'settings_save', lang_code))],
            # [KeyboardButton(text=i18n.get(user_id or 0, 'settings_count', lang_code))],
            [KeyboardButton(text=i18n.get(
                user_id or 0, 'menu_back', lang_code))],
        ],
        resize_keyboard=True,
    )


def build_mood_inline_keyboard(user_id: int = None, lang_code: str = None, current_mood: str | None = None, add_clear: bool = False):
    """Інлайн-клавіатура настрою. current_mood — код обраного (work/date/...) для галочки ✅. add_clear — додати кнопку «Скинути»."""
    builder = InlineKeyboardBuilder()
    moods = [
        ("mood_work", "work"),
        ("mood_date", "date"),
        ("mood_company", "company"),
        ("mood_breakfast", "breakfast"),
    ]
    cur = (current_mood or "").strip().lower()
    for mood_key, mood_code in moods:
        label = i18n.get(user_id or 0, mood_key, lang_code)
        if cur == mood_code:
            label = "✅ " + label
        builder.button(text=label, callback_data=f"set_mood:{mood_code}")
    builder.adjust(2)
    if add_clear:
        builder.row(
            InlineKeyboardButton(
                text=i18n.get(user_id or 0, "category_reset", lang_code),
                callback_data="clear_mood",
            )
        )
    return builder.as_markup()


def add_place_redirect_keyboard(user_id: int = None, lang_code: str = None):
    """Інлайн-клавіатура з посиланням на бота для додавання місць."""
    username = ADD_PLACE_BOT_USERNAME.lstrip("@")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.get(user_id or 0, 'go_to_bot', lang_code),
                              url=f"https://t.me/{username}")],
    ])


def search_keyboard(user_id: int = None, lang_code: str = None):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.get(user_id or 0, 'search_places', lang_code)),
             KeyboardButton(text=i18n.get(user_id or 0, 'search_favorites', lang_code))],
            [KeyboardButton(text=i18n.get(user_id or 0, 'search_by_name', lang_code))],
            # [KeyboardButton(text=i18n.get(user_id or 0, 'search_list', lang_code))],
            # [KeyboardButton(text=i18n.get(user_id or 0, 'search_random', lang_code))],
            
            [KeyboardButton(text=i18n.get(
                user_id or 0, 'menu_cancel', lang_code))],
        ],
        resize_keyboard=True
    )
    return keyboard


def random_choice_keyboard(user_id: int = None, lang_code: str = None):
    """Клавіатура вибору типу випадкового місця (з пошуку чи з улюблених)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.get(user_id or 0, 'random_from_search', lang_code)),
             KeyboardButton(text=i18n.get(user_id or 0, 'random_from_favorites', lang_code))],
            [KeyboardButton(text=i18n.get(
                user_id or 0, 'menu_cancel', lang_code))],
        ],
        resize_keyboard=True
    )



def error_action_keyboard(user_id: int = None, lang_code: str = None):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.get(user_id or 0, 'menu_back', lang_code)),
             KeyboardButton(text="🔄 " + i18n.get(user_id or 0, 'retry', lang_code))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def test_keyboard(user_id: int = None, lang_code: str = None):
    """Стартова клавіатура онбордингу: локація та місто в один ряд."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=i18n.get(user_id or 0, 'send_location', lang_code),
                    request_location=True,
                ),
                KeyboardButton(text=i18n.get(user_id or 0, 'find_city', lang_code)),
            ],
        ],
        resize_keyboard=True,
    )

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


def place_details_keyboard(place_url=None, google_maps_url=None, favorite_callback=None, is_favorite=False, user_id: int = None, lang_code: str = None):
    """
    Генерує клавіатуру для детального перегляду місця.
    """
    builder = InlineKeyboardBuilder()

    if place_url:
        builder.button(text="🌍 " + i18n.get(user_id or 0,
                       'official_website', lang_code), url=place_url)

    if google_maps_url:
        builder.button(text="📍 Map", url=google_maps_url)

    if favorite_callback:
        # Динамічно змінюємо напис кнопки залежно від is_favorite
        button_text = i18n.get(user_id or 0, 'remove_from_favorites', lang_code) if is_favorite else i18n.get(user_id or 0, 'add_to_favorites', lang_code)
        builder.button(
            text=button_text,
            callback_data=favorite_callback
        )

    return builder.as_markup()


def place_navigation_keyboard(user_id: int = None, lang_code: str = None):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.get(user_id or 0, 'menu_dislike', lang_code)),
             KeyboardButton(text=i18n.get(user_id or 0, 'menu_next', lang_code))],
            [KeyboardButton(text=i18n.get(
                user_id or 0, 'menu_stop', lang_code))],
        ],
        resize_keyboard=True
    )

    return keyboard


def favorites_action_keyboard(user_id: int = None, lang_code: str = None):
    """Клавіатура для вибору дії з улюбленими місцями."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=i18n.get(user_id or 0, 'favorites_view', lang_code)),
             KeyboardButton(text=i18n.get(user_id or 0, 'favorites_compare', lang_code))],
            [KeyboardButton(text=i18n.get(
                user_id or 0, 'menu_cancel', lang_code))],
        ],
        resize_keyboard=True
    )


def select_favorites_for_comparison_keyboard(favorites, selected_ids: list = None, user_id: int = None, lang_code: str = None):

    if selected_ids is None:
        selected_ids = []

    builder = InlineKeyboardBuilder()

    # Спочатку показуємо кнопку порівняння
    if len(selected_ids) >= 2:
        builder.button(
            text=i18n.get(user_id or 0, 'comparison_selected', lang_code),
            callback_data="perform_comparison"
        )
    else:
        builder.button(
            text=i18n.get(user_id or 0, 'comparison_select_min',
                          lang_code, count=len(selected_ids)),
            callback_data="comparison_help"
        )

    for favorite in favorites:
        place_id = favorite.get("id")
        name = favorite.get("name", i18n.get(
            user_id or 0, 'unnamed', lang_code) if lang_code else "Без назви")
        is_selected = place_id in selected_ids

        # Додаємо галочку якщо обрано
        checkbox = "✅" if is_selected else "⬜"
        display_name = f"{checkbox} {name}"

        builder.button(
            text=display_name,
            callback_data=f"compare_toggle:{place_id}"
        )

    builder.button(
        text=i18n.get(user_id or 0, 'menu_cancel', lang_code),
        callback_data="cancel_comparison"
    )

    builder.adjust(1)

    return builder.as_markup()
