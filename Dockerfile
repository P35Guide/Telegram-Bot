FROM python:3.11-slim

WORKDIR /app

# Копіюємо requirements (він у тебе в корені, це добре)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо все інше
COPY . .

# Вказуємо порт для Hugging Face
EXPOSE 7860

# ЗАПУСК: вказуємо шлях до main.py всередині папки bot
CMD ["python", "bot/main.py"]