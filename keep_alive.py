from flask import Flask
from threading import Thread
import requests
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "ربات زنده است!"

@app.route('/health')
def health():
    return "OK", 200

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
    logger.info("Keep alive server started")

def ping_self():
    """پینگ زدن به خودش برای جلوگیری از خوابیدن"""
    url = os.environ.get('RENDER_EXTERNAL_URL', 'https://moraby.onrender.com')
    while True:
        try:
            time.sleep(300)  # هر ۵ دقیقه یکبار
            requests.get(url, timeout=10)
            logger.info("Ping sent to keep alive")
        except Exception as e:
            logger.error(f"Ping failed: {e}")
