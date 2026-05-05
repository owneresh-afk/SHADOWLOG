import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from data.database import get_user, format_time_left

def esc(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False):
    user = update.effective_user
    user_data = get_user(user.id)

    name = esc(user.first_name or "User")
    username = esc(f"@{user.username}") if user.username else "No username"

    expires_at = user_data.get("expires_at") if user_data else None
    time_left = format_time_left(expires_at) if expires_at else "Lifetime"
    total_gen = user_data.get("total_generated", 0) if user_data else 0

    text = (
        f"🏠 <b>Main Menu</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Welcome back, <b>{name}</b>! ✨\n\n"
        f"📋 Quick Info:\n"
        f"├ 👤 User: {username}\n"
        f"├ ⏳ Access: <code>{time_left}</code>\n"
        f"└ 💳 Cards Generated: <code>{total_gen:,}</code>\n\n"
        f"<i>Select an option below:</i>"
    )

    buttons = [
        [InlineKeyboardButton("💳 Generate Test Cards", callback_data="menu_generate")],
        [InlineKeyboardButton("👤 My Profile", callback_data="menu_profile"),
         InlineKeyboardButton("📊 Statistics", callback_data="menu_stats")],
        [InlineKeyboardButton("📖 How To Use", callback_data="menu_howto"),
         InlineKeyboardButton("ℹ️ About Bot", callback_data="menu_about")],
        [InlineKeyboardButton("🔑 My License", callback_data="menu_license")],
    ]

    markup = InlineKeyboardMarkup(buttons)
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    else:
        msg = update.message or update.callback_query.message
        await msg.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_profile":
        await show_profile(update, context)
    elif data == "menu_stats":
        await show_user_stats(update, context)
    elif data == "menu_howto":
        await show_howto(update, context)
    elif data == "menu_about":
        await show_about(update, context)
    elif data == "menu_license":
        await show_license_info(update, context)

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user(user.id)

    name = esc(user.first_name or "Unknown")
    username = esc(f"@{user.username}") if user.username else "None"
    uid = user.id

    expires_at = user_data.get("expires_at") if user_data else None
    time_left = format_time_left(expires_at) if expires_at else "N/A"
    total_gen = user_data.get("total_generated", 0) if user_data else 0
    joined = user_data.get("joined_at", time.time()) if user_data else time.time()
    joined_str = time.strftime("%d %b %Y", time.localtime(joined))
    license_key = user_data.get("license_key", "N/A") if user_data else "N/A"

    text = (
        f"👤 <b>My Profile</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ Name: <b>{name}</b>\n"
        f"🔖 Username: {username}\n"
        f"🆔 User ID: <code>{uid}</code>\n\n"
        f"📅 Joined: <code>{joined_str}</code>\n"
        f"🔑 License: <code>{esc(license_key)}</code>\n"
        f"⏳ Access Expires: <code>{time_left}</code>\n\n"
        f"📊 <b>Activity</b>\n"
        f"└ 💳 Total Cards Generated: <code>{total_gen:,}</code>\n"
    )

    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from data.database import get_stats
    stats = get_stats()

    text = (
        f"📊 <b>Bot Statistics</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: <code>{stats['total_users']}</code>\n"
        f"✅ Active Users: <code>{stats['authorized_users']}</code>\n"
        f"💳 Cards Generated: <code>{stats['total_generated']:,}</code>\n"
        f"🌍 Countries Supported: <code>20</code>\n"
        f"🏦 Banks in Database: <code>60+</code>\n"
        f"💡 Card Brands: <code>6</code>\n"
    )

    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)

async def show_howto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"📖 <b>How To Use</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Generating Test Cards:</b>\n"
        f"1️⃣ Click <b>Generate Test Cards</b> from main menu\n"
        f"2️⃣ Select one or more <b>countries</b>\n"
        f"3️⃣ Choose <b>banks</b> (or skip for all)\n"
        f"4️⃣ Pick <b>card brands</b> (Visa, MC, Amex...)\n"
        f"5️⃣ Select <b>card type</b> (Classic, Gold, Platinum...)\n"
        f"6️⃣ Choose <b>Credit</b> or <b>Debit</b>\n"
        f"7️⃣ Enter <b>quantity</b> (up to 10,000)\n"
        f"8️⃣ Wait for generation with progress bar\n\n"
        f"<b>Card Format Output:</b>\n"
        f"<code>NUMBER|MM|YYYY|CVV</code>\n\n"
        f"<b>Commands:</b>\n"
        f"• /start — Open main menu\n"
        f"• /redeem [KEY] — Redeem license key\n"
        f"• /profile — View your profile\n"
        f"• /help — Show this guide\n\n"
        f"⚠️ <b>For developer testing purposes only.</b>"
    )

    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)

async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"ℹ️ <b>About This Bot</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 <b>TestCard Pro Generator</b>\n\n"
        f"A professional test card generation tool for developers and QA engineers.\n\n"
        f"<b>Features:</b>\n"
        f"✅ 20+ Countries supported\n"
        f"✅ 60+ Banks in database\n"
        f"✅ 6 Card brands (Visa, MC, Amex, Discover, JCB, UnionPay)\n"
        f"✅ All card types &amp; categories\n"
        f"✅ Up to 10,000 cards at once\n"
        f"✅ Luhn algorithm validated numbers\n"
        f"✅ Exclusive license-based access\n\n"
        f"⚠️ <b>Disclaimer:</b>\n"
        f"These are test card numbers only, for payment gateway testing and development. "
        f"Using these for any fraudulent activity is illegal and strictly prohibited.\n\n"
        f"🔒 <b>Exclusive Access Bot</b>"
    )

    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)

async def show_license_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user(user.id)

    if not user_data:
        text = "🔑 <b>My License</b>\n━━━━━━━━━━━━━━━━━━━━\nNo license found."
    else:
        key = esc(user_data.get("license_key", "N/A"))
        expires_at = user_data.get("expires_at")
        time_left = format_time_left(expires_at) if expires_at else "N/A"
        status = "✅ Active" if user_data.get("authorized") else "❌ Expired"

        text = (
            f"🔑 <b>My License</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Key: <code>{key}</code>\n"
            f"Status: {status}\n"
            f"⏳ Time Remaining: <code>{time_left}</code>\n"
        )

    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)
