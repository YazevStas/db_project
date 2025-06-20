from .session import SessionLocal, engine, get_db
from .models import (
    Base, User, Client, Staff, Status, Position, Section, Training, 
    Payment, PaymentMethod, Warning, Equipment,
    SubscriptionType, ClientSubscription, TrainingParticipant
)
# Здесь мы импортируем все нужные функции из crud.py
from .crud import (
    get_clients, get_client, create_client, delete_client,
    get_staff, get_single_staff, create_staff, delete_staff, 
    get_user_by_username, create_user,
    get_sections  # <--- Убедитесь, что этот импорт есть
)
from .initial_data import initialize_database
from .sql_objects import create_sql_objects

# А здесь мы "разрешаем" другим файлам использовать эти функции
__all__ = [
    # Сессия и движок
    'SessionLocal', 'engine', 'get_db', 
    
    # Модели
    'Base', 'User', 'Client', 'Staff', 'Status', 'Position', 'Section', 
    'Training', 'Payment', 'PaymentMethod', 'Warning', 'Equipment',
    'SubscriptionType', 'ClientSubscription', 'TrainingParticipant',
    
    # CRUD-функции
    'get_clients', 'get_client', 'create_client', 'delete_client',
    'get_staff', 'get_single_staff', 'create_staff', 'delete_staff', 
    'get_user_by_username', 'create_user',
    'get_sections', # <--- И самое главное, убедитесь, что эта строка здесь есть
    
    # Функции инициализации
    'initialize_database', 'create_sql_objects'
]