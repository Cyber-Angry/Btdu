import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
from user_logger import is_banned, save_user
from admin import admin_panel, handle_admin_callback   # ✅ sirf yeh 2 import kar

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_ID"))

# Load data.json
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    if is_banned(user_id):
        return

    save_user(user)

    username = f"@{user.username}" if user.username else f"{user.first_name or 'User'}"
    entry = f"{username} ({user_id})"

    await update.message.reply_text(DATA["start_text"])
    await update.message.reply_photo(photo=DATA["scanner_file_id"])


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await admin_panel(update, context)
    else:
        await update.message.reply_text("🚫 You are not authorized to use this command.")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(handle_admin_callback))  # ✅ bas ye hi chahiye

    print("🚀 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
