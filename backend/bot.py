"""
Telegram Bot with Admin Panel
"""
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
import json
import os
from typing import Dict, List

from . import config

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# User statistics storage (use database in production)
user_stats = {
    "total_users": set(),
    "daily_users": {},
    "weekly_users": {},
    "monthly_users": {}
}

# Conversation states
(CHANNEL_TYPE, CHANNEL_VISIBILITY, CHANNEL_DATA, 
 BROADCAST_MESSAGE, EDIT_START_MESSAGE) = range(5)

# ==================== Helper Functions ====================

def save_config():
    """Save current config to config.py"""
    admin_ids_str = ", ".join(str(x) for x in config.ADMIN_IDS)
    
    config_content = f'''"""
Конфигурация бота и MiniApp
ВСЕ НАСТРОЙКИ ЗДЕСЬ!
"""

# ==================== БОТ ====================
# Токен бота от @BotFather
# Пример: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
# Получить: @BotFather → /mybots → выбери бота → API Token
BOT_TOKEN = "{config.BOT_TOKEN}"

# ==================== АДМИНЫ ====================
# Telegram ID админов (кто может использовать /adminpanel)
# Пример: [123456789, 987654321]
# Получить свой ID: @userinfobot → Start → скопируй число
ADMIN_IDS = [{admin_ids_str}]

# ==================== MINIAPP ====================
# URL где будет открываться MiniApp (кнопка "Забрать яйцо")
# Пример: "https://your-bot.bothost.tech/"
# Это адрес где будет хоститься твой проект
MINIAPP_URL = "{config.MINIAPP_URL}"

# ==================== СТАРТОВОЕ СООБЩЕНИЕ ====================
# Сообщение которое бот отправляет на /start
# Можно менять через /adminpanel в боте
START_MESSAGE = """{config.START_MESSAGE}"""

# ==================== СЕРВЕР ====================
# Не трогай эти настройки
API_HOST = "{config.API_HOST}"
API_PORT = {config.API_PORT}

# ==================== ТЕХНИЧЕСКИЕ НАСТРОЙКИ ====================
# Не трогай, всё работает правильно
TP_MODE = {config.TP_MODE}
BUTTON_COLOR = "{config.BUTTON_COLOR}"
BUTTON_COLOR_HEX = "{config.BUTTON_COLOR_HEX}"
APP_TITLE = "{config.APP_TITLE}"
APP_DESCRIPTION = "{config.APP_DESCRIPTION}"

# ==================== КАНАЛЫ ДЛЯ ПРОВЕРКИ ====================
# Список каналов на которые пользователь должен подписаться
# Можно управлять через /adminpanel в боте (добавлять/удалять)
# Можно добавлять вручную здесь в config.py
# 
# Формат канала:
# {{
#     "url": "https://t.me/твой_канал",              # Ссылка на канал
#     "name": "Название канала",                     # Как показать в MiniApp
#     "desc": "подписаться",                         # Текст на кнопке
#     "tp_bot_id": 162,                              # Не трогай
#     "tp_flow_id": 1,                               # Не трогай
#     "tp_resource_id": 1,                           # Уникальный номер (1, 2, 3...)
#     "tp_type": "channel",                          # channel, bot или chat
#     "tp_target_action": "subscribe",               # Не трогай
#     "tp_verification_mode": "verified",            # Не трогай
#     "require_verify": True,                        # Проверять подписку?
#     "chat_id": "@твой_канал"                       # Для публичных @username, для закрытых -100123...
# }}
CHANNELS = {repr(config.CHANNELS)}

# ==================== ПРОВЕРКА ПОДПИСОК ====================
# Какие каналы проверять (пустой список = все с require_verify: True)
VERIFY_RESOURCE_IDS = {config.VERIFY_RESOURCE_IDS}

# Режим проверки:
# "always_ok" - всегда успешно (для тестирования без настройки бота)
# "always_fail" - всегда неудача
# "real" - реальная проверка через Telegram Bot API (нужен BOT_TOKEN и бот должен быть админом канала)
VERIFY_FALLBACK = "{config.VERIFY_FALLBACK}"

# ==================== НАГРАДЫ ====================
# Не трогай, это для фронтенда
REWARD_REEL = {config.REWARD_REEL}
REWARD_FINAL = {config.REWARD_FINAL}
REWARD_LABEL = "{config.REWARD_LABEL}"

# ==================== ПОДЕЛИТЬСЯ ====================
# Текст для кнопки "Поделиться с друзьями"
SHARE_TEXT = "{config.SHARE_TEXT}"
SHARE_URL = "{config.SHARE_URL}"

# ==================== CORS (безопасность) ====================
# Домены которым разрешён доступ к API
# Добавь сюда свой домен для production
ALLOWED_ORIGINS = {config.ALLOWED_ORIGINS}
'''
    
    with open('config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)

def track_user(user_id: int):
    """Track user statistics"""
    today = datetime.now().date()
    week = today - timedelta(days=today.weekday())
    month = today.replace(day=1)
    
    user_stats["total_users"].add(user_id)
    
    if today not in user_stats["daily_users"]:
        user_stats["daily_users"][today] = set()
    user_stats["daily_users"][today].add(user_id)
    
    if week not in user_stats["weekly_users"]:
        user_stats["weekly_users"][week] = set()
    user_stats["weekly_users"][week].add(user_id)
    
    if month not in user_stats["monthly_users"]:
        user_stats["monthly_users"][month] = set()
    user_stats["monthly_users"][month].add(user_id)

def get_statistics() -> str:
    """Get formatted statistics"""
    today = datetime.now().date()
    week = today - timedelta(days=today.weekday())
    month = today.replace(day=1)
    
    daily = len(user_stats["daily_users"].get(today, set()))
    weekly = len(user_stats["weekly_users"].get(week, set()))
    monthly = len(user_stats["monthly_users"].get(month, set()))
    total = len(user_stats["total_users"])
    
    return f"""📊 **Статистика бота**

👥 Всего пользователей: {total}
📅 За сегодня: {daily}
📆 За неделю: {weekly}
🗓 За месяц: {monthly}
"""

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in config.ADMIN_IDS

# ==================== Command Handlers ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    track_user(user.id)
    
    # Create webapp button
    keyboard = [
        [InlineKeyboardButton(
            "🥚 Забрать яйцо",
            web_app=WebAppInfo(url=config.MINIAPP_URL)
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        config.START_MESSAGE,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /adminpanel command"""
    user = update.effective_user
    
    if not is_admin(user.id):
        await update.message.reply_text("❌ У вас нет доступа к админ панели.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("✏️ Изменить сообщение /start", callback_data="admin_edit_start")],
        [InlineKeyboardButton("➕ Добавить канал", callback_data="admin_add_channel")],
        [InlineKeyboardButton("➖ Удалить канал", callback_data="admin_remove_channel")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 **Админ панель**\n\nВыберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ==================== Admin Callback Handlers ====================

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.edit_message_text("❌ У вас нет доступа.")
        return
    
    data = query.data
    
    if data == "admin_stats":
        stats = get_statistics()
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(stats, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif data == "admin_edit_start":
        await query.edit_message_text(
            "📝 Отправьте новое сообщение для команды /start\n\n"
            "Текущее сообщение:\n\n" + config.START_MESSAGE + "\n\n"
            "Отправьте /cancel для отмены."
        )
        return EDIT_START_MESSAGE
    
    elif data == "admin_add_channel":
        keyboard = [
            [InlineKeyboardButton("📢 Канал", callback_data="add_channel_type_channel")],
            [InlineKeyboardButton("🤖 Бот", callback_data="add_channel_type_bot")],
            [InlineKeyboardButton("💬 Чат", callback_data="add_channel_type_chat")],
            [InlineKeyboardButton("◀️ Назад", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "➕ **Добавить ресурс**\n\nВыберите тип:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "admin_remove_channel":
        # Get fresh channels
        channels = config.get_channels()
        if not channels:
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Нет каналов для удаления",
                reply_markup=reply_markup
            )
            return
        
        keyboard = []
        for ch in channels:
            keyboard.append([InlineKeyboardButton(
                f"❌ {ch['name']} ({ch['tp_type']})",
                callback_data=f"remove_channel_{ch['tp_resource_id']}"
            )])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="admin_back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "➖ **Удалить канал**\n\nВыберите канал:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("remove_channel_"):
        resource_id = int(data.split("_")[2])
        # Get fresh channels and remove
        channels = config.get_channels()
        channels = [ch for ch in channels if ch['tp_resource_id'] != resource_id]
        config.save_channels(channels)
        
        await query.edit_message_text(
            "✅ Канал удален!\n\n"
            "Изменения применены автоматически! ✨"
        )
    
    elif data == "admin_broadcast":
        await query.edit_message_text(
            "📢 **Рассылка**\n\n"
            "Отправьте сообщение для рассылки всем пользователям.\n\n"
            "Отправьте /cancel для отмены."
        )
        return BROADCAST_MESSAGE
    
    elif data == "admin_back":
        keyboard = [
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("✏️ Изменить сообщение /start", callback_data="admin_edit_start")],
            [InlineKeyboardButton("➕ Добавить канал", callback_data="admin_add_channel")],
            [InlineKeyboardButton("➖ Удалить канал", callback_data="admin_remove_channel")],
            [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🔐 **Админ панель**\n\nВыберите действие:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data.startswith("add_channel_type_"):
        channel_type = data.split("_")[3]
        context.user_data['adding_channel'] = {'tp_type': channel_type}
        
        if channel_type == "channel":
            keyboard = [
                [InlineKeyboardButton("🔓 Открытый", callback_data="channel_visibility_public")],
                [InlineKeyboardButton("🔐 Закрытый", callback_data="channel_visibility_private")],
                [InlineKeyboardButton("📝 С заявками", callback_data="channel_visibility_request")],
                [InlineKeyboardButton("◀️ Назад", callback_data="admin_add_channel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "📢 **Добавить канал**\n\nВыберите тип канала:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                f"🤖 **Добавить {channel_type}**\n\n"
                "Отправьте данные в формате:\n"
                "Название\n"
                "Username (без @)\n"
                "URL\n\n"
                "Например:\n"
                "Мой бот\n"
                "my_bot\n"
                "https://t.me/my_bot\n\n"
                "Отправьте /cancel для отмены."
            )
            return CHANNEL_DATA
    
    elif data.startswith("channel_visibility_"):
        visibility = data.split("_")[2]
        context.user_data['adding_channel']['visibility'] = visibility
        
        if visibility == "public":
            instruction = "Отправьте данные в формате:\nНазвание\nUsername (без @)\nURL"
        elif visibility == "private":
            instruction = "Отправьте данные в формате:\nНазвание\nChat ID (например, -100123456789)\nURL"
        else:  # request
            instruction = "Отправьте данные в формате:\nНазвание\nChat ID или Username\nURL"
        
        await query.edit_message_text(
            f"📢 **Добавить канал ({visibility})**\n\n{instruction}\n\n"
            "Например:\n"
            "Мой канал\n"
            "@my_channel\n"
            "https://t.me/my_channel\n\n"
            "Отправьте /cancel для отмены."
        )
        return CHANNEL_DATA

async def receive_channel_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive channel data from user"""
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    lines = update.message.text.strip().split('\n')
    if len(lines) < 3:
        await update.message.reply_text(
            "❌ Неверный формат! Нужно 3 строки:\n"
            "1. Название\n"
            "2. Username или Chat ID\n"
            "3. URL"
        )
        return CHANNEL_DATA
    
    name = lines[0].strip()
    chat_id = lines[1].strip()
    url = lines[2].strip()
    
    channel_data = context.user_data.get('adding_channel', {})
    tp_type = channel_data.get('tp_type', 'channel')
    
    # Generate new resource_id from fresh channels
    channels = config.get_channels()
    existing_ids = [ch['tp_resource_id'] for ch in channels]
    new_id = max(existing_ids) + 1 if existing_ids else 1
    
    new_channel = {
        "url": url,
        "name": name,
        "desc": "подписаться" if tp_type == "channel" else "запустить бота",
        "tp_bot_id": 162,  # Фиксированное значение для фронтенда
        "tp_flow_id": 1,
        "tp_resource_id": new_id,
        "tp_type": tp_type,
        "tp_target_action": "subscribe" if tp_type == "channel" else "start_bot",
        "tp_verification_mode": "verified",
        "require_verify": True,
        "chat_id": chat_id
    }
    
    channels.append(new_channel)
    config.save_channels(channels)
    
    await update.message.reply_text(
        f"✅ Канал добавлен!\n\n"
        f"Название: {name}\n"
        f"ID: {new_id}\n"
        f"Тип: {tp_type}\n\n"
        "Изменения применены автоматически! ✨"
    )
    
    return ConversationHandler.END

async def receive_start_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive new start message"""
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    new_message = update.message.text.strip()
    config.START_MESSAGE = new_message
    save_config()
    
    # Test new message with button
    keyboard = [[InlineKeyboardButton("🥚 Забрать яйцо", web_app=WebAppInfo(url=config.MINIAPP_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✅ Сообщение обновлено!\n\nПредпросмотр:"
    )
    await update.message.reply_text(
        new_message,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    return ConversationHandler.END

async def receive_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive broadcast message"""
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    message = update.message.text
    users = list(user_stats["total_users"])
    
    await update.message.reply_text(f"📢 Начинаю рассылку для {len(users)} пользователей...")
    
    success = 0
    failed = 0
    
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message, parse_mode='HTML')
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to send to {user_id}: {e}")
    
    await update.message.reply_text(
        f"✅ Рассылка завершена!\n\n"
        f"Успешно: {success}\n"
        f"Ошибок: {failed}"
    )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text("❌ Операция отменена.")
    return ConversationHandler.END

# ==================== Main ====================

# Create application instance
if not config.BOT_TOKEN:
    logger.error("BOT_TOKEN not set in config.py!")
    application = None
else:
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("adminpanel", admin_panel))
    
    # Conversation handler for adding channel
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_callback)],
        states={
            CHANNEL_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel_data)],
            EDIT_START_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_start_message)],
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_broadcast_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(admin_callback))
    
    logger.info("Bot started!")
    logger.info(f"Admins: {config.ADMIN_IDS}")

def main():
    """Start the bot"""
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not set in config.py!")
        return
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
