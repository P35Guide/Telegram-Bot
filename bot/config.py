import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL")
PHOTO_MAX_HEIGHT = 1500
PHOTO_MAX_WIDTH = 1500
