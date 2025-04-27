from dotenv import load_dotenv
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler,
    Application
)
from pathlib import Path
import os
import asyncio
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / '.env')

API_URL = os.getenv('API_URL')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 60))  # Default to 60 seconds

# Menu definitions
MAIN_MENU = ReplyKeyboardMarkup([
    ['➕ New Reminder', '📋 List of Reminders'],
    ['❌ Delete Reminder', '⚙ Settings']
], resize_keyboard=True)

SETTINGS_MENU = ReplyKeyboardMarkup([
    ['🕒 Toggle Time Format (12h/24h)'],
    ['↩️ Back to Main Menu']
], resize_keyboard=True)

# Conversation states
STATE_NEW_REMINDER_TEXT, STATE_NEW_REMINDER_TIME, STATE_DELETE_REMINDER, STATE_SETTINGS = range(4)

# Temporary storage for conversation data
user_data_temp = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    response = requests.post(f"{API_URL}register/", json={
        "telegram_id": telegram_id,
        "name": update.effective_user.first_name
    })
    await update.message.reply_text("Hello! I'm your organizer 📒", reply_markup=MAIN_MENU)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == '➕ New Reminder':
        await update.message.reply_text("Enter the reminder text:")
        return STATE_NEW_REMINDER_TEXT

    if text == '📋 List of Reminders':
        await show_reminders(update)

    if text == '❌ Delete Reminder':
        await show_reminders(update)
        await update.message.reply_text("Enter the ID of the reminder you want to delete:")
        return STATE_DELETE_REMINDER

    if text == '⚙ Settings':
        await update.message.reply_text("Settings:", reply_markup=SETTINGS_MENU)
        return STATE_SETTINGS

async def new_reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp['text'] = update.message.text
    await update.message.reply_text("When should I remind you? (format: 2025-04-30 14:30)")
    return STATE_NEW_REMINDER_TIME

async def new_reminder_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_temp['remind_at'] = update.message.text
    telegram_id = update.effective_user.id

    response = requests.post(f"{API_URL}reminders/create/", json={
        "telegram_id": telegram_id,
        "text": user_data_temp['text'],
        "remind_at": user_data_temp['remind_at']
    })

    await update.message.reply_text("✅ Reminder saved!", reply_markup=MAIN_MENU)
    return ConversationHandler.END

async def show_reminders(update: Update):
    telegram_id = update.effective_user.id
    response = requests.get(f"{API_URL}reminders/{telegram_id}/")

    if response.status_code == 200:
        reminders = response.json()
        if reminders:
            msg = "\n\n".join([f"{r['id']}: {r['text']} (at {r['remind_at']})" for r in reminders])
            await update.message.reply_text(f"Your reminders:\n\n{msg}")
        else:
            await update.message.reply_text("You have no active reminders.")
    else:
        await update.message.reply_text("Error retrieving the list of reminders.")

async def delete_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reminder_id = update.message.text
    telegram_id = update.effective_user.id
        
    if not reminder_id.isdigit():
        await update.message.reply_text("❌ Invalid ID. Please enter a valid reminder ID (numeric).")
        return STATE_DELETE_REMINDER
    
    response = requests.delete(f"{API_URL}reminders/{telegram_id}/{reminder_id}/delete/")
    if response.status_code == 200:
        await update.message.reply_text("✅ Reminder deleted!", reply_markup=MAIN_MENU)
    else:
        await update.message.reply_text("Error deleting the reminder!")
    return ConversationHandler.END

async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '🕒 Toggle Time Format (12h/24h)':
        await toggle_time_format(update, context)
    
    if text == '↩️ Back to Main Menu':
        await update.message.reply_text("Main menu:", reply_markup=MAIN_MENU)
        return ConversationHandler.END
    
    return STATE_SETTINGS

async def toggle_time_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    
    response = requests.post(f"{API_URL}toggle-time-format/{telegram_id}/")
    
    if response.status_code == 200:
        data = response.json()
        format_type = "24-hour" if data['time_format_24h'] else "12-hour"
        await update.message.reply_text(f"✅ Time format changed to {format_type}!", reply_markup=SETTINGS_MENU)
    else:
        await update.message.reply_text("⚠️ Error changing time format!")
    
    return STATE_SETTINGS

async def send_reminder(reminder_data: dict, bot):
    """Send a reminder to user and mark it as sent"""
    try:
        message = f"⏰ Reminder: {reminder_data['text']}"
        await bot.send_message(
            chat_id=reminder_data['user']['telegram_id'],
            text=message
        )
        
        response = requests.post(
            f"{API_URL}reminders/mark-sent/{reminder_data['id']}/"
        )
        if response.status_code != 200:
            print(f"Failed to mark reminder {reminder_data['id']} as sent")
    except Exception as e:
        print(f"Error sending reminder: {str(e)}")

async def check_due_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Periodically check for due reminders"""
    try:
        response = requests.get(f"{API_URL}reminders/due/{566532266}")
        
        if response.status_code == 200:
            due_reminders = response.json()
            
            if due_reminders:
                print(f"Found {len(due_reminders)} due reminders")
                for reminder in due_reminders:
                    await send_reminder(reminder, context.bot)
            else:
                print("No due reminders found")
        else:
            print(f"Error checking reminders: {response.status_code}")
    except Exception as e:
        print(f"Error in check_due_reminders: {str(e)}")


async def post_init(application: Application):
    """Start the reminder checker after bot initialization"""
    check_interval = CHECK_INTERVAL
    application.job_queue.run_repeating(
        check_due_reminders,
        interval=check_interval,
        first=10
    )

def main():
    # Create the Application
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Add conversation handlers
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('➕ New Reminder'), handle_message)],
        states={
            STATE_NEW_REMINDER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_reminder_text)],
            STATE_NEW_REMINDER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, new_reminder_time)],
        },
        fallbacks=[]
    )

    delete_reminder_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('❌ Delete Reminder'), handle_message)],
        states={
            STATE_DELETE_REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_reminder)],
        },
        fallbacks=[]
    )

    settings_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('⚙ Settings'), handle_message)],
        states={
            STATE_SETTINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_handler)],
        },
        fallbacks=[]
    )

    # Add all handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv_handler)
    app.add_handler(delete_reminder_conv)
    app.add_handler(settings_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    app.run_polling()

if __name__ == '__main__':
    main()
