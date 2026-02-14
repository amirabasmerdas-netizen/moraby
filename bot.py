import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.executor import start_webhook
from datetime import datetime
import json

import config
from database import Database
from workout_analyzer import WorkoutAnalyzer
from ai_analyzer import AIAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Initialize components
db = Database(config.DATABASE_URL)
analyzer = WorkoutAnalyzer()
ai_analyzer = AIAnalyzer()

# Store temporary user data
user_temp = {}

# Reply keyboards
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

def get_inline_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("🔥 سخت‌ترش کن", callback_data="harder"),
        InlineKeyboardButton("🧊 سبک‌ترش کن", callback_data="easier"),
        InlineKeyboardButton("⏱ تنظیم استراحت", callback_data="rest")
    )
    keyboard.add(
        InlineKeyboardButton("📋 ذخیره تمرین", callback_data="save"),
        InlineKeyboardButton("📤 خروجی PDF", callback_data="pdf"),
        InlineKeyboardButton("🔄 بازنویسی حرفه‌ای", callback_data="rewrite")
    )
    return keyboard

# Handlers
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user = message.from_user
    await db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome_text = """
🏋️‍♂️ به مربی شخصی هوشمند خوش آمدید! 🤖

من اینجام تا بهت کمک کنم تمریناتت رو حرفه‌ای‌تر کنی و به هدفت برسی.

🔥 چیکار می‌تونم برات انجام بدم؟
• تحلیل هوشمند برنامه تمرینیت
• محاسبه شدت و کالری مصرفی
• پیشنهاد زمان استراحت اصولی
• تشخیص تمرین نامتعادل
• ارائه نسخه پیشرفته تمرین

📝 برای شروع، یکی از گزینه‌های زیر رو انتخاب کن یا برنامه تمرینیت رو برام بفرست!
    """
    
    await message.reply(welcome_text, reply_markup=get_main_keyboard())

@dp.message_handler(lambda message: message.text == "🏋 ثبت برنامه تمرینی")
async def enter_workout(message: types.Message):
    user_temp[message.from_user.id] = {'state': 'waiting_workout'}
    
    await message.reply(
        "📝 برنامه تمرینیت رو برام بنویس.\n\n"
        "مثال:\n"
        "دراز نشست=۲۰\n"
        "شنا=۱۰\n"
        "اسکات=۵\n"
        "طناب=۳ دقیقه\n\n"
        "می‌تونی با = یا : مقادیر رو مشخص کنی.",
        reply_markup=get_main_keyboard()
    )

@dp.message_handler(lambda message: message.text == "📊 تحلیل تمرین من")
async def show_history(message: types.Message):
    workouts = await db.get_user_workouts(message.from_user.id, limit=5)
    
    if not workouts:
        await message.reply("📭 شما هنوز تمرینی ثبت نکرده‌اید. با گزینه 'ثبت برنامه تمرینی' شروع کنید.")
        return
    
    text = "📊 آخرین تمرینات شما:\n\n"
    for i, w in enumerate(workouts, 1):
        text += f"{i}. {w.workout_date.strftime('%Y/%m/%d')} - {w.workout_type} - {w.calories_burned} کالری\n"
    
    await message.reply(text)

@dp.message_handler(lambda message: message.text == "⚡ ارتقای تمرین")
async def upgrade_workout(message: types.Message):
    await message.reply(
        "⚡ برای ارتقای تمرین، ابتدا برنامه تمرینیت رو ثبت کن.\n"
        "بعد از تحلیل، می‌تونی با دکمه 'سخت‌ترش کن' نسخه پیشرفته رو دریافت کنی."
    )

@dp.message_handler(lambda message: message.text == "🧠 راهنمای تمرین اصولی")
async def training_guide(message: types.Message):
    guide = """
🧠 *راهنمای تمرین اصولی*

🔹 *قانون اضافه‌بار پیشرونده*
هر هفته ۵-۱۰٪ به حجم یا شدت تمرین اضافه کن

🔹 *تنوع در تمرین*
هر ۴-۶ هفته تمریناتت رو تغییر بده

🔹 *استراحت کافی*
بین تمرینات قدرتی: ۴۸-۷۲ ساعت استراحت
بین تمرینات هوازی: ۲۴-۴۸ ساعت استراحت

🔹 *تغذیه مناسب*
• پروتئین: ۱.۶-۲.۲ گرم به ازای هر کیلو وزن
• آب: ۳۰-۳۵ میلی‌لیتر به ازای هر کیلو وزن

🔹 *گرم کردن و سرد کردن*
• گرم کردن: ۵-۱۰ دقیقه قبل از تمرین
• سرد کردن: ۵-۱۰ دقیقه بعد از تمرین
    """
    
    await message.reply(guide, parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(lambda message: message.text == "⚙ تنظیمات")
async def settings(message: types.Message):
    user_settings = await db.get_user_settings(message.from_user.id)
    
    settings_text = f"""
⚙ *تنظیمات*

🔔 یادآور استراحت: {'✅' if user_settings.get('rest_reminder', True) else '❌'}
💧 یادآور آب: {'✅' if user_settings.get('water_reminder', True) else '❌'}
📊 سطح تناسب اندام: {user_settings.get('fitness_level', 'مبتدی')}

برای تغییر، گزینه مورد نظر رو انتخاب کن:
    """
    
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("یادآور استراحت 🔔", callback_data="toggle_rest"),
        InlineKeyboardButton("یادآور آب 💧", callback_data="toggle_water"),
        InlineKeyboardButton("سطح مبتدی", callback_data="level_مبتدی"),
        InlineKeyboardButton("سطح متوسط", callback_data="level_متوسط"),
        InlineKeyboardButton("سطح حرفه‌ای", callback_data="level_حرفه‌ای")
    )
    
    await message.reply(settings_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

@dp.message_handler()
async def analyze_workout(message: types.Message):
    user_id = message.from_user.id
    workout_text = message.text
    
    # Check if user is in waiting state
    if user_id in user_temp and user_temp[user_id].get('state') == 'waiting_workout':
        del user_temp[user_id]
        
        # Show typing indicator
        await bot.send_chat_action(user_id, 'typing')
        
        # Parse exercises
        exercises = analyzer.parse_workout(workout_text)
        
        if not exercises:
            await message.reply(
                "❌ تمرینی تشخیص داده نشد!\n\n"
                "لطفاً به این فرمت بنویسید:\n"
                "دراز نشست=۲۰\n"
                "شنا=۱۰\n"
                "اسکات=۵"
            )
            return
        
        # Analyze workout
        analysis = analyzer.analyze_workout(exercises)
        
        # Try AI analysis if available
        if ai_analyzer.use_ai:
            ai_result = await ai_analyzer.analyze_text(workout_text)
            if ai_result.get('using_ai'):
                # Merge AI analysis with basic analysis
                analysis.update(ai_result)
        
        # Calculate total calories
        total_calories = analysis.get('total_calories', 0)
        
        # Save to database
        await db.save_workout(
            user_id=user_id,
            workout_text=workout_text,
            workout_type=analysis['workout_type'],
            intensity=analysis['intensity'],
            calories=total_calories,
            analysis=analysis
        )
        
        # Format response
        response = f"""
🔥 *تحلیل تمرین شما*

📋 *تمرینات ثبت شده:*
"""
        for ex in analysis['exercises']:
            unit = f" {ex['unit']}" if ex.get('unit') else " تکرار"
            response += f"• {ex['original_name']}: {ex['value']}{unit}\n"

        response += f"""
🎯 *هدف احتمالی:* {analysis['goal']}
📊 *نوع تمرین:* {analysis['workout_type']}
💪 *شدت:* {analysis['intensity']}
🏋️‍♂️ *سطح:* {analysis['fitness_level']}

🔥 *کالری مصرفی تقریبی:* {total_calories} کالری
⏱ *زمان استراحت پیشنهادی:* {analysis['rest_time']} ثانیه بین حرکات
💧 *زمان نوشیدن آب:* هر {analysis['water_break']} دقیقه

📈 *عضلات درگیر:* {', '.join(analysis['muscle_groups'])}

📝 *پیشنهاد ارتقا:* 
{analysis['improvement_suggestion']}
"""

        if analysis.get('imbalance'):
            response += f"\n⚠️ *عدم تعادل:* {analysis['imbalance']}"

        if analysis.get('overtraining_risk'):
            response += f"\n{analysis['overtraining_risk']}"

        if analysis.get('recovery_version'):
            response += f"\n🔄 *نسخه ریکاوری:*\n{analysis['recovery_version']}"

        # Add motivational message based on intensity
        if analysis['intensity'] == 'زیاد':
            response += "\n💪 عالی! تمرین چالش‌برانگیزی داری. به خودت افتخار کن!"
        elif analysis['intensity'] == 'متوسط':
            response += "\n👍 تمرین خوبیه! می‌تونی کم‌کم شدتش رو بیشتر کنی."
        else:
            response += "\n🌟 شروع عالی! با استمرار به نتایج خوب می‌رسی."

        # Store analysis for inline actions
        user_temp[user_id] = {'analysis': analysis}
        
        await message.reply(response, reply_markup=get_inline_keyboard(), parse_mode=ParseMode.MARKDOWN)
    else:
        # If not in waiting state, prompt to register workout
        await message.reply(
            "لطفاً ابتدا گزینه 'ثبت برنامه تمرینی' رو انتخاب کن.",
            reply_markup=get_main_keyboard()
        )

@dp.callback_query_handler(lambda c: True)
async def inline_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.callback_data
    
    if data == "harder":
        if user_id in user_temp and 'analysis' in user_temp[user_id]:
            analysis = user_temp[user_id]['analysis']
            
            # Generate harder version
            harder_text = "🔥 *نسخه سخت‌تر تمرین:*\n\n"
            
            for ex in analysis['exercises']:
                new_value = int(ex['value'] * 1.3)  # 30% increase
                unit = f" {ex['unit']}" if ex.get('unit') else " تکرار"
                harder_text += f"• {ex['original_name']}: {new_value}{unit}\n"
            
            harder_text += f"\n⏱ استراحت: {int(analysis['rest_time'] * 0.8)} ثانیه (کمتر)"
            harder_text += "\n\n⚠️ این نسخه چالش‌برانگیزتر است. به فرم صحیح توجه کن!"
            
            await bot.send_message(user_id, harder_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await bot.send_message(user_id, "❌ ابتدا یک تمرین را تحلیل کن.")
    
    elif data == "easier":
        if user_id in user_temp and 'analysis' in user_temp[user_id]:
            analysis = user_temp[user_id]['analysis']
            
            # Generate easier version
            easier_text = "🧊 *نسخه سبک‌تر تمرین:*\n\n"
            
            for ex in analysis['exercises']:
                new_value = int(ex['value'] * 0.7)  # 30% decrease
                unit = f" {ex['unit']}" if ex.get('unit') else " تکرار"
                easier_text += f"• {ex['original_name']}: {new_value}{unit}\n"
            
            easier_text += f"\n⏱ استراحت: {int(analysis['rest_time'] * 1.3)} ثانیه (بیشتر)"
            easier_text += "\n\n👍 نسخه مناسب برای شروع یا ریکاوری."
            
            await bot.send_message(user_id, easier_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await bot.send_message(user_id, "❌ ابتدا یک تمرین را تحلیل کن.")
    
    elif data == "rest":
        await bot.send_message(
            user_id,
            "⏱ *تنظیم زمان استراحت*\n\n"
            "استراحت اصولی بین ست‌ها:\n"
            "• قدرتی: ۶۰-۹۰ ثانیه\n"
            "• استقامتی: ۳۰-۴۵ ثانیه\n"
            "• هایپرتروفی: ۴۵-۶۰ ثانیه\n"
            "• قدرتی سنگین: ۲-۳ دقیقه"
        )
    
    elif data == "save":
        await bot.send_message(
            user_id,
            "✅ تمرین در تاریخچه شما ذخیره شد.\n"
            "برای مشاهده تاریخچه از گزینه 'تحلیل تمرین من' استفاده کن."
        )
    
    elif data == "pdf":
        await bot.send_message(
            user_id,
            "📤 قابلیت خروجی PDF به زودی اضافه خواهد شد!"
        )
    
    elif data == "rewrite":
        if user_id in user_temp and 'analysis' in user_temp[user_id]:
            analysis = user_temp[user_id]['analysis']
            
            rewrite_text = "🔄 *بازنویسی حرفه‌ای تمرین:*\n\n"
            rewrite_text += "تمرین شما به شکل اصولی‌تر:\n\n"
            
            # Group exercises by category
            strength_ex = []
            cardio_ex = []
            
            for ex in analysis['exercises']:
                if analyzer.exercise_database.get(ex['name'], {}).get('type') == 'قدرتی':
                    strength_ex.append(ex)
                else:
                    cardio_ex.append(ex)
            
            if strength_ex:
                rewrite_text += "*حرکات قدرتی (۳ ست):*\n"
                for ex in strength_ex:
                    rewrite_text += f"• {ex['original_name']}: {ex['value']} تکرار\n"
                rewrite_text += "\n"
            
            if cardio_ex:
                rewrite_text += "*حرکات هوازی (۲ ست):*\n"
                for ex in cardio_ex:
                    rewrite_text += f"• {ex['original_name']}: {ex['value']} دقیقه\n"
            
            rewrite_text += "\n⏱ استراحت: ۴۵ ثانیه بین ست‌ها"
            
            await bot.send_message(user_id, rewrite_text, parse_mode=ParseMode.MARKDOWN)
    
    # Settings toggles
    elif data.startswith("toggle_"):
        setting = data.replace("toggle_", "")
        user_settings = await db.get_user_settings(user_id)
        
        if setting == "rest":
            user_settings['rest_reminder'] = not user_settings.get('rest_reminder', True)
        elif setting == "water":
            user_settings['water_reminder'] = not user_settings.get('water_reminder', True)
        
        await db.update_user_settings(user_id, user_settings)
        await bot.answer_callback_query(callback_query.id, text="تنظیمات به‌روزرسانی شد")
    
    elif data.startswith("level_"):
        level = data.replace("level_", "")
        await db.update_fitness_level(user_id, level)
        await bot.answer_callback_query(callback_query.id, text=f"سطح به {level} تغییر یافت")

@dp.message_handler()
async def fallback(message: types.Message):
    await message.reply(
        "❌ دستور نامعتبر!\n"
        "لطفاً از منوی اصلی استفاده کنید.",
        reply_markup=get_main_keyboard()
    )

async def on_startup(dp):
    logging.info("Starting bot...")
    await bot.set_webhook(config.WEBHOOK_URL + config.WEBHOOK_PATH)

async def on_shutdown(dp):
    logging.info("Shutting down...")
    await bot.delete_webhook()

if __name__ == '__main__':
    if config.WEBHOOK_URL:
        start_webhook(
            dispatcher=dp,
            webhook_path=config.WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=config.WEBAPP_HOST,
            port=config.WEBAPP_PORT
        )
    else:
        from aiogram import executor
        executor.start_polling(dp, skip_updates=True)
