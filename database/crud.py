from sqlalchemy.orm import Session
from . import models
from services.utils import generate_id
from services.auth import get_password_hash

# CRUD операции для клиентов
def get_clients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Client).offset(skip).limit(limit).all()

def get_client(db: Session, client_id: str):
    return db.query(models.Client).filter(models.Client.id == client_id).first()

def create_client(db: Session, client_data: dict):
    client_id = generate_id()
    client = models.Client(
        id=client_id,
        last_name=client_data["last_name"],
        first_name=client_data["first_name"],
        middle_name=client_data.get("middle_name"),
        reg_date=client_data["reg_date"],
        discount=client_data.get("discount", 0.0)
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

# CRUD операции для сотрудников
def get_staff(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Staff).offset(skip).limit(limit).all()

def create_staff(db: Session, staff_data: dict):
    staff_id = generate_id()
    staff = models.Staff(
        id=staff_id,
        last_name=staff_data["last_name"],
        first_name=staff_data["first_name"],
        middle_name=staff_data.get("middle_name"),
        birth_date=staff_data["birth_date"],
        gender=staff_data["gender"],
        inn=staff_data["inn"],
        snils=staff_data["snils"],
        hire_date=staff_data["hire_date"],
        position_id=staff_data["position_id"]
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff

# CRUD операции для абонементов
def get_subscriptions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Subscription).offset(skip).limit(limit).all()

def create_subscription(db: Session, subscription_data: dict):
    subscription_id = generate_id()
    subscription = models.Subscription(
        id=subscription_id,
        client_id=subscription_data["client_id"],
        start_date=subscription_data["start_date"],
        end_date=subscription_data["end_date"],
        status_name=subscription_data["status_name"],
        cost=subscription_data["cost"]
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription

# CRUD операции для секций
def get_sections(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Section).offset(skip).limit(limit).all()

# CRUD операции для тренировок
def get_trainings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Training).offset(skip).limit(limit).all()

# CRUD операции для пользователей
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user_data: dict):
    user_id = generate_id()
    hashed_password = get_password_hash(user_data["password"])
    user = models.User(
        id=user_id,
        username=user_data["username"],
        password=hashed_password,  # В реальном приложении должно быть хешировано
        role=user_data["role"],
        client_id=user_data.get("client_id"),
        staff_id=user_data.get("staff_id")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Дополнительные CRUD операции
def get_active_subscriptions(db: Session):
    return db.query(models.Subscription).filter(
        models.Subscription.status_name == "active"
    ).all()

def get_upcoming_trainings(db: Session):
    from datetime import datetime
    return db.query(models.Training).filter(
        models.Training.start_time > datetime.now()
    ).order_by(models.Training.start_time).all()

def get_client_subscriptions(db: Session, client_id: str):
    return db.query(models.Subscription).filter(
        models.Subscription.client_id == client_id
    ).all()

def get_client_attendances(db: Session, client_id: str):
    return db.query(models.Attendance).filter(
        models.Attendance.client_id == client_id
    ).all()