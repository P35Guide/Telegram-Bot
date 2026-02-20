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
        phone,
        website,
        "",
        description
    ]
    return "\n".join(line for line in lines if line is not None)
