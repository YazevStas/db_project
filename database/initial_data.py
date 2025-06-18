# database/initial_data.py

from sqlalchemy.orm import Session
from . import models, crud  # Импортируем модуль crud, чтобы использовать его функции
from datetime import datetime, timedelta

def initialize_database(db: Session):
    """
    Заполняет базу данных начальными данными (справочники, тестовые пользователи, клиенты и т.д.),
    только если база данных пуста.
    """
    # Проверяем, есть ли уже данные, чтобы не дублировать их при перезапуске
    if db.query(models.User).first():
        return

    print("База данных пуста. Создание начальных данных...")

    # 1. Создание справочников (статусы, должности, методы оплаты)
    # ------------------------------------------------------------------
    statuses = [
        models.Status(name="active", description="Активный"),
        models.Status(name="expired", description="Истекший"),
        models.Status(name="blocked", description="Заблокирован"),
        models.Status(name="pending", description="Ожидает активации"),
        models.Status(name="confirmed", description="Подтвержден"),
        models.Status(name="cancelled", description="Отменен"),
    ]
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
    ]
    db.add_all(payment_methods)
    
    # Делаем commit, чтобы справочники были доступны для использования в следующих шагах
    db.commit()

    # 2. Создание основных сущностей (клиенты, сотрудники, пользователи)
    # ---------------------------------------------------------------------

    # Создаем клиентов через crud-функцию
    client1 = crud.create_client(db, {
        "last_name": "Петров", "first_name": "Петр", "middle_name": "Петрович",
        "reg_date": datetime.now().date() - timedelta(days=50), "discount": 5.0
    })
    client2 = crud.create_client(db, {
        "last_name": "Васильева", "first_name": "Анна",
        "reg_date": datetime.now().date() - timedelta(days=10), "discount": 0.0
    })

    # Создаем сотрудников через crud-функцию
    staff_admin = crud.create_staff(db, {
        "last_name": "Админов", "first_name": "Админ", "birth_date": datetime(1990, 1, 1),
        "gender": "М", "inn": "111111111111", "snils": "11111111111",
        "hire_date": datetime(2022, 1, 1), "position_id": "pos_admin"
    })
    staff_trainer = crud.create_staff(db, {
        "last_name": "Тренерова", "first_name": "Ирина", "birth_date": datetime(1995, 5, 10),
        "gender": "Ж", "inn": "222222222222", "snils": "22222222222",
        "hire_date": datetime(2023, 3, 15), "position_id": "pos_trainer"
    })
    # Добавим еще сотрудников для других ролей
    staff_manager = crud.create_staff(db, {"last_name": "Менеджеров", "first_name": "Максим", "birth_date": datetime(1988, 7, 7), "gender": "М", "inn": "333333333333", "snils": "33333333333", "hire_date": datetime(2022, 6, 1), "position_id": "pos_manager"})
    staff_cashier = crud.create_staff(db, {"last_name": "Кассирова", "first_name": "Елена", "birth_date": datetime(2000, 2, 20), "gender": "Ж", "inn": "444444444444", "snils": "44444444444", "hire_date": datetime(2023, 8, 1), "position_id": "pos_cashier"})
    staff_tech = crud.create_staff(db, {"last_name": "Техников", "first_name": "Сергей", "birth_date": datetime(1992, 11, 30), "gender": "М", "inn": "555555555555", "snils": "55555555555", "hire_date": datetime(2021, 10, 5), "position_id": "pos_tech"})


    # Создаем пользователей, ВЫЗЫВАЯ crud.create_user, которая хеширует пароли
    # --------------------------------------------------------------------------
    users_to_create = [
        {"username": "admin", "password": "admin123", "role": "admin", "staff_id": staff_admin.id},
        {"username": "trainer", "password": "trainer123", "role": "trainer", "staff_id": staff_trainer.id},
        {"username": "manager", "password": "manager123", "role": "manager", "staff_id": staff_manager.id},
        {"username": "cashier", "password": "cashier123", "role": "cashier", "staff_id": staff_cashier.id},
        {"username": "tech_admin", "password": "tech123", "role": "tech_admin", "staff_id": staff_tech.id},
        {"username": "client1", "password": "client123", "role": "client", "client_id": client1.id},
        {"username": "client2", "password": "client456", "role": "client", "client_id": client2.id},
    ]
    for user_data in users_to_create:
        crud.create_user(db, user_data)


    # 3. Создание связанных данных (абонементы, секции и т.д.)
    # ------------------------------------------------------------
    section_gym = models.Section(id="gym01", name="Тренажерный зал", status_name="active")
    section_pool = models.Section(id="pool01", name="Бассейн", status_name="active")
    db.add_all([section_gym, section_pool])

    sub1 = crud.create_subscription(db, {
        "client_id": client1.id, "start_date": datetime.now().date() - timedelta(days=10),
        "end_date": datetime.now().date() + timedelta(days=20), "status_name": "active", "cost": 3000
    })

    training1 = models.Training(
        id="tr001", section_id=section_gym.id, trainer_id=staff_trainer.id,
        training_type="Групповая", start_time=datetime.now() + timedelta(days=2, hours=18),
        end_time=datetime.now() + timedelta(days=2, hours=19), max_participants=10
    )
    db.add(training1)

    # Финальный коммит для сохранения всех данных
    db.commit()

    print("Начальные данные успешно созданы.")