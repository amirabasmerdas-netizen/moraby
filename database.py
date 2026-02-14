from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from datetime import datetime
import json
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    registered_at = Column(DateTime, default=datetime.utcnow)
    settings = Column(JSON, default={})
    fitness_level = Column(String(20), default='مبتدی')
    total_workouts = Column(Integer, default=0)

class WorkoutHistory(Base):
    __tablename__ = 'workout_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    workout_date = Column(DateTime, default=datetime.utcnow)
    workout_text = Column(Text)
    workout_type = Column(String(50))
    intensity = Column(String(20))
    calories_burned = Column(Float, default=0)
    analysis_result = Column(JSON)
    is_saved = Column(Boolean, default=True)

class Database:
    def __init__(self, db_url):
        self.engine = create_engine(db_url, poolclass=NullPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    async def add_user(self, user_id, username, first_name, last_name):
        session = self.Session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    settings={
                        'language': 'fa',
                        'rest_reminder': True,
                        'water_reminder': True
                    }
                )
                session.add(user)
                session.commit()
            return user
        finally:
            session.close()
    
    async def save_workout(self, user_id, workout_text, workout_type, intensity, calories, analysis):
        session = self.Session()
        try:
            workout = WorkoutHistory(
                user_id=user_id,
                workout_text=workout_text,
                workout_type=workout_type,
                intensity=intensity,
                calories_burned=calories,
                analysis_result=analysis
            )
            session.add(workout)
            
            # Update user workout count
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.total_workouts += 1
            
            session.commit()
            return workout
        finally:
            session.close()
    
    async def get_user_workouts(self, user_id, limit=10):
        session = self.Session()
        try:
            workouts = session.query(WorkoutHistory)\
                .filter_by(user_id=user_id)\
                .order_by(WorkoutHistory.workout_date.desc())\
                .limit(limit)\
                .all()
            return workouts
        finally:
            session.close()
    
    async def get_user_settings(self, user_id):
        session = self.Session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            return user.settings if user else {}
        finally:
            session.close()
    
    async def update_user_settings(self, user_id, settings):
        session = self.Session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.settings.update(settings)
                session.commit()
            return True
        finally:
            session.close()
    
    async def update_fitness_level(self, user_id, level):
        session = self.Session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.fitness_level = level
                session.commit()
            return True
        finally:
            session.close()
