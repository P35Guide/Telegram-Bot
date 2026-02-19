PRICE_LEVELS = {
    "PRICE_LEVEL_UNSPECIFIED": "",
    "PRICE_LEVEL_FREE": "Безкоштовно",
    "PRICE_LEVEL_INEXPENSIVE": "💰",
    "PRICE_LEVEL_MODERATE": "💰💰",
    "PRICE_LEVEL_EXPENSIVE": "💰💰💰",
    "PRICE_LEVEL_VERY_EXPENSIVE": "💰💰💰💰"
}


def format_place_text(p: dict) -> str:
    """Форматує деталі місця у html рядок"""
    
    # хедер
    title = f"🏢 <b>{p.get('DisplayName') or p.get('Name')}</b>"
    category = f"🏷 <i>{p.get('PrimaryType', '').replace('_', ' ').title()}</i>" if p.get('PrimaryType') else None
    
    # Рейтинг та ціна
    rating_line = None
    if p.get('Rating'):
        stars = "⭐" * int(round(p.get('Rating', 0)))
        rating_line = f"{stars} <b>{p.get('Rating')}</b> ({p.get('UserRatingCount')} відгуків)"
        
        price_level = p.get('PriceLevel')
        if price_level:
            # Спробуємо отримати символ з мапи, або виведемо як є, якщо не знайдено
            price_symbol = PRICE_LEVELS.get(price_level, price_level)
            if price_symbol:
                rating_line += f" • {price_symbol}"

    # Статус
    status = None
    if p.get('OpenNow') is not None:
        status = "🟢 <b>Відчинено</b>" if p.get('OpenNow') else "🔴 <b>Зачинено</b>"
        
        # Графік роботи
        schedule = p.get('WeekdayDescriptions', [])
        if schedule:
            schedule_text = "\n".join([f"▫️ {day}" for day in schedule])
            status += f"\n\n🕒 <b>Графік роботи:</b>\n{schedule_text}"

    # Адреса, телефон та вебсайт
    address = f"📍 {p.get('ShortFormattedAddress')}" if p.get('ShortFormattedAddress') else None
    phone = f"📞 {p.get('PhoneNumber')}" if p.get('PhoneNumber') else None
    website = f"🌐 <a href='{p.get('WebsiteUri')}'>Офіційний сайт</a>" if p.get('WebsiteUri') else None

    # Опис
    description = None
    summary = p.get('EditorialSummary') or p.get('GenerativeSummary')
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
        phone,
        website,
        "",
        description
    ]
    return "\n".join(line for line in lines if line is not None)
