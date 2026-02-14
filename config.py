import os
from dotenv import load_dotenv

load_dotenv()

# Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///workout_bot.db')

# OpenAI API (اختیاری - برای تحلیل هوشمند)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Webhook settings
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_PATH = '/webhook'
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv('PORT', 8080))

# Bot settings
BOT_USERNAME = "AIWorkoutCoachBot"
BOT_VERSION = "1.0.0"
