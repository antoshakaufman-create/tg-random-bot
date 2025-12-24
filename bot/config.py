import os
from dotenv import load_dotenv

load_dotenv()

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Channel configuration
EXEED_CHANNEL_ID = os.getenv("EXEED_CHANNEL_ID", "@exeed_russia")
LUZHNIKI_CHANNEL_ID = os.getenv("LUZHNIKI_CHANNEL_ID", "@luzhniki")
EXEED_CHANNEL_URL = os.getenv("EXEED_CHANNEL_URL", "https://t.me/exeed_russia")
LUZHNIKI_CHANNEL_URL = os.getenv("LUZHNIKI_CHANNEL_URL", "https://t.me/luzhniki")
STORAGE_CHANNEL_ID = os.getenv("STORAGE_CHANNEL_ID", "")

# Randomizer settings (2 days, ~6000 visitors per day)
DAILY_SMALL_PRIZES = int(os.getenv("DAILY_SMALL_PRIZES", "100"))  # маленькие подарки
DAILY_BIG_PRIZES = int(os.getenv("DAILY_BIG_PRIZES", "5"))        # большие подарки
DAILY_VISITORS = int(os.getenv("DAILY_VISITORS", "6000"))

# Prize lists
SMALL_PRIZE_LIST = os.getenv("SMALL_PRIZE_LIST", "Брелок EXEED,Значок,Стикерпак,Ручка,Магнит").split(",")
BIG_PRIZE_LIST = os.getenv("BIG_PRIZE_LIST", "Термокружка,Шарф,Шапка,Перчатки,Плед").split(",")

# Paths
PHOTOS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "photos")
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")
