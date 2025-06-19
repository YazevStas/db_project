from sqlalchemy.orm import Session
from . import models, crud
from datetime import datetime, timedelta

def initialize_database(db: Session):
    if db.query(models.User).first():
        return

    print("База данных пуста. Создание начальных данных...")

    # --- ШАГ 1: Создаем справочники ---
    # Это данные, от которых зависят все остальные
    statuses = [models.Status(name=n, description=d) for n, d in [("active", "Активный"), ("expired", "Истекший"), ("blocked", "Заблокирован"), ("pending", "Ожидает активации"), ("confirmed", "Подтвержден"), ("cancelled", "Отменен")]]
    db.add_all(statuses)

    positions = [
        models.Position(id="pos_admin", name="Администратор", min_salary=50000, max_salary=80000),
        models.Position(id="pos_trainer", name="Тренер", min_salary=60000, max_salary=100000),
        models.Position(id="pos_cashier", name="Кассир", min_salary=40000, max_salary=60000),
        models.Position(id="pos_tech", name="Тех. администратор", min_salary=70000, max_salary=120000),
        models.Position(id="pos_manager", name="Менеджер", min_salary=55000, max_salary=90000),
    ]
    db.add_all(positions)

    payment_methods = [models.PaymentMethod(id="cash", name="Наличные"), models.PaymentMethod(id="card", name="Банковская карта")]
    db.add_all(payment_methods)
    
    # Сохраняем справочники в базу, чтобы их можно было использовать
    db.commit()
    print("Справочники созданы.")

    # --- ШАГ 2: Создаем сущности, которые зависят от справочников ---
    section_gym = models.Section(id="gym01", name="Тренажерный зал", status_name="active")
    section_pool = models.Section(id="pool01", name="Бассейн", status_name="active")
    db.add_all([section_gym, section_pool])

    sub_type1 = models.SubscriptionType(id="sub_full_month", name="Полный день (1 месяц)", cost=3000, description="Доступ во все зоны без ограничений по времени.")
    sub_type2 = models.SubscriptionType(id="sub_morning_month", name="Утренний (1 месяц)", cost=2000, description="Доступ до 12:00.")
    db.add_all([sub_type1, sub_type2])
    
    # Сохраняем секции и типы абонементов
    db.commit()
    print("Секции и типы абонементов созданы.")

    # --- ШАГ 3: Создаем клиентов и сотрудников ---
    client1 = crud.create_client(db, {"last_name": "Петров", "first_name": "Петр", "reg_date": datetime.now().date()})
    client2 = crud.create_client(db, {"last_name": "Васильева", "first_name": "Анна", "reg_date": datetime.now().date()})

    staff_admin = crud.create_staff(db, {"last_name": "Админов", "first_name": "Админ", "birth_date": datetime(1990, 1, 1), "gender": "М", "inn": "111111111111", "snils": "11111111111", "hire_date": datetime(2022, 1, 1), "position_id": "pos_admin"})
    staff_trainer = crud.create_staff(db, {"last_name": "Тренерова", "first_name": "Ирина", "birth_date": datetime(1995, 5, 10), "gender": "Ж", "inn": "222222222222", "snils": "22222222222", "hire_date": datetime(2023, 3, 15), "position_id": "pos_trainer"})
    print("Клиенты и сотрудники созданы.")

    # --- ШАГ 4: Создаем пользователей (которые зависят от клиентов и сотрудников) ---
    users_to_create = [
        {"username": "admin", "password": "admin123", "role": "admin", "staff_id": staff_admin.id},
        {"username": "trainer", "password": "trainer123", "role": "trainer", "staff_id": staff_trainer.id},
        {"username": "client1", "password": "client123", "role": "client", "client_id": client1.id},
    ]
    for user_data in users_to_create:
        crud.create_user(db, user_data)
    print("Пользователи созданы.")
        
    # --- ШАГ 5: Создаем финальные связи ---
    client_sub1 = models.ClientSubscription(
        id=crud.generate_id(), client_id=client1.id, subscription_type_id=sub_type1.id,
        start_date=datetime.now().date() - timedelta(days=10),
        end_date=datetime.now().date() + timedelta(days=20), status_name="active"
    )
    db.add(client_sub1)

    training1 = models.Training(
        id="tr001", name="Йога для начинающих", section_id=section_gym.id, trainer_id=staff_trainer.id,
        start_time=datetime.now() + timedelta(days=2, hours=18),
        end_time=datetime.now() + timedelta(days=2, hours=19), is_group=True, max_participants=10
    )
    db.add(training1)

    # Финальный коммит
    db.commit()
    print("Начальные данные полностью созданы.")