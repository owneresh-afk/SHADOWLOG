# Deploying TestCard Pro Bot to Render

## Step 1 — Push to GitHub
Push the `telegram-bot/` folder (or full repo) to a GitHub repository.

## Step 2 — Create Render Web Service
1. Go to https://render.com and sign in
2. Click **New → Web Service**
3. Connect your GitHub repo
4. Set the following:
   - **Name:** testcard-pro-bot
   - **Root Directory:** `telegram-bot`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`

## Step 3 — Add Environment Variables
In Render → Environment tab, add:
- `TELEGRAM_BOT_TOKEN` = your bot token from BotFather
- `FLASK_PORT` = 10000 (Render uses port 10000)

## Step 4 — Deploy
Click **Create Web Service** and wait for deployment.

## Step 5 — Set Up Uptime Robot (Keep Alive 24/7)
1. Go to https://uptimerobot.com
2. Add a new monitor:
   - **Monitor Type:** HTTP(s)
   - **URL:** `https://your-render-url.onrender.com/ping`
   - **Interval:** Every 5 minutes
3. This pings your bot every 5 minutes so Render doesn't spin it down.

## Endpoints
- `/` — Status page
- `/health` — JSON health check
- `/ping` — Uptime Robot ping endpoint

## Bot Commands
- `/start` — Main menu (or unauthorized message)
- `/redeem KEY` — Activate license key
- `/profile` — View your profile
- `/help` — Help & commands
- `/admin` — Admin panel (admin only, ID: 8731647972)

## Admin — Generate License Keys
1. Send `/admin` to the bot
2. Click **Generate Licenses**
3. Enter how many keys to create
4. Enter duration: `1H`, `7D`, `30D`, `60M`, etc.
5. Share the generated keys with users
