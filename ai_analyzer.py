import aiohttp
import json
from typing import Dict, List
import config

class AIAnalyzer:
    def __init__(self):
        self.api_key = config.OPENAI_API_KEY
        self.use_ai = bool(self.api_key)
    
    async def analyze_text(self, text: str) -> Dict:
        """Use AI to analyze workout text if API key is available"""
        if not self.use_ai:
            return {'using_ai': False}
        
        try:
            prompt = f"""
            لطفاً این برنامه تمرینی را تحلیل کن و اطلاعات زیر را به صورت JSON برگردان:
            متن تمرین: {text}
            
            ساختار JSON مورد نظر:
            {{
                "exercises": [{{"name": "نام حرکت", "count": عدد, "unit": "واحد"}}],
                "workout_type": "نوع تمرین",
                "intensity": "شدت (کم/متوسط/زیاد)",
                "fitness_level": "سطح (مبتدی/متوسط/حرفه‌ای)",
                "total_calories": عدد,
                "muscle_groups": ["گروه‌های عضلانی"],
                "rest_time": عدد (به ثانیه),
                "goal": "هدف تمرین",
                "recommendations": ["توصیه‌ها"]
            }}
            """
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json'
                    },
                    json={
                        'model': 'gpt-3.5-turbo',
                        'messages': [
                            {'role': 'system', 'content': 'You are a professional fitness coach.'},
                            {'role': 'user', 'content': prompt}
                        ],
                        'temperature': 0.7
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        ai_response = data['choices'][0]['message']['content']
                        # Extract JSON from response
                        import re
                        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                        if json_match:
                            result = json.loads(json_match.group())
                            result['using_ai'] = True
                            return result
        except Exception as e:
            print(f"AI Analysis error: {e}")
        
        return {'using_ai': False}
