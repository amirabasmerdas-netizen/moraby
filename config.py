import os

# Token ربات تلگرام
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8564154154:AAGWvLfqMkLX2Bnh3mCDuLNkfuGKZJEws08")

# دیتابیس PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://workout_user:AmtTUedJyWetEtkcvcw5JUeJLnKP4YaI@dpg-d6864q248b3s73afjgo0-a/workout_db_6849")

# پورت برای Health Check
PORT = int(os.environ.get("PORT", 10000))

WELCOME_MESSAGE = """
🏋 **به AI Workout Coach Bot خوش آمدید!** 

من دستیار شخصی تمرینی شما هستم. کافیه تمریناتت رو برام بنویسی، من:
✅ تحلیل حرفه‌ای انجام می‌دم
🎯 هدف تمرین رو تشخیص می‌دم
⏱ زمان استراحت پیشنهاد می‌دم
📈 نسخه بهینه تمرین رو ارائه می‌دم

برای شروع از دکمه‌های زیر استفاده کن 👇
"""
