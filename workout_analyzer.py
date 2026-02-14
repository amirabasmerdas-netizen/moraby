import re
import math
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class WorkoutAnalyzer:
    def __init__(self):
        self.exercise_categories = {
            "قدرتی": ["شنا", "دراز نشست", "اسکات", "پرس سینه", "پشت بازو", "جلو بازو", "ددلیفت", "بارفیکس"],
            "هوازی": ["دویدن", "طناب", "پرش", "دوچرخه", "شناوری", "پله"],
            "مرکزی": ["پلانک", "کرانچ", "پروانه", "کوهنوردی", "پل باسن"],
            "کششی": ["کشش", "یوگا", "حرکت کششی", "نرمش"]
        }
        
        self.difficulty_levels = {
            "مبتدی": {"min_volume": 0, "max_volume": 50},
            "متوسط": {"min_volume": 51, "max_volume": 100},
            "حرفه‌ای": {"min_volume": 101, "max_volume": 999}
        }
    
    def parse_workout(self, text: str) -> List[Dict]:
        """پارس کردن متن تمرین و استخراج حرکات"""
        exercises = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # تشخیص الگوهای مختلف
            patterns = [
                r'([\u0600-\u06FF\s]+)[=:](\d+)(?:\s*(دقیقه|ثانیه|تکرار|بار))?',
                r'([\u0600-\u06FF\s]+)\s+(\d+)\s*(دقیقه|ثانیه|تکرار|بار)?',
                r'طناب\s*=\s*(\d+)\s*(دقیقه)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    name = match.group(1).strip()
                    value = int(match.group(2))
                    unit = match.group(3) if len(match.groups()) > 2 else 'تکرار'
                    
                    exercises.append({
                        'name': name,
                        'value': value,
                        'unit': unit if unit else 'تکرار',
                        'category': self._get_category(name)
                    })
                    break
        
        return exercises
    
    def _get_category(self, exercise_name: str) -> str:
        """تشخیص دسته تمرین"""
        for category, exercises in self.exercise_categories.items():
            for ex in exercises:
                if ex in exercise_name:
                    return category
        return "سایر"
    
    def calculate_volume(self, exercises: List[Dict]) -> int:
        """محاسبه حجم کل تمرین"""
        total_volume = 0
        for ex in exercises:
            if ex['unit'] == 'دقیقه':
                total_volume += ex['value'] * 2  # هر دقیقه معادل ۲ تکرار
            else:
                total_volume += ex['value']
        return total_volume
    
    def calculate_calories(self, exercises: List[Dict], weight: int = 70) -> int:
        """محاسبه کالری تقریبی مصرفی"""
        total_calories = 0
        met_values = {
            "قدرتی": 5.0,
            "هوازی": 8.0,
            "مرکزی": 3.5,
            "کششی": 2.5,
            "سایر": 4.0
        }
        
        for ex in exercises:
            met = met_values.get(ex['category'], 4.0)
            if ex['unit'] == 'دقیقه':
                duration = ex['value']
            else:
                duration = ex['value'] * 0.5  # هر تکرار حدود ۰.۵ دقیقه
            
            calories = (met * 3.5 * weight * duration) / 200
            total_calories += calories
        
        return round(total_calories)
    
    def detect_goal(self, exercises: List[Dict], volume: int) -> str:
        """تشخیص هدف تمرین"""
        categories = [ex['category'] for ex in exercises]
        
        if "هوازی" in categories and volume > 50:
            return "چربی‌سوزی 🔥"
        elif "قدرتی" in categories and any(ex['value'] > 12 for ex in exercises if ex['unit'] != 'دقیقه'):
            return "قدرتی 💪"
        elif "مرکزی" in categories:
            return "تقویت میان‌تنه 🎯"
        elif volume > 100:
            return "استقامتی ⚡"
        elif volume < 30:
            return "عمومی/سبک 🌱"
        else:
            return "ترکیبی (چندمنظوره) 🏆"
    
    def estimate_difficulty(self, volume: int) -> str:
        """تخمین سطح سختی"""
        if volume <= 30:
            return "مبتدی"
        elif volume <= 70:
            return "متوسط"
        else:
            return "حرفه‌ای"
    
    def suggest_rest_time(self, exercises: List[Dict], difficulty: str) -> int:
        """پیشنهاد زمان استراحت"""
        base_rest = {
            "مبتدی": 60,
            "متوسط": 45,
            "حرفه‌ای": 30
        }
        
        has_powerful = any(ex['name'] in ["اسکات", "شنا", "دراز نشست"] for ex in exercises)
        if has_powerful:
            base_rest[difficulty] += 15
        
        return base_rest.get(difficulty, 45)
    
    def detect_imbalance(self, exercises: List[Dict]) -> List[str]:
        """تشخیص عدم تعادل در تمرین"""
        warnings = []
        upper_body = 0
        lower_body = 0
        core = 0
        
        upper_ex = ["شنا", "پرس", "بارفیکس", "پشت بازو", "جلو بازو"]
        lower_ex = ["اسکات", "ددلیفت", "لانگز"]
        core_ex = ["پلانک", "کرانچ", "دراز نشست"]
        
        for ex in exercises:
            if any(u in ex['name'] for u in upper_ex):
                upper_body += ex['value']
            if any(l in ex['name'] for l in lower_ex):
                lower_body += ex['value']
            if any(c in ex['name'] for c in core_ex):
                core += ex['value']
        
        if upper_body > 0 and lower_body == 0:
            warnings.append("تمرین فقط بالاتنه - بهتره حرکات پایین‌تنه هم اضافه کنی")
        if lower_body > 0 and upper_body == 0:
            warnings.append("تمرین فقط پایین‌تنه - بهتره حرکات بالاتنه هم اضافه کنی")
        if core == 0:
            warnings.append("هیچ حرکت مرکزی نداری - پیشنهاد می‌کنم پلانک یا کرانچ اضافه کنی")
        
        return warnings
    
    def suggest_improvement(self, exercises: List[Dict], difficulty: str) -> str:
        """پیشنهاد بهبود تمرین"""
        suggestions = []
        
        # پیشنهاد افزایش تنوع
        categories = set(ex['category'] for ex in exercises)
        if len(categories) < 2:
            suggestions.append("برای نتیجه بهتر، تمرینات متنوع‌تری انجام بده")
        
        # پیشنهاد افزایش حجم
        if difficulty == "مبتدی":
            suggestions.append("می‌تونی هر هفته ۱۰٪ به تعداد تکرارها اضافه کنی")
        elif difficulty == "متوسط":
            suggestions.append("اضافه کردن وزنه یا افزایش تعداد ست‌ها رو در نظر بگیر")
        
        # پیشنهاد تنظیم زمان
        if any(ex['unit'] == 'دقیقه' for ex in exercises):
            suggestions.append("تمرینات هوازی رو می‌تونی به صورت اینتروال انجام بدی")
        
        return "\n".join(suggestions) if suggestions else "تمرین خوبی داری! ادامه بده"
    
    def check_overtraining(self, exercises: List[Dict], user_level: str) -> List[str]:
        """بررسی تمرین بیش از حد"""
        warnings = []
        volume = self.calculate_volume(exercises)
        
        max_volumes = {
            "مبتدی": 50,
            "متوسط": 100,
            "حرفه‌ای": 200
        }
        
        max_vol = max_volumes.get(user_level, 50)
        
        if volume > max_vol:
            warnings.append(f"⚠ حجم تمرین بالاست! برای سطح {user_level}، حجم مناسب حداکثر {max_vol} هست")
        
        # بررسی حرکات سنگین متوالی
        consecutive_hard = 0
        for ex in exercises:
            if ex['value'] > 20 and ex['unit'] == 'تکرار':
                consecutive_hard += 1
                if consecutive_hard > 3:
                    warnings.append("چند حرکت سنگین پشت سر هم داری - به بدنت استراحت بده")
        
        return warnings
