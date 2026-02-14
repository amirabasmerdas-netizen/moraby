import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiohttp import web

from config import BOT_TOKEN, DATABASE_URL, WELCOME_MESSAGE, PORT
from database import Database
from workout_analyzer import WorkoutAnalyzer
from ai_analyzer import AIAnalyzer

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# مقداردهی اولیه
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# اتصال به دیتابیس
db = Database(DATABASE_URL)
workout_analyzer = WorkoutAnalyzer()
ai_analyzer = AIAnalyzer()

# ==================== تمام توابع قبلی اینجا می‌آیند ====================
# (همه توابع start_command, register_workout, process_workout و ...)
# دقیقاً مثل کد قبلی، بدون تغییر

# تعریف حالت‌ها
class WorkoutStates(StatesGroup):
    waiting_for_workout = State()
    waiting_for_goal = State()
    waiting_for_difficulty = State()

# کیبورد اصلی
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("🏋 ثبت برنامه تمرینی"),
        KeyboardButton("📊 تحلیل تمرین من"),
        KeyboardButton("📅 ساخت برنامه هفتگی"),
        KeyboardButton("⚡ ارتقای تمرین"),
        KeyboardButton("📉 کاهش وزن هوشمند"),
        KeyboardButton("📈 افزایش قدرت"),
        KeyboardButton("🧠 راهنمای تمرین اصولی"),
        KeyboardButton("⚙ تنظیمات")
    )
    return keyboard

# کیبورد اینلاین برای بعد از تحلیل
def get_analysis_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🔥 سخت‌ترش کن", callback_data="make_harder"),
        InlineKeyboardButton("🧊 سبک‌ترش کن", callback_data="make_easier"),
        InlineKeyboardButton("⏱ تنظیم زمان استراحت", callback_data="adjust_rest"),
        InlineKeyboardButton("📋 ذخیره این تمرین", callback_data="save_workout"),
        InlineKeyboardButton("📤 خروجی PDF", callback_data="export_pdf"),
        InlineKeyboardButton("🔄 بازنویسی حرفه‌ای", callback_data="rewrite_pro")
    )
    return keyboard

# دستور start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    user = message.from_user
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    await message.reply(
        WELCOME_MESSAGE,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# ثبت برنامه تمرینی
@dp.message_handler(lambda message: message.text == "🏋 ثبت برنامه تمرینی")
async def register_workout(message: types.Message):
    await WorkoutStates.waiting_for_workout.set()
    await message.reply(
        "📝 لطفاً تمریناتت رو به این شکل برام بنویس:\n\n"
        "دراز نشست=۲۰\n"
        "شنا=۱۰\n"
        "اسکات=۵\n"
        "طناب=۳ دقیقه\n\n"
        "یا هر شکل دیگه‌ای که راحت‌تری ✍️"
    )

# دریافت تمرین از کاربر
@dp.message_handler(state=WorkoutStates.waiting_for_workout)
async def process_workout(message: types.Message, state: FSMContext):
    workout_text = message.text
    
    # تحلیل با workout_analyzer
    exercises = workout_analyzer.parse_workout(workout_text)
    
    if not exercises:
        await message.reply("❌ متوجه تمرینات نشدم! لطفاً دوباره با فرمت واضح‌تر بنویس.")
        return
    
    # محاسبات
    volume = workout_analyzer.calculate_volume(exercises)
    calories = workout_analyzer.calculate_calories(exercises)
    goal = workout_analyzer.detect_goal(exercises, volume)
    difficulty = workout_analyzer.estimate_difficulty(volume)
    rest_time = workout_analyzer.suggest_rest_time(exercises, difficulty)
    imbalances = workout_analyzer.detect_imbalance(exercises)
    improvements = workout_analyzer.suggest_improvement(exercises, difficulty)
    overtraining = workout_analyzer.check_overtraining(exercises, difficulty)
    
    # تحلیل با AI
    ai_analysis = ai_analyzer.analyze_text(workout_text)
    
    # ذخیره در دیتابیس
    db.save_workout(
        user_id=message.from_user.id,
        workout_text=workout_text,
        analysis=f"هدف: {goal} - شدت: {difficulty}",
        calories=calories,
        intensity=difficulty
    )
    
    # ساخت پیام نتیجه
    result = f"""🔥 **تحلیل تمرین شما:**

📋 **تمرینات ثبت شده:**
"""
    for ex in exercises:
        result += f"• {ex['name']}: {ex['value']} {ex['unit']} (دسته: {ex['category']})\n"
    
    result += f"""
📊 **آمار کلی:**
• حجم کل: {volume}
• کالری تقریبی: {calories} کالری
• هدف تمرین: {goal}
• سطح سختی: {difficulty}

⏱ **زمان استراحت پیشنهادی:**
• بین حرکات: {rest_time} ثانیه
💧 آب: هر ۱۵ دقیقه

"""
    
    if imbalances:
        result += "⚠ **هشدارهای تعادل:**\n"
        for w in imbalances:
            result += f"• {w}\n"
        result += "\n"
    
    if overtraining:
        result += "⚠ **هشدار تمرین بیش از حد:**\n"
        for w in overtraining:
            result += f"• {w}\n"
        result += "\n"
    
    result += f"📈 **پیشنهاد بهینه‌سازی:**\n{improvements}\n\n"
    
    if ai_analysis.get("suggestions"):
        result += "🧠 **پیشنهادات هوشمند:**\n"
        for s in ai_analysis["suggestions"]:
            result += f"• {s}\n"
    
    await message.reply(result, parse_mode="Markdown", reply_markup=get_analysis_keyboard())
    await state.finish()

# تحلیل تمرین قبلی
@dp.message_handler(lambda message: message.text == "📊 تحلیل تمرین من")
async def analyze_my_workout(message: types.Message):
    history = db.get_user_history(message.from_user.id, limit=1)
    
    if history:
        last_workout = history[0]
        await message.reply(
            f"📊 **آخرین تمرین ثبت شده:**\n\n"
            f"📅 تاریخ: {last_workout['workout_date']}\n"
            f"🏋 تمرین: {last_workout['workout_text']}\n"
            f"🔥 کالری: {last_workout['calories']}\n"
            f"📈 شدت: {last_workout['intensity']}\n\n"
            f"برای تحلیل جدید از دکمه ثبت تمرین استفاده کن 👇",
            parse_mode="Markdown"
        )
    else:
        await message.reply("📭 هنوز تمرینی ثبت نکردی! از دکمه 'ثبت برنامه تمرینی' شروع کن.")

# ساخت برنامه هفتگی
@dp.message_handler(lambda message: message.text == "📅 ساخت برنامه هفتگی")
async def weekly_plan(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🔥 چربی‌سوزی", callback_data="plan_fatloss"),
        InlineKeyboardButton("💪 افزایش قدرت", callback_data="plan_strength"),
        InlineKeyboardButton("⚡ استقامتی", callback_data="plan_endurance"),
        InlineKeyboardButton("🧘 ترکیبی", callback_data="plan_mixed")
    )
    
    await message.reply(
        "🎯 **هدف خود از برنامه هفتگی رو انتخاب کن:**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# ارتقای تمرین
@dp.message_handler(lambda message: message.text == "⚡ ارتقای تمرین")
async def upgrade_workout(message: types.Message):
    await WorkoutStates.waiting_for_workout.set()
    await message.reply(
        "📝 تمرین فعلیت رو برام بنویس تا نسخه پیشرفته‌ترش رو بهت بدم:"
    )

# کاهش وزن هوشمند
@dp.message_handler(lambda message: message.text == "📉 کاهش وزن هوشمند")
async def smart_weight_loss(message: types.Message):
    await message.reply(
        "🎯 **برنامه کاهش وزن هوشمند:**\n\n"
        "برای شروع، اطلاعات زیر رو برام بفرست:\n"
        "1️⃣ وزن فعلی\n"
        "2️⃣ وزن هدف\n"
        "3️⃣ تعداد جلسات تمرین در هفته\n\n"
        "مثال: ۷۵, ۶۵, ۴"
    )
    await WorkoutStates.waiting_for_goal.set()

# افزایش قدرت
@dp.message_handler(lambda message: message.text == "📈 افزایش قدرت")
async def strength_gain(message: types.Message):
    await message.reply(
        "💪 **برنامه افزایش قدرت:**\n\n"
        "برای شروع، سطح فعلی خودت رو انتخاب کن:",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("مبتدی", callback_data="strength_beginner"),
            InlineKeyboardButton("متوسط", callback_data="strength_intermediate"),
            InlineKeyboardButton("حرفه‌ای", callback_data="strength_advanced")
        )
    )

# راهنمای تمرین اصولی
@dp.message_handler(lambda message: message.text == "🧠 راهنمای تمرین اصولی")
async def tutorial(message: types.Message):
    tutorial_text = """
🧠 **راهنمای تمرین اصولی:**

🔹 **قبل از تمرین:**
• ۱۰ دقیقه گرم کردن
• حرکات کششی پویا
• نوشیدن آب کافی

🔸 **حین تمرین:**
• فرم صحیح حرکات رو رعایت کن
• بین حرکات ۳۰-۶۰ ثانیه استراحت کن
• هر ۱۵-۲۰ دقیقه آب بخور

🔹 **بعد از تمرین:**
• ۵-۱۰ دقیقه سرد کردن
• حرکات کششی ایستا
• تغذیه مناسب (پروتئین + کربوهیدرات)

⚠ **نکات مهم:**
• به بدن خود گوش کن
• در صورت درد شدید، تمرین رو قطع کن
• پیشرفت تدریجی داشته باش
• ۴۸ ساعت بین تمرینات یک گروه عضلانی فاصله بنداز

💧 **هیدراتاسیون:**
• قبل تمرین: ۵۰۰ میلی‌لیتر
• حین تمرین: هر ۱۵ دقیقه ۲۰۰ میلی‌لیتر
• بعد تمرین: ۵۰۰ میلی‌لیتر به ازای هر نیم‌ساعت
"""
    await message.reply(tutorial_text, parse_mode="Markdown")

# تنظیمات
@dp.message_handler(lambda message: message.text == "⚙ تنظیمات")
async def settings(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🔔 اعلان‌ها", callback_data="settings_notifications"),
        InlineKeyboardButton("📊 سطح تمرین", callback_data="settings_level"),
        InlineKeyboardButton("🔄 بازنشانی", callback_data="settings_reset"),
        InlineKeyboardButton("📤 خروجی", callback_data="settings_export")
    )
    
    await message.reply(
        "⚙ **تنظیمات ربات:**\n\n"
        "از اینجا می‌تونی تنظیمات ربات رو شخصی‌سازی کنی.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# پاسخ به callbackهای اینلاین
@dp.callback_query_handler(lambda c: True)
async def inline_callbacks(callback_query: types.CallbackQuery):
    data = callback_query.data
    
    if data == "make_harder":
        await callback_query.message.answer(
            "🔥 **نسخه سخت‌تر تمرین:**\n\n"
            "برای دریافت نسخه سخت‌تر، لطفاً تمرین فعلیت رو با دکمه ثبت برنامه وارد کن."
        )
    
    elif data == "make_easier":
        await callback_query.message.answer(
            "🧊 **نسخه سبک‌تر تمرین:**\n\n"
            "برای شروع می‌تونی تعداد تکرارها رو ۲۰٪ کاهش بدی و زمان استراحت رو افزایش بدی."
        )
    
    elif data == "adjust_rest":
        keyboard = InlineKeyboardMarkup(row_width=3)
        keyboard.add(
            InlineKeyboardButton("۳۰ ثانیه", callback_data="rest_30"),
            InlineKeyboardButton("۴۵ ثانیه", callback_data="rest_45"),
            InlineKeyboardButton("۶۰ ثانیه", callback_data="rest_60"),
            InlineKeyboardButton("۹۰ ثانیه", callback_data="rest_90"),
            InlineKeyboardButton("۲ دقیقه", callback_data="rest_120")
        )
        await callback_query.message.answer(
            "⏱ **زمان استراحت مورد نظر را انتخاب کن:**",
            reply_markup=keyboard
        )
    
    elif data == "save_workout":
        await callback_query.message.answer(
            "✅ تمرین با موفقیت در تاریخچه شما ذخیره شد!"
        )
    
    elif data == "export_pdf":
        await callback_query.message.answer(
            "📤 در حال آماده‌سازی PDF... لطفاً صبر کنید."
        )
    
    elif data == "rewrite_pro":
        await callback_query.message.answer(
            "🔄 در حال بازنویسی حرفه‌ای تمرین..."
        )
    
    # پاسخ به تنظیمات استراحت
    elif data.startswith("rest_"):
        time = data.split("_")[1]
        await callback_query.message.answer(
            f"✅ زمان استراحت روی {time} ثانیه تنظیم شد.\n\n"
            f"به یاد داشته باش که بین ستها هم {time} ثانیه استراحت کنی."
        )
    
    # پاسخ به برنامه‌های هفتگی
    elif data.startswith("plan_"):
        plan_type = data.split("_")[1]
        plans = {
            "fatloss": "🔥 **برنامه چربی‌سوزی هفتگی:**\n\n"
                      "شنبه: هوازی ۴۵ دقیقه + کرانچ\n"
                      "یک‌شنبه: تمرین قدرتی تمام بدن\n"
                      "دوشنبه: استراحت یا یوگا\n"
                      "سه‌شنبه: اینتروال ۳۰ دقیقه\n"
                      "چهارشنبه: تمرین قدرتی میان‌تنه\n"
                      "پنج‌شنبه: هوازی ۶۰ دقیقه\n"
                      "جمعه: استراحت فعال",
            
            "strength": "💪 **برنامه افزایش قدرت هفتگی:**\n\n"
                        "شنبه: سینه و پشت بازو\n"
                        "یک‌شنبه: پا و سرشانه\n"
                        "دوشنبه: استراحت\n"
                        "سه‌شنبه: پشت و جلو بازو\n"
                        "چهارشنبه: پا و سرشانه\n"
                        "پنج‌شنبه: سینه و زیربغل\n"
                        "جمعه: استراحت",
            
            "endurance": "⚡ **برنامه استقامتی هفتگی:**\n\n"
                         "شنبه: دویدن ۵ کیلومتر\n"
                         "یک‌شنبه: شنا ۱۰۰۰ متر\n"
                         "دوشنبه: دوچرخه ۲۰ کیلومتر\n"
                         "سه‌شنبه: تمرین تناوبی\n"
                         "چهارشنبه: استراحت\n"
                         "پنج‌شنبه: کوهنوردی\n"
                         "جمعه: پیاده‌روی سریع",
            
            "mixed": "🧘 **برنامه ترکیبی هفتگی:**\n\n"
                     "شنبه: قدرتی بالاتنه + هوازی\n"
                     "یک‌شنبه: یوگا و کشش\n"
                     "دوشنبه: قدرتی پایین‌تنه\n"
                     "سه‌شنبه: اینتروال + کرانچ\n"
                     "چهارشنبه: استراحت\n"
                     "پنج‌شنبه: تمرین دایره‌ای\n"
                     "جمعه: پیاده‌روی طولانی"
        }
        
        await callback_query.message.answer(plans.get(plan_type, "برنامه مورد نظر یافت نشد."), parse_mode="Markdown")
    
    # پاسخ به تنظیمات
    elif data.startswith("settings_"):
        setting = data.split("_")[1]
        if setting == "notifications":
            await callback_query.message.answer("🔔 اعلان‌ها با موفقیت تغییر کرد!")
        elif setting == "level":
            keyboard = InlineKeyboardMarkup(row_width=3)
            keyboard.add(
                InlineKeyboardButton("مبتدی", callback_data="level_beginner"),
                InlineKeyboardButton("متوسط", callback_data="level_intermediate"),
                InlineKeyboardButton("حرفه‌ای", callback_data="level_advanced")
            )
            await callback_query.message.answer("📊 سطح تمرینی خود را انتخاب کن:", reply_markup=keyboard)
        elif setting == "reset":
            await callback_query.message.answer("🔄 تنظیمات به حالت پیش‌فرض بازگشت!")
        elif setting == "export":
            await callback_query.message.answer("📤 اطلاعات شما در حال آماده‌سازی است...")
    
    # پاسخ به سطوح
    elif data.startswith("level_"):
        level = data.split("_")[1]
        db.update_user_level(callback_query.from_user.id, level)
        await callback_query.message.answer(f"✅ سطح شما به {level} تغییر کرد!")
    
    # پاسخ به سطوح قدرت
    elif data.startswith("strength_"):
        level = data.split("_")[1]
        levels = {
            "beginner": "برنامه مبتدی: ۳ جلسه در هفته، تمرینات پایه",
            "intermediate": "برنامه متوسط: ۴ جلسه در هفته، تمرینات ترکیبی",
            "advanced": "برنامه حرفه‌ای: ۵ جلسه در هفته، تمرینات پیشرفته"
        }
        await callback_query.message.answer(f"💪 {levels.get(level, 'برنامه انتخابی')}")
    
    await callback_query.answer()

# ==================== قسمت جدید برای Health Check ====================

async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_health_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Health check server started on port {PORT}")

async def on_startup_polling(dp):
    await start_health_server()
    logger.info("Bot started with polling mode")

# ==================== اجرای اصلی ====================

if __name__ == "__main__":
    # اجرا با Polling به جای Webhook
    executor.start_polling(
        dp,
        on_startup=on_startup_polling,
        skip_updates=True
    )
