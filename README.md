# P35Guide Telegram Bot

Простий Telegram бот для пошуку місць поруч (ресторани, кафе, лікарні тощо) з
використанням P35Guide API

## 🚀 Встановлення та запуск

### 1. Клонуйте репозиторій

```bash
git clone https://github.com/P35Guide/Telegram-Bot
cd Telegram-Bot
```

### 2. Створіть віртуальне середовище (рекомендовано)

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Встановіть залежності

```bash
pip install -r requirements.txt
```

### 4. Налаштуйте змінні оточення

Створіть файл `.env` у корені проекту (скопіюйте `.env.example`):

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Відкрийте файл `.env` та додайте свій токен бота:

```ini
BOT_TOKEN=your_bot_token_here
API_BASE_URL=http://localhost:5000
ADD_PLACE_BOT_USERNAME=@YourAddPlaceBot
```

**Як отримати BOT_TOKEN:**
1. Відкрийте Telegram і знайдіть [@BotFather](https://t.me/botfather)
2. Відправте команду `/newbot`
3. Слідуйте інструкціям для створення бота
4. Скопіюйте отриманий токен у файл `.env`

### 5. Запустіть бота

```bash
python main.py
```

## 🛠 Функціонал

- 📍 Пошук місць за геолокацією
- ⚙️ Налаштування радіусу пошуку та мови
- 🏷 Фільтрація за типами (включення/виключення)
- ⭐ Сортування за популярністю або відстанню
- 🗺 Перегляд деталей місця та побудова маршруту
