from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ TestCard Pro Bot is running!", 200

@app.route('/health')
def health():
    return {"status": "ok", "bot": "TestCard Pro"}, 200

@app.route('/ping')
def ping():
    return "pong", 200

def run():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()
