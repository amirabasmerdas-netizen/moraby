import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Bot token
BOT_TOKEN = os.getenv('BOT_TOKEN', '7884677676:AAGBd1i_MU80j0nH8NWmFTRnGlL-62NfTf0')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://moraby.onrender.com')
WEBHOOK_PATH = '/webhook'

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Simple keyboard
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("🏋 ثبت تمرین"),
        KeyboardButton("ℹ️ راهنما")
    )
    return keyboard

# Handler for /start command
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply(
        "🤖 *ربات مربی هوشمند*\n\n"
        "به ربات خوش آمدید! این نسخه تستی بدون دیتابیس است.\n\n"
        "دستورات موجود:\n"
        "/help - راهنما\n"
        "/test - تست پاسخگویی",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_keyboard()
    )

# Handler for /help command
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.reply(
        "📚 *راهنمای ربات*\n\n"
        "این نسخه ساده برای تست اتصال است.\n"
        "به زودی نسخه اصلی با دیتابیس فعال می‌شود.",
        parse_mode=ParseMode.MARKDOWN
    )

# Handler for /test command
@dp.message_handler(commands=['test'])
async def test(message: types.Message):
    await message.reply("✅ ربات فعال است و پاسخ می‌دهد!")

# Handler for "🏋 ثبت تمرین" button
@dp.message_handler(lambda message: message.text == "🏋 ثبت تمرین")
async def register_workout(message: types.Message):
    await message.reply(
        "در نسخه تستی، تمرین ثبت نمی‌شود.\n"
        "اما می‌توانید پیام خود را بفرستید تا منعکس شود."
    )

# Handler for "ℹ️ راهنما" button
@dp.message_handler(lambda message: message.text == "ℹ️ راهنما")
async def guide(message: types.Message):
    await message.reply(
        "ℹ️ *راهنما*\n\n"
        "برای تست، هر پیامی بفرستید تا پاسخ بگیرید."
    )

# Echo handler for any other message
@dp.message_handler()
async def echo(message: types.Message):
    await message.reply(f"شما گفتید: {message.text}")

# Webhook handler
async def webhook_handler(request):
    try:
        update = await request.json()
        logging.info(f"📩 دریافت آپدیت: {update.get('update_id')}")
        await dp.process_update(update)
        return web.Response(text="OK", status=200)
    except Exception as e:
        logging.error(f"❌ خطا: {e}")
        return web.Response(text=str(e), status=500)

# Root handler
async def handle_root(request):
    return web.Response(
        text="<h1>🤖 ربات فعال است</h1><p>نسخه تستی بدون دیتابیس</p>",
        content_type="text/html"
    )

# Startup function
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    logging.info(f"✅ Webhook تنظیم شد: {WEBHOOK_URL + WEBHOOK_PATH}")
    
    # Get webhook info
    webhook_info = await bot.get_webhook_info()
    logging.info(f"📊 اطلاعات Webhook: {webhook_info}")

# Shutdown function
async def on_shutdown(app):
    await bot.delete_webhook()
    logging.info("👋 ربات خاموش شد")

if __name__ == '__main__':
    # Create web application
    app = web.Application()
    
    # Add routes
    app.router.add_get('/', handle_root)
    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    
    # Setup startup and shutdown hooks
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    # Get port from environment
    PORT = int(os.getenv('PORT', 8080))
    
    # Start web server
    logging.info(f"🚀 شروع سرور روی پورت {PORT}")
    web.run_app(app, host='0.0.0.0', port=PORT)
