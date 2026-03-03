from math import radians, sin, cos, sqrt, atan2

PRICE_LEVELS = {
    "PRICE_LEVEL_UNSPECIFIED": "",
    "PRICE_LEVEL_FREE": "Безкоштовно",
    "PRICE_LEVEL_INEXPENSIVE": "💰",
    "PRICE_LEVEL_MODERATE": "💰💰",
    "PRICE_LEVEL_EXPENSIVE": "💰💰💰",
    "PRICE_LEVEL_VERY_EXPENSIVE": "💰💰💰💰"
}


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


def format_place_text(p: dict, user_coords: dict = None) -> str:
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
            # Спробуємо отримати символ з мапи, або виведемо як є, якщо не знайдено
            price_symbol = PRICE_LEVELS.get(price_level, price_level)
            if price_symbol:
                rating_line += f" • {price_symbol}"

    # Статус
    status = None
    if p.get('openNow') is not None:
        status = "🟢 <b>Відчинено</b>" if p.get(
            'openNow') else "🔴 <b>Зачинено</b>"

        # Графік роботи
        schedule = p.get('weekdayDescriptions', [])
        if schedule:
            schedule_text = "\n".join([f"▫️ {day}" for day in schedule])
            status += f"\n\n🕒 <b>Графік роботи:</b>\n{schedule_text}"

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
            distance_text = f"📏 Відстань: <b>{distance_str}</b>"
    
    phone = f"📞 {p.get('phoneNumber')}" if p.get('phoneNumber') else None
    website = f"🌐 <a href='{p.get('websiteUri')}'>Офіційний сайт</a>" if p.get(
        'websiteUri') else None

    # Опис
    description = None
    summary = p.get('editorialSummary') or p.get('generativeSummary')
    if summary:
        description = f"📝 <b>Про місце:</b>\n<i>{summary}</i>"

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


def format_comparison_text(places: list, user_coords: dict = None) -> str:
    """
    Форматує порівняння кількох місць у HTML рядок з таблицею.
    Порівнює за: кількість відгуків, рейтингом (зірки), відстанню.
    Показує позначки для найкращих та найгірших.
    """
    if not places or len(places) < 2:
        return "❌ Потрібно вибрати мінімум 2 місця для порівняння."
    
    # Заголовок
    header = "⚖️ <b>Порівняння закладів</b>\n"
    
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
            data["distance_str"] = format_distance(distance_km)
        else:
            data["distance_km"] = float('inf')
            data["distance_str"] = "Невідомо"
        
        comparison_data.append(data)
    
    # Знаходимо найкращих і найгірших за кожним параметром
    # Рейтинг (фільтруємо місця з рейтингом > 0)
    places_with_rating = [p for p in comparison_data if p["rating"] > 0]
    best_rating = max(places_with_rating, key=lambda x: x["rating"]) if places_with_rating else None
    worst_rating = min(places_with_rating, key=lambda x: x["rating"]) if places_with_rating else None
    
    # Відгуки (фільтруємо місця з відгуками > 0)
    places_with_reviews = [p for p in comparison_data if p["reviews_count"] > 0]
    most_reviews = max(places_with_reviews, key=lambda x: x["reviews_count"]) if places_with_reviews else None
    least_reviews = min(places_with_reviews, key=lambda x: x["reviews_count"]) if places_with_reviews else None
    
    # Відстань (фільтруємо місця з відомою відстанню)
    places_with_distance = [p for p in comparison_data if p["distance_km"] != float('inf')]
    closest = min(places_with_distance, key=lambda x: x["distance_km"]) if places_with_distance else None
    farthest = max(places_with_distance, key=lambda x: x["distance_km"]) if places_with_distance else None
    
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
                    rating_text += " <b>✅ (НАЙЛІПШИЙ)</b>"
                elif data == worst_rating and data != best_rating:
                    rating_text += " <b>❌ (НАЙГІРШИЙ)</b>"
        else:
            rating_text = "<i>Немає оцінок</i> ❌"
        
        lines.append(f"⭐ Рейтинг: {rating_text}")
        
        # Кількість відгуків
        reviews_marker = ""
        if most_reviews and least_reviews:
            if data == most_reviews and data != least_reviews:
                reviews_marker = " <b>✅ (НАЙБІЛЬШЕ)</b>"
            elif data == least_reviews and data != most_reviews:
                reviews_marker = " <b>❌ (НАЙМЕНШЕ)</b>"
        
        lines.append(f"💬 Відгуків: <b>{data['reviews_count']}</b>{reviews_marker}")
        
        # Відстань
        distance_marker = ""
        if data['distance_km'] != float('inf') and closest and farthest:
            if data == closest and data != farthest:
                distance_marker = " <b>✅ (НАЙБЛИЖЧЕ)</b>"
            elif data == farthest and data != closest:
                distance_marker = " <b>❌ (НАЙДАЛІ)</b>"
        
        lines.append(f"📏 Відстань: <b>{data['distance_str']}</b>{distance_marker}")
        
        # Статус
        if data['open_now'] is not None:
            status = "🟢 Відчинено" if data['open_now'] else "🔴 Зачинено"
            lines.append(f"🕒 Статус: {status}")
        
        # Ціна
        if data['price_level']:
            price_symbol = PRICE_LEVELS.get(data['price_level'], data['price_level'])
            if price_symbol:
                lines.append(f"💰 Ціна: {price_symbol}")
    
    # Рекомендація
    
    lines.append("<b>💡 ПОРІВНЯННЯ:</b>\n")
    
    # Найкращий за рейтингом
    if best_rating:
        lines.append(f"⭐ За рейтингом ЛІДЕР: <b>{best_rating['name']}</b> ({best_rating['rating']})")
    
    # Найближче
    if closest and closest['distance_km'] != float('inf'):
        lines.append(f"📍 Найближче до вас: <b>{closest['name']}</b> ({closest['distance_str']})")
    
    # Найбільше відгуків
    if most_reviews:
        lines.append(f"💬 Найбільше відгуків: <b>{most_reviews['name']}</b> ({most_reviews['reviews_count']})")
    
    return "\n".join(lines)
