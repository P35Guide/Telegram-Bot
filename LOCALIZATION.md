# 🌍 Система багатомовності Telegram-бота

## Підтримувані мови

Бот підтримує наступні мови:

- �🇧 **Англійська** (en) - *мова за замовчуванням*
- 🇺🇦 **Українська** (uk, ua) - *додаткова мова*
- 🇩🇪 **Німецька** (de)
- 🇫🇷 **Французька** (fr)
- 🇪🇸 **Іспанська** (es)
- 🇮🇹 **Італійська** (it)
- 🇵🇱 **Польська** (pl)
- 🇵🇹 **Португальська** (pt)
- 🇯🇵 **Японська** (ja)
- 🇨🇳 **Китайська** (zh)

## Коди мов

Бот підтримує наступні коди для вибору мови:

```
Language codes / Коди мов:
• en - English
• ua / uk - Українська / Ukrainian
• de - Deutsch / German
• fr - Français / French
• es - Español / Spanish
• it - Italiano / Italian
• pl - Polski / Polish
• pt - Português / Portuguese
• ja - 日本語 / Japanese
• zh - 中文 / Chinese
```

**Примітка:** Для української мови можна використовувати як `ua`, так і `uk` коди.

## Автоматичне визначення мови

### З мови Telegram
Бот **автоматично визначає мову** користувача з налаштувань Telegram (`user.language_code`):

```python
@router.message(CommandStart())
async def cmd_start(message: Message, session: aiohttp.ClientSession):
    user_id = message.from_user.id
    lang_code = message.from_user.language_code  # Отримуємо мову з Telegram
    
    # Система автоматично встановлює мову
    i18n.get_user_language(user_id, lang_code)
```

### Мапінг мов
Російська та білоруська мови **автоматично замінюються на англійську**:

```python
LANGUAGE_MAPPING = {
    'ru': 'en',  # Російська → Англійська
    'be': 'en',  # Білоруська → Англійська
}
```

Альтернативні коди мов також підтримуються:

```python
LANGUAGE_CODES = {
    'ua': 'uk',  # ua → uk (для з / Language
2. Виберіть потрібну мову зі списку (відображається список з прапорами)
3. Інтерфейс миттєво змінюється

### Підказки з кодами мов

При виборі мови користувач бачить підказки з кодами:

```
Language codes / Коди мов:
• en - English
• ua / uk - Українська / Ukrainian
• de - Deutsch / German
• fr - Français / French
...
```

Це допомагає користувачам зрозуміти, який код відповідає якій мові.
}
```en.json             # Англійська (за замовчуванням)
│   ├── uk.json             # Україн
## Ручна зміна мови

Користувачі можуть змінити мову в будь-який час через:

1. **Меню налаштувань** → 🌐 Мова
2. Виберіть потрібну мову зі списку
3. Інтерфейс миттєво змінюється

## Структура файлів

```
Telegram-Bot/
├── locales/                 # Папка з перекладами
│   ├── uk.json             # Українська
│   ├── en.json             # Англійська
│   ├── de.json             # Німецька
│   ├── fr.json             # Французька
│   ├── es.json             # Іспанська
│   ├── it.json             # Італійська
│   ├── pl.json             # Польська
│   ├── pt.json             # Португальська
│   ├── ja.json             # Японська
│   └── zh.json             # Китайська
│
├── bot/
│   ├── utils/
│   │   ├── localization.py  # Система локалізації
│   │   └── __init__.py      # Експорт i18n
│   │
│   ├── handlers/
│   │   ├── main_menu.py     # Оновлено для i18n
│   │   ├── settings.py      # Вибір мови
│   │   └── places.py        # Оновлюється...
│   │
│   ├── keyboards.py         # Багатомовні клавіатури
│   └── utils/
│       └── formatter.py     # Багатомовне форматування
```

## Використання в коді

### Простий переклад

```python
from bot.utils.localization import i18n

user_id = message.from_user.id
lang_code = message.from_user.language_code

# Отримати переклад
text = i18n.get(user_id, 'welcome', lang_code)
```

### Переклад з параметрами

```python
# У JSON файлі
{
  "city_found": "✅ Місто '{city}' знайдено!\\nТепер ви можете шукати місця поруч!"
}

# У коді
await message.answer(
    i18n.get(user_id, 'city_found', lang_code, city=text)
)
```

### Використання в клавіатурах

```python
def actions_keyboard(user_id: int = None, lang_code: str = None):
    return ReplyKeyboardMarkup(
        keyboard=[en.json` та перекладіть всі ключі

3. **Додайте мову** до `SUPPORTED_LANGUAGES` у `localization.py`:
   ```python
   SUPPORTED_LANGUAGES = {
       'en': '🇬🇧 English',  # Англійська має бути першою
       # ... інші мови
       'xx': '🏴 Назва мови',
   }
   ```

4. **Додайте код мови** до `LANGUAGE_CODES` (якщо потрібні альтернативні коди):
   ```python
   LANGUAGE_CODES = {
       'xx': 'xx',
       'alt': 'xx',  # Альтернативний код
   }
   ```

5. **Створіть новий JSON файл** у папці `locales/`:
   ```bash
   locales/xx.json  # де xx - код мови
   ```

2. **Скопіюйте структуру** з `uk.json` та перекладіть всі ключі

3. **Додайте мову** до `SUPPORTED_LANGUAGES` у `localization.py`:
   ```python
   SUPPORTED_LANGUAGES = {
       # ... інші мови
       'xx': '🏴 Назва мови',
   }
   ```

4. **Перезапустіть бота** - нова мова автоматично завантажиться!

## Додавання нових перекладів

1. **Додайте ключ** до всіх JSON файлів у `locales/`:
   ```json
   {
       "new_key": "Переклад цього ключа"
   }
   `Мова за замовчуванням**: Англійська (English)
- **Fallback**: Якщо переклад не знайдено, система використовує англійську мову
- **Кешування**: Мова користувача зберігається в пам'яті після першого визначення
- **Динамічна зміна**: Користувач може змінити мову в будь-який момент
- **Параметри**: Використовуйте `{parameter}` для динамічних значень
- **Альтернативні коди**: `ua` та `uk` обидва ведуть до української мови
- **Автозаміна**: Російська та білоруська автоматично замінюються на англійську
   i18n.get(user_id, 'new_key', lang_code)
   ```

## Гарячі поради

- **Fallback**: Якщо переклад не знайдено, система використовує українську мову
- **Кешування**: Мова користувача зберігається в пам'яті після першого визначення
- **Динамічна зміна**: Користувач може змінити мову в будь-який момент
- **Параметри**: Використовуйте `{parameter}` для динамічних значень

## Приклади використання

### У хендлері
```python
@router.message(F.location)
async def handle_location(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    user_id = message.from_user.id
    lang_code = message.from_user.language_code
    
    await message.answer(
        i18n.get(user_id, 'location_received', lang_code),
        reply_markup=actions_keyboard(user_id, lang_code),
    )
```

### З альтернативними кодами мов
```python
# Користувач може ввести як 'ua', так і 'uk'
user_input = "ua"  # або "uk"
if i18n.set_user_language(user_id, user_input):
    # Обидва коди призведуть до української мови
    lang = i18n.get_user_language(user_id)  # 'uk'
```

### Отримання підказок з кодами мов
```python
# Показати користувачу список кодів мов
hints = i18n.get_language_hints()
# Поверне форматований текст з усіма кодами та описами
```

### У форматуванні
```python
def format_place_text(p: dict, user_id: int = 0, lang_code: str = None) -> str:
    status_text = i18n.get(user_id, 'open_now', lang_code) if p.get('openNow') else i18n.get(user_id, 'closed_now', lang_code)
    
    distance_text = i18n.get(user_id, 'distance', lang_code, distance=distance_str)
    
    return f"{status_text}\\n{distance_text}"
```

## Підтримка

Якщо потрібно додати нову мову або виправити переклад:

1. Відкрийте відповідний файл у `locales/` (для нової мови - створіть новий файл)
2. Внесіть зміни або скопіюйте структуру з `en.json`
3. Додайте мову до `SUPPORTED_LANGUAGES` та `LANGUAGE_CODES` у `localization.py`
4. Збережіть файл
5. Перезапустіть бота

Система автоматично завантажить оновлені переклади!

## Особливості реалізації

### Пріоритет визначення мови

1. **Збережена мова користувача** (якщо раніше обирав вручну)
2. **Мова з Telegram** (автоматичне визначення)
3. **Англійська за замовчуванням** (якщо мова не підтримується)

### Мапінг кодів

```python
# Telegram може надіслати 'ua', але система використовує 'uk'
telegram_code = 'ua'
normalized = LANGUAGE_CODES.get('ua', 'ua')  # 'uk'

# Російська та білоруська замінюються на англійську
telegram_code = 'ru'
mapped = LANGUAGE_MAPPING.get('ru', 'ru')  # 'en'
```

---

**Розроблено з ❤️ для P35Guide**

*Default language: English 🇬🇧 | Мова за замовчуванням: Англійська*
