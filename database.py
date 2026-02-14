import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, database_url):
        self.database_url = database_url
        self.init_db()
    
    def get_connection(self):
        return psycopg2.connect(self.database_url, sslmode='require')
    
    def init_db(self):
        """ایجاد جداول مورد نیاز"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # جدول کاربران
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fitness_level VARCHAR(50) DEFAULT 'مبتدی',
                    last_activity TIMESTAMP
                )
            """)
            
            # جدول تاریخچه تمرینات
            cur.execute("""
                CREATE TABLE IF NOT EXISTS workout_history (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    workout_text TEXT,
                    analysis TEXT,
                    calories INT,
                    intensity VARCHAR(50),
                    workout_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # جدول تنظیمات کاربر
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
                    language VARCHAR(10) DEFAULT 'fa',
                    notifications BOOLEAN DEFAULT TRUE,
                    workout_reminder_time TIME,
                    preferred_level VARCHAR(50)
                )
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def add_user(self, user_id, username, first_name, last_name):
        """افزودن کاربر جدید"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (user_id, username, first_name, last_name, last_activity)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                last_activity = EXCLUDED.last_activity
            """, (user_id, username, first_name, last_name, datetime.now()))
            
            # ایجاد تنظیمات پیش‌فرض
            cur.execute("""
                INSERT INTO user_settings (user_id)
                VALUES (%s)
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id,))
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def save_workout(self, user_id, workout_text, analysis, calories, intensity):
        """ذخیره تمرین در تاریخچه"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO workout_history (user_id, workout_text, analysis, calories, intensity)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, workout_text, analysis, calories, intensity))
            
            # به‌روزرسانی آخرین فعالیت کاربر
            cur.execute("""
                UPDATE users SET last_activity = %s WHERE user_id = %s
            """, (datetime.now(), user_id))
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving workout: {e}")
            return False
    
    def get_user_history(self, user_id, limit=10):
        """دریافت تاریخچه تمرینات کاربر"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT * FROM workout_history 
                WHERE user_id = %s 
                ORDER BY workout_date DESC 
                LIMIT %s
            """, (user_id, limit))
            history = cur.fetchall()
            cur.close()
            conn.close()
            return history
        except Exception as e:
            logger.error(f"Error getting history: {e}")
            return []
    
    def update_user_level(self, user_id, level):
        """به‌روزرسانی سطح کاربر"""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE users SET fitness_level = %s WHERE user_id = %s
            """, (level, user_id))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating user level: {e}")
            return False
