"""
Конфигурация бота и MiniApp
ВСЕ НАСТРОЙКИ ЗДЕСЬ!
"""
import json
import os

# ==================== БОТ ====================
# Токен бота от @BotFather
# Пример: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
# Получить: @BotFather → /mybots → выбери бота → API Token
BOT_TOKEN = "8918785448:AAFznBVvRdwAGCIgTWcmx5aH-fSXFwojE7M"

# ==================== АДМИНЫ ====================
# Telegram ID админов (кто может использовать /adminpanel)
# Пример: [123456789, 987654321]
# Получить свой ID: @userinfobot → Start → скопируй число
ADMIN_IDS = [192237320, 8764325618, 8307076618]

# ==================== MINIAPP ====================
# URL где будет открываться MiniApp (кнопка "Забрать яйцо")
# Пример: "https://your-bot.bothost.tech/"
# Это адрес где будет хоститься твой проект
MINIAPP_URL = "https://mybot45664.bothost.tech"

# ==================== СТАРТОВОЕ СООБЩЕНИЕ ====================
# Сообщение которое бот отправляет на /start
# Можно менять через /adminpanel в боте
START_MESSAGE = """EN: Welcome!  
In this bot, you can claim secret Brainrot Eggs or NEW MONSTER EGGS in STEAL AN EGG mode! 🥚✨  
━━━━━━━━━━━━━  
RU: Привет!  
В этом боте вы можете забрать секретные яйца Brainrot или НОВЫЕ МОНСТР ЯЙЦА в режиме «УКРАДИ ЯЙЦО»! 🥚✨"""

# ==================== СЕРВЕР ====================
# Не трогай эти настройки
API_HOST = "0.0.0.0"
API_PORT = 8000

# ==================== ТЕХНИЧЕСКИЕ НАСТРОЙКИ ====================
# Не трогай, всё работает правильно
TP_MODE = True
BUTTON_COLOR = "primary"
BUTTON_COLOR_HEX = "#3390ec"
APP_TITLE = "Stael an Eggs"
APP_DESCRIPTION = "Open eggs and win prizes!"

# ==================== КАНАЛЫ ДЛЯ ПРОВЕРКИ ====================
# Каналы теперь хранятся в channels.json и загружаются динамически
# Управлять через /adminpanel в боте (добавлять/удалять) - БЕЗ ПЕРЕЗАПУСКА!
# Или редактируй channels.json вручную

# Путь к файлу с каналами (абсолютный путь)
CHANNELS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "channels.json")

def load_channels():
    """Load channels from JSON file"""
    try:
        if os.path.exists(CHANNELS_FILE):
            with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
                channels = json.load(f)
                print(f"✅ Loaded {len(channels)} channels from {CHANNELS_FILE}")
                return channels
        else:
            print(f"⚠️ Channels file not found: {CHANNELS_FILE}, using defaults")
    except Exception as e:
        print(f"❌ Error loading channels: {e}")
    
    # Default channels if file doesn't exist
    default_channels = [
        {
            "url": "https://t.me/your_channel_1",
            "name": "Главный канал",
            "desc": "подписаться",
            "tp_bot_id": 162,
            "tp_flow_id": 1,
            "tp_resource_id": 1,
            "tp_type": "channel",
            "tp_target_action": "subscribe",
            "tp_verification_mode": "verified",
            "require_verify": True,
            "chat_id": "@your_channel_1"
        },
        {
            "url": "https://t.me/your_channel_2",
            "name": "Новости и обновления",
            "desc": "подписаться",
            "tp_bot_id": 162,
            "tp_flow_id": 1,
            "tp_resource_id": 2,
            "tp_type": "channel",
            "tp_target_action": "subscribe",
            "tp_verification_mode": "verified",
            "require_verify": True,
            "chat_id": "@your_channel_2"
        },
        {
            "url": "https://t.me/your_channel_3",
            "name": "Розыгрыши",
            "desc": "подписаться",
            "tp_bot_id": 162,
            "tp_flow_id": 1,
            "tp_resource_id": 3,
            "tp_type": "channel",
            "tp_target_action": "subscribe",
            "tp_verification_mode": "verified",
            "require_verify": True,
            "chat_id": "@your_channel_3"
        },
        {
            "url": "https://t.me/your_bot",
            "name": "Бот поддержки",
            "desc": "запустить бота",
            "tp_bot_id": 162,
            "tp_flow_id": 1,
            "tp_resource_id": 4,
            "tp_type": "bot",
            "tp_target_action": "start_bot",
            "tp_verification_mode": "verified",
            "require_verify": False,
            "chat_id": "@your_bot"
        }
    ]
    
    # Save defaults to file for first time
    save_channels(default_channels)
    return default_channels

def save_channels(channels_list):
    """Save channels to JSON file"""
    try:
        print(f"💾 Saving {len(channels_list)} channels to {CHANNELS_FILE}")
        with open(CHANNELS_FILE, 'w', encoding='utf-8') as f:
            json.dump(channels_list, f, ensure_ascii=False, indent=2)
        print(f"✅ Channels saved successfully!")
        return True
    except Exception as e:
        print(f"❌ Error saving channels: {e}")
        return False

def get_channels():
    """Get current channels (always fresh from file)"""
    return load_channels()

# Load channels on startup
CHANNELS = load_channels()

# ==================== ПРОВЕРКА ПОДПИСОК ====================
# Какие каналы проверять (пустой список = все с require_verify: True)
VERIFY_RESOURCE_IDS = []

# Режим проверки:
# "always_ok" - всегда успешно (для тестирования без настройки бота)
# "always_fail" - всегда неудача
# "real" - реальная проверка через Telegram Bot API (нужен BOT_TOKEN и бот должен быть админом канала)
VERIFY_FALLBACK = "real"

# ==================== НАГРАДЫ ====================
# Не трогай, это для фронтенда
REWARD_REEL = [30, 50, 100, 200]
REWARD_FINAL = 50
REWARD_LABEL = "Robux"

# ==================== ПОДЕЛИТЬСЯ ====================
# Текст для кнопки "Поделиться с друзьями"
SHARE_TEXT = "Я открыл яйцо и выиграл приз! Попробуй и ты!"
SHARE_URL = "https://t.me/your_bot/app"

# ==================== CORS (безопасность) ====================
# Домены которым разрешён доступ к API
# Добавь сюда свой домен для production
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
