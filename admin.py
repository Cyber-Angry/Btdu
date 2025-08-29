import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes
from user_logger import USERS_FILE, BLOCKED_FILE, get_user_name

BOT_OWNER_ID = str(os.getenv("BOT_OWNER_ID") or "0")


# ✅ Generate Admin Panel Text
def generate_admin_text():
    with open(USERS_FILE, "r") as f:
        user_lines = f.read().splitlines()

    with open(BLOCKED_FILE, "r") as f:
        blocked = set(f.read().splitlines())

    text = f"👥 Total Users: {len(user_lines)}\n\n"
    for i, line in enumerate(user_lines, start=1):
        user_id, display = line.split(" | ", 1)
        status = "🚫 Blocked" if user_id in blocked else "✅ Active"
        text += f"{i}. {display} - {status}\n"

    keyboard = [
        [InlineKeyboardButton("📊 Refresh", callback_data="refresh")],
        [
            InlineKeyboardButton("🚫 Block User", callback_data="choose_block"),
            InlineKeyboardButton("✅ Unblock User", callback_data="choose_unblock"),
        ],
        [InlineKeyboardButton("📂 Export Users", callback_data="export_users")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return text, reply_markup


# ✅ Admin panel command
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != BOT_OWNER_ID:
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    text, reply_markup = generate_admin_text()
    await update.message.reply_text(text, reply_markup=reply_markup)


# ✅ Show list of users for block/unblock
def generate_user_list(action: str):
    with open(USERS_FILE, "r") as f:
        users = [line.split(" | ", 1) for line in f.read().splitlines()]

    with open(BLOCKED_FILE, "r") as f:
        blocked = set(f.read().splitlines())

    keyboard = []
    for user_id, display in users:
        if action == "block" and user_id not in blocked:
            keyboard.append([InlineKeyboardButton(f"🚫 {display}", callback_data=f"block_{user_id}")])
        elif action == "unblock" and user_id in blocked:
            keyboard.append([InlineKeyboardButton(f"✅ {display}", callback_data=f"unblock_{user_id}")])

    if not keyboard:
        keyboard = [[InlineKeyboardButton("⚠️ No users available", callback_data="none")]]

    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="refresh")])
    return InlineKeyboardMarkup(keyboard)


# ✅ Handle button clicks
async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if str(query.from_user.id) != BOT_OWNER_ID:
        await query.edit_message_text("🚫 Not authorized.")
        return

    action = query.data

    if action == "refresh":
        text, reply_markup = generate_admin_text()
        await query.edit_message_text(text=text, reply_markup=reply_markup)

    elif action == "choose_block":
        await query.edit_message_text("📋 Select a user to block:", reply_markup=generate_user_list("block"))

    elif action == "choose_unblock":
        await query.edit_message_text("📋 Select a user to unblock:", reply_markup=generate_user_list("unblock"))

    elif action.startswith("block_"):
        user_id = action.replace("block_", "")
        with open(BLOCKED_FILE, "r+") as f:
            blocked = set(f.read().splitlines())
            if user_id not in blocked:
                blocked.add(user_id)
                f.seek(0)
                f.write("\n".join(blocked) + "\n")
        await query.edit_message_text(f"🚫 Blocked {get_user_name(user_id)}", reply_markup=generate_admin_text()[1])

    elif action.startswith("unblock_"):
        user_id = action.replace("unblock_", "")
        with open(BLOCKED_FILE, "r") as f:
            blocked = set(f.read().splitlines())
        if user_id in blocked:
            blocked.remove(user_id)
            with open(BLOCKED_FILE, "w") as f:
                f.write("\n".join(blocked) + "\n")
        await query.edit_message_text(f"✅ Unblocked {get_user_name(user_id)}", reply_markup=generate_admin_text()[1])

    elif action == "export_users":
        if not os.path.exists(USERS_FILE) or os.path.getsize(USERS_FILE) == 0:
            await query.message.reply_text("⚠️ No users logged yet.")
            return

        with open(USERS_FILE, "rb") as f:
    await query.message.reply_document(
        document=InputFile(f, filename="users_list.txt"),
        caption="📂 All registered users list"
    )
