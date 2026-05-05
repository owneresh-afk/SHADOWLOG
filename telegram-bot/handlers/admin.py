import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from data.database import (
    get_stats, get_all_users, get_all_licenses,
    create_license, generate_license_key, parse_duration, format_duration, format_time_left
)

ADMIN_ID = 8731647972
BOT_START_TIME = time.time()

AWAIT_LICENSE_COUNT = "await_license_count"
AWAIT_LICENSE_DURATION = "await_license_duration"
AWAIT_BROADCAST = "await_broadcast"

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def esc(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def get_uptime() -> str:
    elapsed = time.time() - BOT_START_TIME
    days = int(elapsed // 86400)
    hours = int((elapsed % 86400) // 3600)
    mins = int((elapsed % 3600) // 60)
    secs = int(elapsed % 60)
    if days > 0:
        return f"{days}d {hours}h {mins}m {secs}s"
    elif hours > 0:
        return f"{hours}h {mins}m {secs}s"
    return f"{mins}m {secs}s"

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        if update.callback_query:
            await update.callback_query.answer("⛔ Access Denied", show_alert=True)
            return
        await update.message.reply_text("⛔ <b>Access Denied</b>\nThis command is restricted to administrators.", parse_mode=ParseMode.HTML)
        return

    stats = get_stats()
    uptime = get_uptime()

    text = (
        f"👑 <b>Admin Control Panel</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <b>Bot Status:</b> 🟢 Online\n"
        f"⏱️ <b>Uptime:</b> <code>{uptime}</code>\n\n"
        f"📊 <b>Statistics</b>\n"
        f"├ 👥 Total Users: <code>{stats['total_users']}</code>\n"
        f"├ ✅ Active Users: <code>{stats['authorized_users']}</code>\n"
        f"├ 🔑 Total Licenses: <code>{stats['total_licenses']}</code>\n"
        f"├ 🔓 Used Licenses: <code>{stats['used_licenses']}</code>\n"
        f"└ 💳 Cards Generated: <code>{stats['total_generated']:,}</code>\n"
    )

    buttons = [
        [InlineKeyboardButton("🔑 Generate Licenses", callback_data="admin_gen_license"),
         InlineKeyboardButton("📋 List Licenses", callback_data="admin_list_licenses")],
        [InlineKeyboardButton("👥 View Users", callback_data="admin_list_users"),
         InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Full Stats", callback_data="admin_full_stats"),
         InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh")],
    ]

    markup = InlineKeyboardMarkup(buttons)
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    if not is_admin(user_id):
        await query.answer("⛔ Access Denied", show_alert=True)
        return

    data = query.data

    if data == "admin_refresh":
        await admin_panel(update, context)

    elif data == "admin_gen_license":
        context.user_data["admin_state"] = AWAIT_LICENSE_COUNT
        await query.edit_message_text(
            "🔑 <b>Generate License Keys</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "How many license keys do you want to generate?\n\n"
            "<i>Reply with a number (e.g. 5)</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel")]])
        )

    elif data == "admin_list_licenses":
        licenses = get_all_licenses()
        if not licenses:
            await query.edit_message_text(
                "📋 <b>License Keys</b>\n━━━━━━━━━━━━━━━━━━━━\nNo licenses created yet.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]])
            )
            return

        lines = []
        for key, lic in list(licenses.items())[-20:]:
            status = "🔓 Used" if lic["used"] else "🔑 Available"
            dur = format_duration(lic["duration_seconds"])
            lines.append(f"<code>{esc(key)}</code> | {status} | {dur}")

        text = f"📋 <b>License Keys</b> (Last 20)\n━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]))

    elif data == "admin_list_users":
        users = get_all_users()
        if not users:
            await query.edit_message_text(
                "👥 <b>Users</b>\n━━━━━━━━━━━━━━━━━━━━\nNo users yet.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]])
            )
            return

        lines = []
        for uid, u in list(users.items())[-15:]:
            name = esc(u.get("first_name", "Unknown"))
            username = f"@{esc(u['username'])}" if u.get("username") else "No username"
            auth = "✅" if u.get("authorized") else "❌"
            generated = u.get("total_generated", 0)
            expires = format_time_left(u["expires_at"]) if u.get("expires_at") else "N/A"
            lines.append(f"{auth} <b>{name}</b> ({username})\n   💳 {generated:,} cards | ⏳ {expires}")

        text = f"👥 <b>Users</b> (Last 15)\n━━━━━━━━━━━━━━━━━━━━\n\n" + "\n\n".join(lines)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]))

    elif data == "admin_full_stats":
        stats = get_stats()
        uptime = get_uptime()
        licenses = get_all_licenses()
        available = sum(1 for l in licenses.values() if not l.get("used"))

        text = (
            f"📊 <b>Full Bot Statistics</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ <b>Uptime:</b> <code>{uptime}</code>\n\n"
            f"👥 <b>Users</b>\n"
            f"├ Total Registered: <code>{stats['total_users']}</code>\n"
            f"└ Currently Active: <code>{stats['authorized_users']}</code>\n\n"
            f"🔑 <b>Licenses</b>\n"
            f"├ Total Created: <code>{stats['total_licenses']}</code>\n"
            f"├ Used: <code>{stats['used_licenses']}</code>\n"
            f"└ Available: <code>{available}</code>\n\n"
            f"💳 <b>Cards Generated</b>\n"
            f"└ All Time: <code>{stats['total_generated']:,}</code>\n"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]))

    elif data == "admin_broadcast":
        context.user_data["admin_state"] = AWAIT_BROADCAST
        await query.edit_message_text(
            "📢 <b>Broadcast Message</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Type the message you want to send to all authorized users.\n\n"
            "<i>Supports HTML formatting</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel")]])
        )

    elif data == "admin_back":
        await admin_panel(update, context)

    elif data == "admin_cancel":
        context.user_data.pop("admin_state", None)
        context.user_data.pop("admin_license_count", None)
        await admin_panel(update, context)

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return False

    state = context.user_data.get("admin_state")
    if not state:
        return False

    text = update.message.text.strip()

    if state == AWAIT_LICENSE_COUNT:
        try:
            count = int(text)
            if count < 1 or count > 100:
                await update.message.reply_text("❌ Please enter a number between 1 and 100.")
                return True
            context.user_data["admin_license_count"] = count
            context.user_data["admin_state"] = AWAIT_LICENSE_DURATION
            await update.message.reply_text(
                f"⏳ <b>Set Duration for {count} License(s)</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"Enter duration using:\n"
                f"• <code>1D</code> = 1 Day\n"
                f"• <code>12H</code> = 12 Hours\n"
                f"• <code>30M</code> = 30 Minutes\n\n"
                f"<i>Examples: 7D, 24H, 1D, 60M</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("1H", callback_data="admin_dur_1H"),
                     InlineKeyboardButton("1D", callback_data="admin_dur_1D"),
                     InlineKeyboardButton("7D", callback_data="admin_dur_7D"),
                     InlineKeyboardButton("30D", callback_data="admin_dur_30D")],
                    [InlineKeyboardButton("❌ Cancel", callback_data="admin_cancel")]
                ])
            )
            return True
        except ValueError:
            await update.message.reply_text("❌ Invalid number. Please enter a valid integer.")
            return True

    elif state == AWAIT_LICENSE_DURATION:
        await _process_license_duration(update, context, text)
        return True

    elif state == AWAIT_BROADCAST:
        users = get_all_users()
        sent = 0
        failed = 0
        for uid, u in users.items():
            if u.get("authorized"):
                try:
                    await context.bot.send_message(
                        chat_id=int(uid),
                        text=f"📢 <b>Announcement</b>\n━━━━━━━━━━━━━━━━━━━━\n{text}",
                        parse_mode=ParseMode.HTML
                    )
                    sent += 1
                except Exception:
                    failed += 1
        context.user_data.pop("admin_state", None)
        await update.message.reply_text(
            f"📢 <b>Broadcast Complete</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Sent: {sent}\n❌ Failed: {failed}",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_back")]])
        )
        return True

    return False

async def handle_admin_duration_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    duration_str = query.data.replace("admin_dur_", "")
    await _process_license_duration_from_callback(update, context, duration_str)

async def _process_license_duration(update, context, duration_str):
    seconds = parse_duration(duration_str)
    if not seconds:
        await update.message.reply_text("❌ Invalid format. Use 1D, 12H, 30M etc.")
        return

    count = context.user_data.get("admin_license_count", 1)
    keys = []
    for _ in range(count):
        key = generate_license_key()
        create_license(key, seconds, update.effective_user.id)
        keys.append(key)

    context.user_data.pop("admin_state", None)
    context.user_data.pop("admin_license_count", None)

    duration_label = format_duration(seconds)
    key_list = "\n".join([f"<code>{k}</code>" for k in keys])

    await update.message.reply_text(
        f"✅ <b>{count} License Key(s) Generated</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ Duration: <b>{duration_label}</b>\n\n"
        f"🔑 <b>Keys:</b>\n{key_list}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_back")]])
    )

async def _process_license_duration_from_callback(update, context, duration_str):
    query = update.callback_query
    seconds = parse_duration(duration_str)
    if not seconds:
        await query.answer("Invalid duration", show_alert=True)
        return

    count = context.user_data.get("admin_license_count", 1)
    keys = []
    for _ in range(count):
        key = generate_license_key()
        create_license(key, seconds, update.effective_user.id)
        keys.append(key)

    context.user_data.pop("admin_state", None)
    context.user_data.pop("admin_license_count", None)

    duration_label = format_duration(seconds)
    key_list = "\n".join([f"<code>{k}</code>" for k in keys])

    await query.edit_message_text(
        f"✅ <b>{count} License Key(s) Generated</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ Duration: <b>{duration_label}</b>\n\n"
        f"🔑 <b>Keys:</b>\n{key_list}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_back")]])
    )
