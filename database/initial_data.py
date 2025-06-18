from sqlalchemy.orm import Session
from . import models
from .crud import create_user, create_client, create_staff, create_subscription
from datetime import datetime, timedelta

def initialize_database(db: Session):
    # Создание статусов
    statuses = [
        models.Status(name="active", description="Активный"),
        models.Status(name="expired", description="Истекший"),
        models.Status(name="blocked", description="Заблокирован"),
        models.Status(name="pending", description="Ожидает активации"),
        models.Status(name="confirmed", description="Подтвержден"),
        models.Status(name="cancelled", description="Отменен"),
    ]
    for status in statuses:
        db.add(status)
    
    # Создание должностей
    positions = [
        models.Position(
            id="pos001", 
            name="Администратор", 
            min_salary=50000, 
            max_salary=80000
        ),
        models.Position(
            id="pos002", 
            name="Тренер", 
            min_salary=60000, 
            max_salary=100000
        ),
        models.Position(
            id="pos003", 
            name="Кассир", 
            min_salary=40000, 
            max_salary=60000
        ),
        models.Position(
            id="pos004", 
            name="Технический администратор", 
            min_salary=70000, 
            max_salary=120000
        ),
    ]
    for position in positions:
        db.add(position)
    
    # Создание методов оплаты
    payment_methods = [
        models.PaymentMethod(id="cash", name="Наличные"),
        models.PaymentMethod(id="card", name="Банковская карта"),
    ]
    for method in payment_methods:
        db.add(method)
    
    db.commit()
    
    # Создание клиентов
    clients = [
        create_client(db, {
            "last_name": "Иванов",
            "first_name": "Иван",
            "middle_name": "Иванович",
            "reg_date": datetime.now() - timedelta(days=30),
            "discount": 10.0
        }),
        create_client(db, {
            "last_name": "Петрова",
            "first_name": "Мария",
            "reg_date": datetime.now() - timedelta(days=15),
            "discount": 5.0
        }),
    ]
    
    # Создание сотрудников
    staff = [
        create_staff(db, {
            "last_name": "Сидоров",
            "first_name": "Алексей",
            "birth_date": datetime(1990, 5, 15),
            "gender": "М",
            "inn": "123456789012",
            "snils": "12345678901",
            "hire_date": datetime(2020, 1, 10),
            "position_id": "pos001"
        }),
        create_staff(db, {
            "last_name": "Кузнецова",
            "first_name": "Ольга",
            "birth_date": datetime(1985, 8, 22),
            "gender": "Ж",
            "inn": "098765432109",
            "snils": "09876543210",
            "hire_date": datetime(2021, 3, 5),
            "position_id": "pos002"
        }),
    ]
    
    # Создание абонементов
    subscriptions = [
        create_subscription(db, {
            "client_id": clients[0].id,
            "start_date": datetime.now() - timedelta(days=10),
            "end_date": datetime.now() + timedelta(days=20),
            "status_name": "active",
            "cost": 5000.0
        }),
        create_subscription(db, {
            "client_id": clients[1].id,
            "start_date": datetime.now() - timedelta(days=5),
            "end_date": datetime.now() + timedelta(days=25),
            "status_name": "active",
            "cost": 7000.0
        }),
    ]
    
    # Создание пользователей
    users = [
        create_user(db, {
            "username": "admin",
            "password": "admin123",  # В реальном приложении должно быть хешировано!
            "role": "admin",
            "staff_id": staff[0].id
        }),
        create_user(db, {
            "username": "trainer",
            "password": "trainer123",
            "role": "trainer",
            "staff_id": staff[1].id
        }),
        create_user(db, {
            "username": "client1",
            "password": "client123",
            "role": "client",
            "client_id": clients[0].id
        }),
        create_user(db, {
            "username": "client2",
            "password": "client456",
            "role": "client",
            "client_id": clients[1].id
        }),
    ]
    
    # Создание секций
    sections = [
        models.Section(
            id="gym01",
            name="Тренажерный зал",
            status_name="active"
        ),
        models.Section(
            id="pool01",
            name="Бассейн",
            status_name="active"
        ),
    ]
    for section in sections:
        db.add(section)
    
    # Создание тренировок
    trainings = [
        models.Training(
            id="tr001",
            section_id="gym01",
            trainer_id=staff[1].id,
            training_type="Групповая",
            start_time=datetime.now() + timedelta(days=1, hours=10),
            end_time=datetime.now() + timedelta(days=1, hours=11),
            max_participants=10
        ),
        models.Training(
            id="tr002",
            section_id="pool01",
            training_type="Индивидуальная",
            start_time=datetime.now() + timedelta(days=2, hours=14),
            end_time=datetime.now() + timedelta(days=2, hours=15),
            max_participants=1
        ),
    ]
    for training in trainings:
        db.add(training)
    
    # Создание участников тренировок
    participants = [
        models.TrainingParticipant(
            training_id="tr001",
            client_id=clients[0].id,
            status_name="confirmed"
        ),
        models.TrainingParticipant(
            training_id="tr002",
            client_id=clients[1].id,
            status_name="confirmed"
        ),
    ]
    for participant in participants:
        db.add(participant)
    
    db.commit()
    
    return {"message": "Initial data created successfully"}