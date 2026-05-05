import os
import sys
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode

from keep_alive import keep_alive
from data.database import (
    get_user, is_user_authorized, redeem_license,
    format_time_left, format_duration, parse_duration
)
from handlers.menu import show_main_menu, handle_menu_callback
from handlers.admin import (
    admin_panel, handle_admin_callback, handle_admin_message,
    handle_admin_duration_callback, is_admin, ADMIN_ID
)
from handlers.cc_generator import (
    start_cc_generation, show_country_selection, show_bank_selection,
    show_brand_selection, show_type_selection, show_category_selection,
    show_quantity_selection, run_generation, get_session, reset_session
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

def esc(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_admin(user.id):
        await show_main_menu(update, context)
        return

    if is_user_authorized(user.id):
        await show_main_menu(update, context)
        return

    name = esc(user.first_name or "there")
    text = (
        f"🔒 <b>Access Restricted</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Hello, <b>{name}</b>!\n\n"
        f"This is an <b>exclusive</b> bot. You are not an authorised user.\n\n"
        f"If you have a licence key, use:\n"
        f"<code>/redeem YOUR-KEY-HERE</code>\n\n"
        f"<i>Contact the administrator to obtain a licence key.</i>"
    )
    buttons = [[InlineKeyboardButton("🔑 Redeem Key", callback_data="prompt_redeem")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)


async def cmd_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args

    if not args:
        await update.message.reply_text(
            "🔑 <b>Redeem a License Key</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Usage: <code>/redeem YOUR-KEY-HERE</code>\n\n"
            "<i>Example: /redeem ABCD-1234-EFGH-5678</i>",
            parse_mode=ParseMode.HTML
        )
        return

    key = args[0].strip().upper()
    result = redeem_license(user.id, key, username=user.username, first_name=user.first_name)

    if result["success"]:
        expires_at = result["expires_at"]
        duration = format_duration(result["duration_seconds"])
        time_left = format_time_left(expires_at)

        text = (
            f"✅ <b>License Activated Successfully!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 Key: <code>{esc(key)}</code>\n"
            f"⏳ Duration: <b>{esc(duration)}</b>\n"
            f"🕐 Time Remaining: <code>{time_left}</code>\n\n"
            f"Welcome to <b>TestCard Pro</b>! 🎉"
        )
        buttons = [[InlineKeyboardButton("🏠 Open Main Menu", callback_data="main_menu")]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)

    elif result["reason"] == "invalid":
        await update.message.reply_text(
            "❌ <b>Invalid License Key</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "The key you entered does not exist. Please check and try again.",
            parse_mode=ParseMode.HTML
        )
    elif result["reason"] == "used":
        await update.message.reply_text(
            "❌ <b>License Already Used</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "This license key has already been redeemed by another user.",
            parse_mode=ParseMode.HTML
        )
    elif result["reason"] == "already_yours":
        await update.message.reply_text(
            "⚠️ <b>Already Redeemed</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "You already redeemed this key. Use /start to open the menu.",
            parse_mode=ParseMode.HTML
        )


async def cmd_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_user_authorized(user.id) and not is_admin(user.id):
        await update.message.reply_text("⛔ Access denied. Use /start to begin.", parse_mode=ParseMode.HTML)
        return
    user_data = get_user(user.id)
    name = esc(user.first_name or "Unknown")
    username = esc(f"@{user.username}") if user.username else "None"
    total_gen = user_data.get("total_generated", 0) if user_data else 0
    expires_at = user_data.get("expires_at") if user_data else None
    time_left = format_time_left(expires_at) if expires_at else "Lifetime"
    key = esc(user_data.get("license_key", "N/A")) if user_data else "N/A"

    text = (
        f"👤 <b>My Profile</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ Name: <b>{name}</b>\n"
        f"🔖 Username: {username}\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"🔑 License: <code>{key}</code>\n"
        f"⏳ Access: <code>{time_left}</code>\n"
        f"💳 Cards Generated: <code>{total_gen:,}</code>\n"
    )
    buttons = [[InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"📖 <b>Help &amp; Commands</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"• /start — Open main menu\n"
        f"• /redeem [KEY] — Activate a license key\n"
        f"• /profile — View your profile\n"
        f"• /help — Show this help message\n\n"
        f"<b>How to get access:</b>\n"
        f"Contact the administrator for a license key, then use <code>/redeem YOUR-KEY</code>.\n\n"
        f"⚠️ <b>For developer testing only.</b>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await admin_panel(update, context)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = update.effective_user

    if data == "prompt_redeem":
        await query.answer()
        await query.edit_message_text(
            "🔑 <b>Redeem License Key</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Send your key using:\n<code>/redeem YOUR-KEY-HERE</code>",
            parse_mode=ParseMode.HTML
        )
        return

    if data == "main_menu":
        await query.answer()
        if not is_user_authorized(user.id) and not is_admin(user.id):
            await query.edit_message_text(
                "🔒 <b>Access Restricted</b>\nYou are not authorised. Use <code>/redeem KEY</code> to activate.",
                parse_mode=ParseMode.HTML
            )
            return
        await show_main_menu(update, context, edit=True)
        return

    if not is_user_authorized(user.id) and not is_admin(user.id):
        await query.answer("⛔ You are not authorised. Please redeem a license key first.", show_alert=True)
        return

    if data.startswith("admin_dur_"):
        await handle_admin_duration_callback(update, context)
        return

    if data.startswith("admin_"):
        await handle_admin_callback(update, context)
        return

    if data == "menu_generate":
        await query.answer()
        await start_cc_generation(update, context)
        return

    if data.startswith("menu_"):
        await handle_menu_callback(update, context)
        return

    if data.startswith("cc_country_page_"):
        await query.answer()
        page = int(data.split("_")[-1])
        await show_country_selection(update, context, page=page, edit=True)
        return

    if data.startswith("cc_country_"):
        suffix = data[len("cc_country_"):]

        if suffix == "done":
            await query.answer()
            session = get_session(context, user.id)
            if not session.get("countries"):
                await query.answer("⚠️ Please select at least one country!", show_alert=True)
                return
            await show_bank_selection(update, context, page=0)
            return

        if suffix == "clear":
            await query.answer()
            session = get_session(context, user.id)
            session["countries"] = []
            await show_country_selection(update, context, page=session.get("country_page", 0), edit=True)
            return

        await query.answer()
        session = get_session(context, user.id)
        code = suffix
        countries = session.get("countries", [])
        if code in countries:
            countries.remove(code)
        else:
            countries.append(code)
        session["countries"] = countries
        await show_country_selection(update, context, page=session.get("country_page", 0), edit=True)
        return

    if data.startswith("cc_bank_page_"):
        await query.answer()
        page = int(data.split("_")[-1])
        await show_bank_selection(update, context, page=page)
        return

    if data.startswith("cc_bank_"):
        suffix = data[len("cc_bank_"):]

        if suffix == "skip":
            await query.answer()
            session = get_session(context, user.id)
            session["banks"] = []
            await show_brand_selection(update, context)
            return

        if suffix == "done":
            await query.answer()
            await show_brand_selection(update, context)
            return

        await query.answer()
        session = get_session(context, user.id)
        bank_name = suffix
        banks = session.get("banks", [])
        if bank_name in banks:
            banks.remove(bank_name)
        else:
            banks.append(bank_name)
        session["banks"] = banks
        await show_bank_selection(update, context, page=session.get("bank_page", 0))
        return

    if data.startswith("cc_brand_"):
        suffix = data[len("cc_brand_"):]

        if suffix == "all":
            await query.answer()
            session = get_session(context, user.id)
            session["brands"] = ["VISA", "MASTERCARD", "AMEX", "DISCOVER", "JCB", "UNIONPAY"]
            await show_brand_selection(update, context)
            return

        if suffix == "done":
            await query.answer()
            session = get_session(context, user.id)
            if not session.get("brands"):
                await query.answer("⚠️ Please select at least one brand!", show_alert=True)
                return
            await show_type_selection(update, context)
            return

        await query.answer()
        session = get_session(context, user.id)
        brands = session.get("brands", [])
        if suffix in brands:
            brands.remove(suffix)
        else:
            brands.append(suffix)
        session["brands"] = brands
        await show_brand_selection(update, context)
        return

    if data.startswith("cc_type_"):
        suffix = data[len("cc_type_"):]

        if suffix == "all":
            await query.answer()
            session = get_session(context, user.id)
            session["card_types"] = ["CLASSIC", "GOLD", "PLATINUM", "BUSINESS", "SIGNATURE", "INFINITE", "WORLD", "WORLD ELITE"]
            await show_type_selection(update, context)
            return

        if suffix == "done":
            await query.answer()
            session = get_session(context, user.id)
            if not session.get("card_types"):
                await query.answer("⚠️ Please select at least one type!", show_alert=True)
                return
            await show_category_selection(update, context)
            return

        await query.answer()
        session = get_session(context, user.id)
        card_type = suffix.replace("_", " ")
        types = session.get("card_types", [])
        if card_type in types:
            types.remove(card_type)
        else:
            types.append(card_type)
        session["card_types"] = types
        await show_type_selection(update, context)
        return

    if data.startswith("cc_cat_"):
        suffix = data[len("cc_cat_"):]

        if suffix == "all":
            await query.answer()
            session = get_session(context, user.id)
            session["card_categories"] = ["CREDIT", "DEBIT"]
            await show_category_selection(update, context)
            return

        if suffix == "done":
            await query.answer()
            session = get_session(context, user.id)
            if not session.get("card_categories"):
                await query.answer("⚠️ Please select at least one category!", show_alert=True)
                return
            await show_quantity_selection(update, context)
            return

        await query.answer()
        session = get_session(context, user.id)
        cats = session.get("card_categories", [])
        if suffix in cats:
            cats.remove(suffix)
        else:
            cats.append(suffix)
        session["card_categories"] = cats
        await show_category_selection(update, context)
        return

    if data.startswith("cc_qty_"):
        suffix = data[len("cc_qty_"):]

        if suffix == "custom":
            await query.answer()
            context.user_data["awaiting_qty"] = True
            await query.edit_message_text(
                "✏️ <b>Custom Quantity</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "Type the number of cards to generate (1–10,000):",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="cc_back_cat")]])
            )
            return

        await query.answer()
        qty = int(suffix)
        session = get_session(context, user.id)
        session["quantity"] = qty
        await run_generation(update, context, qty)
        return

    if data.startswith("cc_back_"):
        await query.answer()
        step = data[len("cc_back_"):]
        if step == "country":
            session = get_session(context, user.id)
            await show_country_selection(update, context, page=session.get("country_page", 0), edit=True)
        elif step == "bank":
            session = get_session(context, user.id)
            await show_bank_selection(update, context, page=session.get("bank_page", 0))
        elif step == "brand":
            await show_brand_selection(update, context)
        elif step == "type":
            await show_type_selection(update, context)
        elif step == "cat":
            await show_category_selection(update, context)
        return


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip() if update.message.text else ""

    if is_admin(user.id):
        handled = await handle_admin_message(update, context)
        if handled:
            return

    if context.user_data.get("awaiting_qty"):
        if not is_user_authorized(user.id) and not is_admin(user.id):
            return
        try:
            qty = int(text)
            if qty < 1 or qty > 10000:
                await update.message.reply_text("❌ Please enter a number between 1 and 10,000.")
                return
            context.user_data.pop("awaiting_qty", None)
            session = get_session(context, user.id)
            session["quantity"] = qty

            class FakeCallback:
                message = update.message
                async def answer(self): pass

            update.callback_query = FakeCallback()
            await run_generation(update, context, qty)
            return
        except ValueError:
            await update.message.reply_text("❌ Invalid number. Please enter a valid integer (1–10,000).")
            return

    if not is_user_authorized(user.id) and not is_admin(user.id):
        await update.message.reply_text(
            "🔒 You are not authorised.\nUse <code>/redeem YOUR-KEY</code> to activate access.",
            parse_mode=ParseMode.HTML
        )
        return


def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set!")
        sys.exit(1)

    keep_alive()
    logger.info("Starting TestCard Pro Bot...")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("redeem", cmd_redeem))
    app.add_handler(CommandHandler("profile", cmd_profile))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("admin", cmd_admin))

    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
