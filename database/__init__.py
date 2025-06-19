from .session import SessionLocal, engine, get_db
from .models import (
    Base, User, Client, Staff, Status, Position, Section, Training, 
    Payment, PaymentMethod, Warning,
    # Новые модели
    SubscriptionType, ClientSubscription, TrainingParticipant
)
from .crud import (
    get_clients, get_client, create_client, get_staff, create_staff,
    get_user_by_username, create_user
)
from .initial_data import initialize_database
from .sql_objects import create_sql_objects

# Экспортируем все необходимые имена для использования в других частях приложения
__all__ = [
    # Сессия и движок
    'SessionLocal', 'engine', 'get_db', 
    
    # Модели
    'Base', 'User', 'Client', 'Staff', 'Status', 'Position', 'Section', 
    'Training', 'Payment', 'PaymentMethod', 'Warning',
    'SubscriptionType', 'ClientSubscription', 'TrainingParticipant',
    
    # CRUD-функции
    'get_clients', 'get_client', 'create_client', 'get_staff', 'create_staff', 
    'get_user_by_username', 'create_user',
    
    # Функции инициализации
    'initialize_database', 'create_sql_objects'
]