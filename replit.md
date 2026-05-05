# TestCard Pro — Telegram Bot

## Overview
A professional exclusive Telegram bot that generates test card numbers for developers and QA engineers. Access is gated by time-limited license keys.

## Architecture
- **Language:** Python 3.11
- **Bot Framework:** python-telegram-bot 20.7
- **Web Server:** Flask (keep-alive for Render + Uptime Robot)
- **Storage:** JSON flat-file database (`telegram-bot/data/db.json`)

## Project Structure
```
telegram-bot/
├── bot.py                  # Main entry point & all command/callback handlers
├── generator.py            # Card generation logic (Luhn algorithm)
├── keep_alive.py           # Flask server for Render + Uptime Robot
├── requirements.txt        # Python dependencies
├── data/
│   ├── bins.py             # BIN database (20 countries, 60+ banks)
│   ├── database.py         # JSON DB helpers (users, licenses)
│   └── db.json             # Runtime data (auto-created)
└── handlers/
    ├── admin.py            # Admin panel (/admin command)
    ├── cc_generator.py     # Multi-step CC generation wizard
    └── menu.py             # Main menu & profile screens
```

## Features
- License key system with time-based expiry (D/H/M format)
- 20+ countries, 60+ banks, 6 card brands in BIN database
- Multi-select: country, bank, brand, card type, category
- Up to 10,000 cards per generation with animated progress bar
- Luhn-algorithm validated card numbers
- Admin panel with stats, uptime, license generation, broadcast
- Flask keep-alive server (port 8080) for 24/7 hosting on Render

## Admin
- Admin Telegram ID: 8731647972
- Access: `/admin` command
- Features: Generate licenses, view users, bot stats, broadcast

## Environment Variables
- `TELEGRAM_BOT_TOKEN` — Bot token from @BotFather (stored as secret)

## Running
- Workflow: `Telegram Bot` → `cd telegram-bot && python bot.py`
- Flask server runs on `PORT` env var (default 8080)

## Hosting on Render
1. Create a new Web Service on Render
2. Set `TELEGRAM_BOT_TOKEN` environment variable
3. Build command: `pip install -r telegram-bot/requirements.txt`
4. Start command: `cd telegram-bot && python bot.py`
5. Add the Render URL to Uptime Robot for 24/7 uptime monitoring
