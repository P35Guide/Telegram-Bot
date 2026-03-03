from math import radians, sin, cos, sqrt, atan2
from bot.utils.localization import i18n

# Ці константи більше не використовуються напряму, але залишаємо для сумісності
PRICE_LEVELS = {
    "PRICE_LEVEL_UNSPECIFIED": "",
    "PRICE_LEVEL_FREE": "Безкоштовно",
    "PRICE_LEVEL_INEXPENSIVE": "💰",
    "PRICE_LEVEL_MODERATE": "💰💰",
    "PRICE_LEVEL_EXPENSIVE": "💰💰💰",
    "PRICE_LEVEL_VERY_EXPENSIVE": "💰💰💰💰"
}


def get_price_level_text(price_level: str, user_id: int = 0, lang_code: str = None) -> str:
    """Отримати переклад рівня ціни"""
    price_map = {
        "PRICE_LEVEL_FREE": i18n.get(user_id, 'price_free', lang_code),
        "PRICE_LEVEL_INEXPENSIVE": i18n.get(user_id, 'price_inexpensive', lang_code),
        "PRICE_LEVEL_MODERATE": i18n.get(user_id, 'price_moderate', lang_code),
        "PRICE_LEVEL_EXPENSIVE": i18n.get(user_id, 'price_expensive', lang_code),
        "PRICE_LEVEL_VERY_EXPENSIVE": i18n.get(user_id, 'price_very_expensive', lang_code),
    }
    return price_map.get(price_level, "")


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Розраховує відстань між двома координатами в км (формула Гаверсина)"""
    R = 6371  # Радіус Землі в км
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    
    return distance


def format_distance(distance_km: float) -> str:
    """Форматує відстань у зручний вигляд"""
    if distance_km < 1:
        return f"{int(distance_km * 1000)} м"
    else:
        return f"{distance_km:.1f} км"


def format_place_text(p: dict, user_coords: dict = None, user_id: int = 0, lang_code: str = None) -> str:
    """Форматує деталі місця у html рядок"""

    # хедер
    title = f"🏢 <b>{p.get('displayName') or p.get('name')}</b>"
    category = f"🏷 <i>{p.get('primaryType', '').replace('_', ' ').title()}</i>" if p.get(
        'primaryType') else None

    # Рейтинг та ціна
    rating_line = None
    if p.get('rating'):
        stars = "⭐" * int(round(p.get('rating', 0)))
        rating_line = f"{stars} <b>{p.get('rating')}</b> ({p.get('userRatingCount')} відгуків)"

        price_level = p.get('priceLevel')
        if price_level:
            price_symbol = get_price_level_text(price_level, user_id, lang_code)
            if price_symbol:
                rating_line += f" • {price_symbol}"

    # Статус
    status = None
    if p.get('openNow') is not None:
        status_text = i18n.get(user_id, 'open_now', lang_code) if p.get('openNow') else i18n.get(user_id, 'closed_now', lang_code)
        status = status_text

        # Графік роботи
        schedule = p.get('weekdayDescriptions', [])
        if schedule:
            schedule_text = "\n".join([f"▫️ {day}" for day in schedule])
            status += f"\n\n{i18n.get(user_id, 'schedule_title', lang_code)}\n{schedule_text}"

    # Адреса, телефон та вебсайт
    address = f"📍 {p.get('shortFormattedAddress')}" if p.get(
        'shortFormattedAddress') else None
    
    # Розраховуємо відстань, якщо є координати користувача
    distance_text = None
    if user_coords and user_coords.get('latitude') and user_coords.get('longitude'):
        if p.get('latitude') and p.get('longitude'):
            distance_km = calculate_distance(
                user_coords['latitude'], user_coords['longitude'],
                p['latitude'], p['longitude']
            )
            distance_str = format_distance(distance_km)
            distance_text = i18n.get(user_id, 'distance', lang_code, distance=distance_str)
    
    phone = f"📞 {p.get('phoneNumber')}" if p.get('phoneNumber') else None
    website = f"🌐 <a href='{p.get('websiteUri')}'>{i18n.get(user_id, 'official_website', lang_code)}</a>" if p.get(
        'websiteUri') else None

    # Опис
    description = None
    summary = p.get('editorialSummary') or p.get('generativeSummary')
    if summary:
        description = f"{i18n.get(user_id, 'about_place', lang_code)}\n<i>{summary}</i>"

    # Відділювач
    sep = "──────────────"

    lines = [
        title,
        category,
        sep,
        rating_line,
        status,
        "",
        address,
        distance_text,
        phone,
        website,
        "",
        description
    ]
    return "\n".join(line for line in lines if line is not None)
