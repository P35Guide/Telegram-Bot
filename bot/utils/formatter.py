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
    """Calculates distance between two coordinates in km (Haversine formula)"""
    R = 6371  # Earth radius in km

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance


def format_distance(distance_km: float, user_id: int = 0, lang_code: str = None) -> str:
    """Formats distance in readable format"""
    if distance_km < 1:
        meters = int(distance_km * 1000)
        return f"{meters} м" if lang_code in ['uk', 'ru'] else f"{meters} m"
    else:
        km_str = "км" if lang_code in ['uk', 'ru'] else "km"
        return f"{distance_km:.1f} {km_str}"


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
        reviews_text = i18n.get(user_id, 'reviews_count',
                                lang_code, count=format_int_with_spaces(p.get('userRatingCount', 0)))
        rating_line = f"{stars} <b>{p.get('rating')}</b> ({reviews_text})"

        price_level = p.get('priceLevel')
        if price_level:
            price_symbol = get_price_level_text(
                price_level, user_id, lang_code)
            if price_symbol:
                rating_line += f" • {price_symbol}"

    # Статус
    status = None
    if p.get('openNow') is not None:
        status_text = i18n.get(user_id, 'open_now', lang_code) if p.get(
            'openNow') else i18n.get(user_id, 'closed_now', lang_code)
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
            distance_str = format_distance(distance_km, user_id, lang_code)
            distance_text = i18n.get(
                user_id, 'distance', lang_code, distance=distance_str)

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


def format_int_with_spaces(n: int, separator: str = " ") -> str:
    number_str = str(n)
    result = ""
    count = 0

    for c in reversed(number_str):
        if count == 3:
            result = separator + result
            count = 0
        result = c + result
        count += 1

    return result


def format_comparison_text(places: list, user_coords: dict = None, user_id: int = 0, lang_code: str = None) -> str:

    if not places or len(places) < 2:
        return i18n.get(user_id, 'comparison_min_2', lang_code)

    # Заголовок
    header = i18n.get(user_id, 'comparison_header', lang_code) + "\n"

    # Збираємо дані для порівняння
    comparison_data = []
    for place in places:
        data = {
            "name": place.get("displayName") or place.get("name", "Без назви"),
            "rating": place.get("rating") or 0,
            "user_rating_count": place.get("userRatingCount") or 0,
            "reviews_count": place.get("reviewCount") or place.get("userRatingCount") or 0,
            "latitude": place.get("latitude"),
            "longitude": place.get("longitude"),
            "phone": place.get("phoneNumber"),
            "address": place.get("shortFormattedAddress"),
            "price_level": place.get("priceLevel"),
            "open_now": place.get("openNow"),
        }

        # Розраховуємо відстань
        if user_coords and data["latitude"] and data["longitude"]:
            distance_km = calculate_distance(
                user_coords.get("latitude", 0),
                user_coords.get("longitude", 0),
                data["latitude"],
                data["longitude"]
            )
            data["distance_km"] = distance_km
            data["distance_str"] = format_distance(
                distance_km, user_id, lang_code)
        else:
            data["distance_km"] = float('inf')
            data["distance_str"] = i18n.get(
                user_id, 'unknown_distance', lang_code)

        comparison_data.append(data)

    # Знаходимо найкращих і найгірших за кожним параметром
    # Рейтинг (фільтруємо місця з рейтингом > 0)
    places_with_rating = [p for p in comparison_data if p["rating"] > 0]
    best_rating = max(places_with_rating,
                      key=lambda x: x["rating"]) if places_with_rating else None
    worst_rating = min(
        places_with_rating, key=lambda x: x["rating"]) if places_with_rating else None

    # Відгуки (фільтруємо місця з відгуками > 0)
    places_with_reviews = [
        p for p in comparison_data if p["reviews_count"] > 0]
    most_reviews = max(
        places_with_reviews, key=lambda x: x["reviews_count"]) if places_with_reviews else None
    least_reviews = min(
        places_with_reviews, key=lambda x: x["reviews_count"]) if places_with_reviews else None

    # Відстань (фільтруємо місця з відомою відстанню)
    places_with_distance = [
        p for p in comparison_data if p["distance_km"] != float('inf')]
    closest = min(places_with_distance,
                  key=lambda x: x["distance_km"]) if places_with_distance else None
    farthest = max(places_with_distance,
                   key=lambda x: x["distance_km"]) if places_with_distance else None

    # Формуємо порівняльну таблицю
    lines = [header]

    # Таблиця порівняння
    for i, data in enumerate(comparison_data, 1):
        lines.append(f"\n<b>#{i} {data['name']}</b>")

        # Рейтинг
        rating_text = ""
        if data['rating'] > 0:
            stars = "⭐" * int(round(data['rating']))
            rating_text = f"<b>{data['rating']}</b> {stars}"

            # Позначаємо найкращий та найгірший за рейтингом
            if best_rating and worst_rating:
                if data == best_rating and data != worst_rating:
                    rating_text += f" <b>✅ ({i18n.get(user_id, 'rating_best', lang_code)})</b>"
                elif data == worst_rating and data != best_rating:
                    rating_text += f" <b>❌ ({i18n.get(user_id, 'rating_worst', lang_code)})</b>"
        else:
            rating_text = f"<i>{i18n.get(user_id, 'no_ratings', lang_code)}</i> ❌"

        lines.append(
            f"⭐ {i18n.get(user_id, 'rating_label', lang_code)}: {rating_text}")

        # Кількість відгуків
        reviews_marker = ""
        if most_reviews and least_reviews:
            if data == most_reviews and data != least_reviews:
                reviews_marker = f" <b>✅ ({i18n.get(user_id, 'reviews_most', lang_code)})</b>"
            elif data == least_reviews and data != most_reviews:
                reviews_marker = f" <b>❌ ({i18n.get(user_id, 'reviews_least', lang_code)})</b>"

        lines.append(
            f"💬 {i18n.get(user_id, 'reviews_label', lang_code)}: <b>{format_int_with_spaces(data['reviews_count'])}</b>{reviews_marker}")

        # Відстань
        distance_marker = ""
        if data['distance_km'] != float('inf') and closest and farthest:
            if data == closest and data != farthest:
                distance_marker = f" <b>✅ ({i18n.get(user_id, 'distance_closest', lang_code)})</b>"
            elif data == farthest and data != closest:
                distance_marker = f" <b>❌ ({i18n.get(user_id, 'distance_farthest', lang_code)})</b>"

        lines.append(
            f"📏 {i18n.get(user_id, 'distance_label', lang_code)}: <b>{data['distance_str']}</b>{distance_marker}")

        # Статус
        if data['open_now'] is not None:
            if data['open_now']:
                status = f"🟢 {i18n.get(user_id, 'status_open', lang_code)}"
            else:
                status = f"🔴 {i18n.get(user_id, 'status_closed', lang_code)}"
            lines.append(
                f"🕒 {i18n.get(user_id, 'status_label', lang_code)}: {status}")

        # Ціна
        if data['price_level']:
            price_symbol = get_price_level_text(
                data['price_level'], user_id, lang_code)
            if price_symbol:
                lines.append(
                    f"💰 {i18n.get(user_id, 'price_label', lang_code)}: {price_symbol}")

    # Рекомендація

    lines.append(
        f"<b>💡 {i18n.get(user_id, 'comparison_summary', lang_code)}:</b>\n")

    # Найкращий за рейтингом
    if best_rating:
        lines.append(
            f"⭐ {i18n.get(user_id, 'rating_leader', lang_code)}: <b>{best_rating['name']}</b> ({best_rating['rating']})")

    # Найближче
    if closest and closest['distance_km'] != float('inf'):
        lines.append(
            f"📍 {i18n.get(user_id, 'closest_to_you', lang_code)}: <b>{closest['name']}</b> ({closest['distance_str']})")

    # Найбільше відгуків
    if most_reviews:
        lines.append(
            f"💬 {i18n.get(user_id, 'most_reviews', lang_code)}: <b>{most_reviews['name']}</b> ({format_int_with_spaces(most_reviews['reviews_count'])})")

    return "\n".join(lines)
