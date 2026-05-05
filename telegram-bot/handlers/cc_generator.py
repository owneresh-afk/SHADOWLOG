import asyncio
import io
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from data.bins import COUNTRY_BANKS, CARD_BRANDS, CARD_TYPES, CARD_CATEGORIES
from data.database import increment_generated
from generator import generate_cards, format_card

COUNTRIES_PER_PAGE = 8
BANKS_PER_PAGE = 6


def get_session(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> dict:
    if "cc_session" not in context.user_data:
        context.user_data["cc_session"] = {}
    return context.user_data["cc_session"]


def reset_session(context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cc_session"] = {
        "countries": [],
        "banks": [],
        "brands": [],
        "card_types": [],
        "card_categories": [],
        "quantity": 0,
        "country_page": 0,
        "bank_page": 0,
    }


async def start_cc_generation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_session(context)
    await show_country_selection(update, context, page=0, edit=False)


async def show_country_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0, edit: bool = True):
    session = get_session(context, update.effective_user.id)
    session["country_page"] = page
    selected = session.get("countries", [])

    all_countries = list(COUNTRY_BANKS.items())
    total_pages = (len(all_countries) + COUNTRIES_PER_PAGE - 1) // COUNTRIES_PER_PAGE
    start = page * COUNTRIES_PER_PAGE
    page_countries = all_countries[start:start + COUNTRIES_PER_PAGE]

    buttons = []
    row = []
    for code, data in page_countries:
        flag = data["flag"]
        name = data["name"]
        check = "✅ " if code in selected else ""
        row.append(InlineKeyboardButton(f"{check}{flag} {name}", callback_data=f"cc_country_{code}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"cc_country_page_{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"cc_country_page_{page+1}"))
    if nav_row:
        buttons.append(nav_row)

    action_row = []
    if selected:
        action_row.append(InlineKeyboardButton(f"✅ Continue ({len(selected)} selected)", callback_data="cc_country_done"))
    action_row.append(InlineKeyboardButton("🔄 Clear All", callback_data="cc_country_clear"))
    buttons.append(action_row)
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])

    selected_flags = ""
    if selected:
        flags = [COUNTRY_BANKS[c]["flag"] + " " + COUNTRY_BANKS[c]["name"] for c in selected if c in COUNTRY_BANKS]
        selected_flags = f"\n\n✅ <b>Selected:</b> {', '.join(flags)}"

    text = (
        f"🌍 <b>Step 1/6 — Select Countries</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Choose one or more countries to generate test cards from.\n"
        f"Page {page+1}/{total_pages}{selected_flags}"
    )

    markup = InlineKeyboardMarkup(buttons)
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
    else:
        msg = update.message or update.callback_query.message
        await msg.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def show_bank_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    session = get_session(context, update.effective_user.id)
    session["bank_page"] = page
    selected_countries = session.get("countries", [])
    selected_banks = session.get("banks", [])

    all_banks = []
    for cc in selected_countries:
        country_data = COUNTRY_BANKS.get(cc, {})
        for bank_name in country_data.get("banks", {}).keys():
            if bank_name not in all_banks:
                all_banks.append(bank_name)

    total_pages = max(1, (len(all_banks) + BANKS_PER_PAGE - 1) // BANKS_PER_PAGE)
    start = page * BANKS_PER_PAGE
    page_banks = all_banks[start:start + BANKS_PER_PAGE]

    buttons = []
    for bank in page_banks:
        check = "✅ " if bank in selected_banks else ""
        buttons.append([InlineKeyboardButton(f"{check}🏦 {bank}", callback_data=f"cc_bank_{bank[:30]}")])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"cc_bank_page_{page-1}"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"cc_bank_page_{page+1}"))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton("⏭️ Skip (All Banks)", callback_data="cc_bank_skip"),
        InlineKeyboardButton("✅ Continue", callback_data="cc_bank_done"),
    ])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="cc_back_country")])

    selected_text = ""
    if selected_banks:
        preview = ", ".join(selected_banks[:4])
        more = f" +{len(selected_banks)-4} more" if len(selected_banks) > 4 else ""
        selected_text = f"\n\n✅ <b>Selected:</b> {preview}{more}"

    text = (
        f"🏦 <b>Step 2/6 — Select Banks</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Choose specific banks or skip to use all banks.\n"
        f"Page {page+1}/{total_pages}{selected_text}"
    )
    markup = InlineKeyboardMarkup(buttons)
    await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def show_brand_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(context, update.effective_user.id)
    selected = session.get("brands", [])

    all_brands = ["VISA", "MASTERCARD", "AMEX", "DISCOVER", "JCB", "UNIONPAY"]
    brand_icons = {"VISA": "💳", "MASTERCARD": "🔴", "AMEX": "💎", "DISCOVER": "🔶", "JCB": "🔷", "UNIONPAY": "🐉"}

    buttons = []
    row = []
    for brand in all_brands:
        check = "✅ " if brand in selected else ""
        icon = brand_icons.get(brand, "💳")
        row.append(InlineKeyboardButton(f"{check}{icon} {brand}", callback_data=f"cc_brand_{brand}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton("🌐 All Brands", callback_data="cc_brand_all")])
    action_row = []
    if selected:
        action_row.append(InlineKeyboardButton(f"✅ Continue ({len(selected)})", callback_data="cc_brand_done"))
    action_row.append(InlineKeyboardButton("🔙 Back", callback_data="cc_back_bank"))
    buttons.append(action_row)

    selected_text = ""
    if selected:
        selected_text = f"\n\n✅ <b>Selected:</b> {', '.join(selected)}"

    text = (
        f"💳 <b>Step 3/6 — Card Issuer / Brand</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Select which card brands to generate.{selected_text}"
    )
    markup = InlineKeyboardMarkup(buttons)
    await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def show_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(context, update.effective_user.id)
    selected = session.get("card_types", [])

    types = ["CLASSIC", "GOLD", "PLATINUM", "BUSINESS", "SIGNATURE", "INFINITE", "WORLD", "WORLD ELITE"]
    icons = {"CLASSIC": "🃏", "GOLD": "🥇", "PLATINUM": "⬜", "BUSINESS": "💼",
             "SIGNATURE": "✍️", "INFINITE": "♾️", "WORLD": "🌍", "WORLD ELITE": "👑"}

    buttons = []
    row = []
    for t in types:
        check = "✅ " if t in selected else ""
        icon = icons.get(t, "🃏")
        row.append(InlineKeyboardButton(f"{check}{icon} {t}", callback_data=f"cc_type_{t.replace(' ', '_')}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton("✅ All Types", callback_data="cc_type_all")])
    action_row = []
    if selected:
        action_row.append(InlineKeyboardButton(f"✅ Continue ({len(selected)})", callback_data="cc_type_done"))
    action_row.append(InlineKeyboardButton("🔙 Back", callback_data="cc_back_brand"))
    buttons.append(action_row)

    selected_text = ""
    if selected:
        selected_text = f"\n\n✅ <b>Selected:</b> {', '.join(selected)}"

    text = (
        f"🃏 <b>Step 4/6 — Card Type</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Choose card tier(s) to generate.{selected_text}"
    )
    markup = InlineKeyboardMarkup(buttons)
    await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def show_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(context, update.effective_user.id)
    selected = session.get("card_categories", [])

    buttons = []
    for cat, icon in [("CREDIT", "💳"), ("DEBIT", "🏧")]:
        check = "✅ " if cat in selected else ""
        buttons.append([InlineKeyboardButton(f"{check}{icon} {cat}", callback_data=f"cc_cat_{cat}")])

    buttons.append([InlineKeyboardButton("✅ Both", callback_data="cc_cat_all")])
    action_row = []
    if selected:
        action_row.append(InlineKeyboardButton(f"✅ Continue ({len(selected)})", callback_data="cc_cat_done"))
    action_row.append(InlineKeyboardButton("🔙 Back", callback_data="cc_back_type"))
    buttons.append(action_row)

    selected_text = ""
    if selected:
        selected_text = f"\n\n✅ <b>Selected:</b> {', '.join(selected)}"

    text = (
        f"💰 <b>Step 5/6 — Credit or Debit?</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Choose card category.{selected_text}"
    )
    markup = InlineKeyboardMarkup(buttons)
    await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def show_quantity_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    presets = [1, 5, 10, 25, 50, 100, 500, 1000, 5000, 10000]
    buttons = []
    row = []
    for q in presets:
        row.append(InlineKeyboardButton(str(q), callback_data=f"cc_qty_{q}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton("✏️ Custom Amount", callback_data="cc_qty_custom")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="cc_back_cat")])

    text = (
        f"🔢 <b>Step 6/6 — How Many Cards?</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Select a preset or enter a custom amount.\n"
        f"Maximum: <b>10,000 cards</b>"
    )
    markup = InlineKeyboardMarkup(buttons)
    await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


async def run_generation(update: Update, context: ContextTypes.DEFAULT_TYPE, quantity: int):
    session = get_session(context, update.effective_user.id)
    user_id = update.effective_user.id

    countries = session.get("countries", [])
    banks = session.get("banks", [])
    brands = session.get("brands", [])
    card_types = session.get("card_types", [])
    card_categories = session.get("card_categories", [])

    msg = update.callback_query.message if update.callback_query else update.message

    progress_msg = await msg.reply_text(
        f"⚙️ <b>Generating {quantity:,} Test Cards...</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"▱▱▱▱▱▱▱▱▱▱ 0%",
        parse_mode=ParseMode.HTML
    )

    bars = 10
    for i in range(bars):
        filled = i + 1
        bar = "▰" * filled + "▱" * (bars - filled)
        pct = int((filled / bars) * 100)
        await asyncio.sleep(0.25)
        try:
            await progress_msg.edit_text(
                f"⚙️ <b>Generating {quantity:,} Test Cards...</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"{bar} {pct}%",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

    cards = generate_cards(countries, banks, brands, card_types, card_categories, quantity)
    increment_generated(user_id, len(cards))

    await progress_msg.edit_text(
        f"✅ <b>Generation Complete!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"▰▰▰▰▰▰▰▰▰▰ 100%\n\n"
        f"📊 Generated: <b>{len(cards):,} cards</b>\n"
        f"📄 Preparing your <b>.txt</b> file...",
        parse_mode=ParseMode.HTML
    )

    country_names = [COUNTRY_BANKS[c]["name"] for c in countries if c in COUNTRY_BANKS]
    header_lines = [
        "=" * 50,
        "  TestCard Pro — Test Card Generator",
        "=" * 50,
        f"  Generated : {len(cards):,} cards",
        f"  Countries : {', '.join(country_names) if country_names else 'All'}",
        f"  Brands    : {', '.join(brands) if brands else 'All'}",
        f"  Types     : {', '.join(card_types) if card_types else 'All'}",
        f"  Category  : {', '.join(card_categories) if card_categories else 'All'}",
        f"  Banks     : {', '.join(banks[:3]) + ('...' if len(banks) > 3 else '') if banks else 'All'}",
        "=" * 50,
        "  Format: NUMBER|MM|YYYY|CVV",
        "=" * 50,
        "",
    ]

    card_lines = [format_card(c) for c in cards]
    file_content = "\n".join(header_lines + card_lines) + "\n"

    file_bytes = io.BytesIO(file_content.encode("utf-8"))
    file_bytes.name = f"testcards_{quantity}.txt"

    footer_buttons = [
        [InlineKeyboardButton("🔄 Generate Again", callback_data="menu_generate")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]

    caption = (
        f"✅ <b>Cards Ready!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Total: <b>{len(cards):,} cards</b>\n"
        f"🌍 Countries: {', '.join(country_names[:3]) + ('...' if len(country_names) > 3 else '') if country_names else 'All'}\n"
        f"💳 Brands: {', '.join(brands[:3]) if brands else 'All'}\n"
        f"📂 Format: <code>NUMBER|MM|YYYY|CVV</code>"
    )

    await msg.reply_document(
        document=file_bytes,
        filename=f"testcards_{quantity}.txt",
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(footer_buttons)
    )
