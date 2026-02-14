import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self):
        self.exercise_keywords = {
            "شنا": ["شنا", "شنای", "push up", "pushup"],
            "دراز نشست": ["دراز نشست", "درازنشست", "sit up", "situp"],
            "اسکات": ["اسکات", "squat"],
            "طناب": ["طناب", "طناب زدن", "skipping"],
            "دویدن": ["دویدن", "دو", "running", "run"],
            "پلانک": ["پلانک", "plank"],
            "بارفیکس": ["بارفیکس", "pull up", "pullup"],
            "پرس سینه": ["پرس سینه", "chest press"],
        }
    
    def analyze_text(self, text: str) -> Dict:
        """تحلیل متن با هوش مصنوعی ساده"""
        analysis = {
            "exercises": [],
            "estimated_level": "مبتدی",
            "focus_areas": [],
            "suggestions": [],
            "warnings": []
        }
        
        # تشخیص تمرینات
        lines = text.strip().split('\n')
        for line in lines:
            exercise = self._extract_exercise(line)
            if exercise:
                analysis["exercises"].append(exercise)
        
        # تشخیص سطح
        analysis["estimated_level"] = self._estimate_level(analysis["exercises"])
        
        # تشخیص نواحی تمرکز
        analysis["focus_areas"] = self._detect_focus_areas(analysis["exercises"])
        
        # پیشنهادات هوشمند
        analysis["suggestions"] = self._generate_suggestions(analysis)
        
        # هشدارها
        analysis["warnings"] = self._generate_warnings(analysis)
        
        return analysis
    
    def _extract_exercise(self, text: str) -> Dict:
        """استخراج اطلاعات تمرین از متن"""
        exercise = {}
        
        # تشخیص نام تمرین
        for ex_name, keywords in self.exercise_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    exercise["name"] = ex_name
                    break
            if exercise.get("name"):
                break
        
        if not exercise.get("name"):
            # تشخیص نام‌های فارسی عمومی
            match = re.search(r'([\u0600-\u06FF\s]+)', text)
            if match:
                exercise["name"] = match.group(1).strip()
        
        # تشخیص تعداد/زمان
        value_match = re.search(r'[=:]?\s*(\d+)\s*(دقیقه|ثانیه|تکرار|بار)?', text)
        if value_match:
            exercise["value"] = int(value_match.group(1))
            exercise["unit"] = value_match.group(2) if value_match.group(2) else "تکرار"
        else:
            exercise["value"] = 0
            exercise["unit"] = "تکرار"
        
        return exercise
    
    def _estimate_level(self, exercises: List[Dict]) -> str:
        """تخمین سطح کاربر"""
        if not exercises:
            return "مبتدی"
        
        total_count = sum(ex.get("value", 0) for ex in exercises)
        difficult_moves = sum(1 for ex in exercises if ex.get("name") in ["بارفیکس", "پرس سینه", "ددلیفت"])
        
        if total_count > 100 or difficult_moves > 3:
            return "حرفه‌ای"
        elif total_count > 50 or difficult_moves > 1:
            return "متوسط"
        else:
            return "مبتدی"
    
    def _detect_focus_areas(self, exercises: List[Dict]) -> List[str]:
        """تشخیص نواحی تمرکز"""
        areas = []
        for ex in exercises:
            name = ex.get("name", "")
            if "شنا" in name or "پرس" in name or "بارفیکس" in name:
                if "بالاتنه" not in areas:
                    areas.append("بالاتنه")
            elif "اسکات" in name or "ددلیفت" in name:
                if "پایین‌تنه" not in areas:
                    areas.append("پایین‌تنه")
            elif "پلانک" in name or "کرانچ" in name:
                if "میان‌تنه" not in areas:
                    areas.append("میان‌تنه")
        
        return areas if areas else ["عمومی"]
    
    def _generate_suggestions(self, analysis: Dict) -> List[str]:
        """تولید پیشنهادات هوشمند"""
        suggestions = []
        exercises = analysis.get("exercises", [])
        
        if len(exercises) < 3:
            suggestions.append("می‌تونی تنوع تمریناتت رو بیشتر کنی")
        
        focus_areas = analysis.get("focus_areas", [])
        if len(focus_areas) == 1:
            suggestions.append(f"پیشنهاد می‌کنم تمرینات {focus_areas[0]} رو با تمرینات مکمل ترکیب کنی")
        
        has_cardio = any("طناب" in ex.get("name", "") or "دویدن" in ex.get("name", "") for ex in exercises)
        if not has_cardio:
            suggestions.append("اضافه کردن یک تمرین هوازی کوتاه می‌تونه چربی‌سوزی رو افزایش بده")
        
        return suggestions
    
    def _generate_warnings(self, analysis: Dict) -> List[str]:
        """تولید هشدارها"""
        warnings = []
        exercises = analysis.get("exercises", [])
        
        for ex in exercises:
            if ex.get("value", 0) > 50 and ex.get("unit") == "تکرار":
                warnings.append(f"⚠ تعداد {ex.get('name')} خیلی بالاست - مراقب آسیب باش")
        
        return warnings
    
    def generate_pro_version(self, exercises: List[Dict], level: str) -> str:
        """تولید نسخه پیشرفته تمرین"""
        pro_version = []
        
        for ex in exercises:
            name = ex.get("name", "")
            value = ex.get("value", 0)
            unit = ex.get("unit", "تکرار")
            
            if level == "مبتدی":
                pro_version.append(f"{name} = {value + 5} {unit}")
            elif level == "متوسط":
                pro_version.append(f"{name} = {value + 8} {unit}")
            else:
                pro_version.append(f"{name} = {value + 12} {unit}")
            
            # اضافه کردن تنوع
            if "شنا" in name:
                pro_version.append(f"شنا دست باز = {max(5, value//3)} تکرار")
            elif "اسکات" in name:
                pro_version.append(f"اسکات پرشی = {max(5, value//4)} تکرار")
        
        return "\n".join(pro_version)
