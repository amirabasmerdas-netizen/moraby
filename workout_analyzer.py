import re
import math
from typing import Dict, List, Tuple

class WorkoutAnalyzer:
    def __init__(self):
        self.exercise_database = {
            'دراز نشست': {'type': 'قدرتی', 'category': 'مرکزی', 'difficulty': 3, 'calories_per_rep': 0.3},
            'شنا': {'type': 'قدرتی', 'category': 'بالاتنه', 'difficulty': 4, 'calories_per_rep': 0.5},
            'اسکات': {'type': 'قدرتی', 'category': 'پایین تنه', 'difficulty': 5, 'calories_per_rep': 0.8},
            'طناب': {'type': 'هوازی', 'category': 'تمام بدن', 'difficulty': 6, 'calories_per_minute': 10},
            'برپی': {'type': 'هوازی', 'category': 'تمام بدن', 'difficulty': 8, 'calories_per_rep': 1.5},
            'لانگز': {'type': 'قدرتی', 'category': 'پایین تنه', 'difficulty': 4, 'calories_per_rep': 0.7},
            'پلانک': {'type': 'قدرتی', 'category': 'مرکزی', 'difficulty': 5, 'calories_per_minute': 5},
            'دوچرخه': {'type': 'هوازی', 'category': 'پایین تنه', 'difficulty': 5, 'calories_per_minute': 8},
            'کرانچ': {'type': 'قدرتی', 'category': 'مرکزی', 'difficulty': 2, 'calories_per_rep': 0.2},
            'پشت بازو': {'type': 'قدرتی', 'category': 'بالاتنه', 'difficulty': 3, 'calories_per_rep': 0.4},
        }
        
    def parse_workout(self, text: str) -> List[Dict]:
        """Parse user input and extract exercises"""
        exercises = []
        lines = text.strip().split('\n')
        
        for line in lines:
            # Patterns: exercise=value or exercise=value unit
            patterns = [
                r'([\u0600-\u06FF\s]+)=(\d+)\s*(دقیقه|ثانیه)?',
                r'([\u0600-\u06FF\s]+):\s*(\d+)\s*(دقیقه|ثانیه)?',
                r'([\u0600-\u06FF\s]+)\s+(\d+)\s*(تکرار|دقیقه|ثانیه)?'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    exercise_name = match.group(1).strip()
                    value = int(match.group(2))
                    unit = match.group(3) if len(match.groups()) > 2 else None
                    
                    # Find best matching exercise in database
                    exercise_key = self._find_exercise(exercise_name)
                    
                    exercises.append({
                        'name': exercise_key or exercise_name,
                        'value': value,
                        'unit': unit,
                        'original_name': exercise_name
                    })
                    break
        
        return exercises
    
    def _find_exercise(self, name: str) -> str:
        """Find closest matching exercise in database"""
        for exercise in self.exercise_database:
            if exercise in name or name in exercise:
                return exercise
        return None
    
    def analyze_workout(self, exercises: List[Dict]) -> Dict:
        """Analyze workout and return detailed analysis"""
        if not exercises:
            return {'error': 'تمرینی یافت نشد'}
        
        total_calories = 0
        workout_types = []
        muscle_groups = []
        total_difficulty = 0
        
        for ex in exercises:
            ex_name = ex['name']
            if ex_name in self.exercise_database:
                data = self.exercise_database[ex_name]
                workout_types.append(data['type'])
                muscle_groups.append(data['category'])
                
                # Calculate calories
                if ex['unit'] == 'دقیقه':
                    calories = data.get('calories_per_minute', 5) * ex['value']
                else:
                    calories = data.get('calories_per_rep', 0.5) * ex['value']
                
                total_calories += calories
                total_difficulty += data['difficulty'] * (ex['value'] / 10)
        
        # Determine workout type
        if workout_types:
            main_type = max(set(workout_types), key=workout_types.count)
        else:
            main_type = 'ترکیبی'
        
        # Determine intensity
        avg_difficulty = total_difficulty / len(exercises) if exercises else 0
        if avg_difficulty < 3:
            intensity = 'کم'
            level = 'مبتدی'
        elif avg_difficulty < 6:
            intensity = 'متوسط'
            level = 'متوسط'
        else:
            intensity = 'زیاد'
            level = 'حرفه‌ای'
        
        # Calculate rest time
        rest_time = self._calculate_rest_time(intensity, workout_types)
        
        # Check for imbalance
        imbalance = self._check_imbalance(muscle_groups)
        
        # Calculate workout goal
        goal = self._determine_goal(workout_types, intensity, total_calories)
        
        # Check for overtraining
        overtraining_risk = self._check_overtraining(total_difficulty, len(exercises))
        
        return {
            'exercises': exercises,
            'workout_type': main_type,
            'intensity': intensity,
            'fitness_level': level,
            'total_calories': round(total_calories, 1),
            'muscle_groups': list(set(muscle_groups)),
            'rest_time': rest_time,
            'water_break': self._calculate_water_break(len(exercises)),
            'goal': goal,
            'imbalance': imbalance,
            'overtraining_risk': overtraining_risk,
            'improvement_suggestion': self._generate_improvement(exercises, main_type),
            'recovery_version': self._generate_recovery(exercises, main_type) if intensity == 'زیاد' else None
        }
    
    def _calculate_rest_time(self, intensity: str, workout_types: List[str]) -> int:
        """Calculate recommended rest time between exercises"""
        if 'قدرتی' in workout_types:
            base_rest = 60  # seconds
        else:
            base_rest = 30  # seconds
        
        if intensity == 'کم':
            return base_rest
        elif intensity == 'متوسط':
            return base_rest * 1.5
        else:
            return base_rest * 2
    
    def _calculate_water_break(self, num_exercises: int) -> int:
        """Calculate when to take water breaks"""
        return max(15, math.ceil(num_exercises / 3) * 15)  # minutes
    
    def _check_imbalance(self, muscle_groups: List[str]) -> str:
        """Check if workout is imbalanced"""
        if not muscle_groups:
            return None
        
        upper_count = muscle_groups.count('بالاتنه')
        lower_count = muscle_groups.count('پایین تنه')
        core_count = muscle_groups.count('مرکزی')
        
        if upper_count > lower_count * 2 and lower_count > 0:
            return "تمرین شما بیشتر روی بالاتنه متمرکز است. پیشنهاد می‌شود تمرینات پایین تنه را نیز اضافه کنید."
        elif lower_count > upper_count * 2 and upper_count > 0:
            return "تمرین شما بیشتر روی پایین تنه متمرکز است. پیشنهاد می‌شود تمرینات بالاتنه را نیز اضافه کنید."
        elif core_count == 0 and (upper_count > 0 or lower_count > 0):
            return "تمرینات مرکزی بدن (کرانچ، پلانک) را برای تعادل بیشتر اضافه کنید."
        
        return None
    
    def _determine_goal(self, workout_types: List[str], intensity: str, calories: float) -> str:
        """Determine the likely goal of the workout"""
        if calories > 300:
            return "چربی‌سوزی"
        elif 'قدرتی' in workout_types and intensity == 'زیاد':
            return "افزایش قدرت"
        elif 'هوازی' in workout_types and workout_types.count('هوازی') > len(workout_types)/2:
            return "استقامتی"
        elif intensity == 'کم':
            return "حفظ سلامتی و فعال ماندن"
        else:
            return "ترکیبی (چربی‌سوزی و قدرتی)"
    
    def _check_overtraining(self, difficulty: float, num_exercises: int) -> str:
        """Check for overtraining risk"""
        if difficulty > 50 or num_exercises > 10:
            return "⚠️ خطر تمرین بیش از حد! به بدن خود استراحت کافی بدهید."
        elif difficulty > 30 or num_exercises > 6:
            return "⚠️ حجم تمرین نسبتاً بالاست. به علائم خستگی توجه کنید."
        return None
    
    def _generate_improvement(self, exercises: List[Dict], workout_type: str) -> str:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Add compound movement if missing
        has_compound = any(ex['name'] in ['اسکات', 'شنا', 'برپی'] for ex in exercises)
        if not has_compound:
            suggestions.append("اضافه کردن یک حرکت ترکیبی مانند اسکات یا شنا")
        
        # Progressive overload
        suggestions.append("افزایش تدریجی تعداد تکرارها یا ست‌ها در هفته")
        
        # Variation
        if workout_type == 'قدرتی':
            suggestions.append("تنوع در زاویه و نوع حرکات برای درگیری بیشتر عضلات")
        
        return " - ".join(suggestions[:2])
    
    def _generate_recovery(self, exercises: List[Dict], workout_type: str) -> str:
        """Generate recovery version for intense workouts"""
        recovery_exercises = []
        for ex in exercises[:3]:  # Take first 3 exercises
            recovery_exercises.append(f"{ex['name']}: {max(5, ex['value']//2)} تکرار")
        
        recovery_text = "نسخه ریکاوری: " + " - ".join(recovery_exercises)
        recovery_text += "\n💧 تمرین سبک‌تر با ۵۰٪ حجم و استراحت بیشتر بین ست‌ها"
        
        return recovery_text
