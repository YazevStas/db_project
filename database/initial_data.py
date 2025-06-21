from sqlalchemy.orm import Session
from . import models, crud
from datetime import datetime, timedelta

def initialize_database(db: Session):
    if db.query(models.User).first():
        return

    print("База данных пуста. Создание начальных данных...")

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
    payment_methods = [
        models.PaymentMethod(id="cash", name="Наличные"), 
        models.PaymentMethod(id="card", name="Банковская карта"),
        models.PaymentMethod(id="sbp", name="СБП")
    ]
    db.add_all(payment_methods)
    db.commit()
    print("Справочники созданы.")

    section_gym = models.Section(id="gym01", name="Тренажерный зал", status_name="active")
    section_pool = models.Section(id="pool01", name="Бассейн", status_name="active")
    db.add_all([section_gym, section_pool])
    sub_type1 = models.SubscriptionType(id="sub_full_month", name="Полный день (1 месяц)", cost=3000, description="Доступ во все зоны без ограничений по времени.")
    sub_type2 = models.SubscriptionType(id="sub_morning_month", name="Утренний (1 месяц)", cost=2000, description="Доступ до 12:00.")
    db.add_all([sub_type1, sub_type2])
    db.commit()
    print("Секции и типы абонементов созданы.")

    client1 = crud.create_client(db, {"last_name": "Петров", "first_name": "Петр", "reg_date": datetime.now().date()})
    
    base_staff_data = {
        "birth_date": datetime(1990, 1, 1), "gender": "М", "phone": "+79001112233",
        "passport_series": "4501", "passport_number": "111111", 
        "address": "г. Москва, ул. Тверская, д.1", "education": "Высшее, РГУФК",
        "hire_date": datetime(2022, 1, 1), "salary": 75000
    }

    staff_admin_data = {**base_staff_data, "last_name": "Админов", "first_name": "Админ", "inn": "111111111111", "snils": "11111111111", "position_id": "pos_admin"}
    staff_trainer_data = {**base_staff_data, "last_name": "Тренерова", "first_name": "Ирина", "gender": "Ж", "inn": "222222222222", "snils": "22222222222", "position_id": "pos_trainer", "salary": 80000}
    staff_cashier_data = {**base_staff_data, "last_name": "Кассиров", "first_name": "Иван", "inn": "333333333333", "snils": "33333333333", "position_id": "pos_cashier", "salary": 50000}
    staff_manager_data = {**base_staff_data, "last_name": "Менеджеров", "first_name": "Максим", "inn": "444444444444", "snils": "44444444444", "position_id": "pos_manager", "salary": 65000}
    staff_tech_data = {**base_staff_data, "last_name": "Техников", "first_name": "Сергей", "inn": "555555555555", "snils": "55555555555", "position_id": "pos_tech", "salary": 90000}

    staff_admin = crud.create_staff(db, staff_admin_data)
    staff_trainer = crud.create_staff(db, staff_trainer_data)
    staff_cashier = crud.create_staff(db, staff_cashier_data)
    staff_manager = crud.create_staff(db, staff_manager_data)
    staff_tech = crud.create_staff(db, staff_tech_data)
    print("Клиенты и сотрудники созданы.")

    users_to_create = [
        {"username": "admin", "password": "admin123", "role": "admin", "staff_id": staff_admin.id},
        {"username": "trainer", "password": "trainer123", "role": "trainer", "staff_id": staff_trainer.id},
        {"username": "cashier", "password": "cashier123", "role": "cashier", "staff_id": staff_cashier.id},
        {"username": "manager", "password": "manager123", "role": "manager", "staff_id": staff_manager.id},
        {"username": "tech_admin", "password": "tech123", "role": "tech_admin", "staff_id": staff_tech.id},
        {"username": "client1", "password": "client123", "role": "client", "client_id": client1.id},
    ]
    for user_data in users_to_create:
        crud.create_user(db, user_data)
    print("Пользователи созданы.")
        
    client1_phone = models.ClientContact(client_id=client1.id, contact_type="phone", contact_value="+79123456789")
    db.add(client1_phone)
    
    print("Создание начального оборудования...")
    equipment1 = models.Equipment(id=crud.generate_id(), name="Беговая дорожка", model="TechnoGym Run 500", section_id=section_gym.id, purchase_date=datetime(2023, 1, 15).date(), warranty_months=24, last_maintenance_date=datetime(2024, 1, 10).date(), quantity=5)
    equipment2 = models.Equipment(id=crud.generate_id(), name="Силовая рама", model="Foreman FY-201", section_id=section_gym.id, purchase_date=datetime(2022, 11, 20).date(), warranty_months=36, last_maintenance_date=datetime(2023, 12, 1).date(), quantity=2)
    db.add_all([equipment1, equipment2])
    print("Оборудование создано.")

    client_sub1 = models.ClientSubscription(id=crud.generate_id(), client_id=client1.id, subscription_type_id=sub_type1.id, start_date=datetime.now().date() - timedelta(days=10), end_date=datetime.now().date() + timedelta(days=20), status_name="active")
    db.add(client_sub1)
    training1 = models.Training(id="tr001", name="Йога для начинающих", section_id=section_gym.id, trainer_id=staff_trainer.id, start_time=datetime.now() + timedelta(days=2, hours=18), end_time=datetime.now() + timedelta(days=2, hours=19), is_group=True, max_participants=10)
    db.add(training1)
    db.commit()
    print("Начальные данные полностью созданы.")