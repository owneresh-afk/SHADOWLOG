import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from data.database import get_user, format_time_left

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False):
    user = update.effective_user
    user_data = get_user(user.id)
    
    name = user.first_name or "User"
    username = f"@{user.username}" if user.username else "No username"
    
    expires_at = user_data.get("expires_at") if user_data else None
    time_left = format_time_left(expires_at) if expires_at else "Lifetime"
    total_gen = user_data.get("total_generated", 0) if user_data else 0
    
    text = (
        f"🏠 *Main Menu*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Welcome back, *{name}*! ✨\n\n"
        f"📋 Quick Info:\n"
        f"├ 👤 User: {username}\n"
        f"├ ⏳ Access: `{time_left}`\n"
        f"└ 💳 Cards Generated: `{total_gen:,}`\n\n"
        f"_Select an option below:_"
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
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
    else:
        msg = update.message or update.callback_query.message
        await msg.reply_text(text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)

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
    
    name = user.first_name or "Unknown"
    username = f"@{user.username}" if user.username else "None"
    uid = user.id
    
    expires_at = user_data.get("expires_at") if user_data else None
    time_left = format_time_left(expires_at) if expires_at else "N/A"
    total_gen = user_data.get("total_generated", 0) if user_data else 0
    joined = user_data.get("joined_at", time.time()) if user_data else time.time()
    joined_str = time.strftime("%d %b %Y", time.localtime(joined))
    license_key = user_data.get("license_key", "N/A") if user_data else "N/A"
    
    text = (
        f"👤 *My Profile*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ Name: *{name}*\n"
        f"🔖 Username: {username}\n"
        f"🆔 User ID: `{uid}`\n\n"
        f"📅 Joined: `{joined_str}`\n"
        f"🔑 License: `{license_key}`\n"
        f"⏳ Access Expires: `{time_left}`\n\n"
        f"📊 *Activity*\n"
        f"└ 💳 Total Cards Generated: `{total_gen:,}`\n"
    )
    
    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.MARKDOWN)

async def show_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from data.database import get_stats
    stats = get_stats()
    
    text = (
        f"📊 *Bot Statistics*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: `{stats['total_users']}`\n"
        f"✅ Active Users: `{stats['authorized_users']}`\n"
        f"💳 Cards Generated: `{stats['total_generated']:,}`\n"
        f"🌍 Countries Supported: `20`\n"
        f"🏦 Banks in Database: `60+`\n"
        f"💡 Card Brands: `6`\n"
    )
    
    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.MARKDOWN)

async def show_howto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"📖 *How To Use*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*Generating Test Cards:*\n"
        f"1️⃣ Click *Generate Test Cards* from main menu\n"
        f"2️⃣ Select one or more *countries*\n"
        f"3️⃣ Choose *banks* (or skip for all)\n"
        f"4️⃣ Pick *card brands* (Visa, MC, Amex...)\n"
        f"5️⃣ Select *card type* (Classic, Gold, Platinum...)\n"
        f"6️⃣ Choose *Credit* or *Debit*\n"
        f"7️⃣ Enter *quantity* (up to 10,000)\n"
        f"8️⃣ Wait for generation with progress bar\n\n"
        f"*Card Format Output:*\n"
        f"`NUMBER|MM|YYYY|CVV`\n\n"
        f"*Commands:*\n"
        f"• /start — Open main menu\n"
        f"• /redeem [KEY] — Redeem license key\n"
        f"• /profile — View your profile\n"
        f"• /help — Show this guide\n\n"
        f"⚠️ *For developer testing purposes only.*"
    )
    
    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.MARKDOWN)

async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"ℹ️ *About This Bot*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *TestCard Pro Generator*\n\n"
        f"A professional test card generation tool for developers and QA engineers.\n\n"
        f"*Features:*\n"
        f"✅ 20+ Countries supported\n"
        f"✅ 60+ Banks in database\n"
        f"✅ 6 Card brands (Visa, MC, Amex, Discover, JCB, UnionPay)\n"
        f"✅ All card types & categories\n"
        f"✅ Up to 10,000 cards at once\n"
        f"✅ Luhn algorithm validated numbers\n"
        f"✅ Exclusive license-based access\n\n"
        f"⚠️ *Disclaimer:*\n"
        f"These are test card numbers only. They are for payment gateway testing and development purposes. Using these for any fraudulent activity is illegal and strictly prohibited.\n\n"
        f"🔒 *Exclusive Access Bot*"
    )
    
    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.MARKDOWN)

async def show_license_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user(user.id)
    
    if not user_data:
        text = "🔑 *My License*\n━━━━━━━━━━━━━━━━━━━━\nNo license found."
    else:
        key = user_data.get("license_key", "N/A")
        expires_at = user_data.get("expires_at")
        time_left = format_time_left(expires_at) if expires_at else "N/A"
        status = "✅ Active" if user_data.get("authorized") else "❌ Expired"
        
        text = (
            f"🔑 *My License*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Key: `{key}`\n"
            f"Status: {status}\n"
            f"⏳ Time Remaining: `{time_left}`\n"
        )
    
    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.MARKDOWN)
