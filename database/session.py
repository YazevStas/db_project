from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Используем переменную окружения для строки подключения к PostgreSQL
# Пример значения в .env: DATABASE_URL="postgresql://user:password@localhost/gym_db"
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Необходимо установить переменную окружения DATABASE_URL")

# Создаем движок для PostgreSQL
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base больше не нужен здесь, так как он определяется в models.py
# и импортируется оттуда.

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()