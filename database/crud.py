from sqlalchemy.orm import Session
from . import models
from services.utils import generate_id
from services.auth import get_password_hash

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

def delete_client(db: Session, client_id: str):
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if client:
        db.delete(client)
        db.commit()
        return True
    return False

def get_staff(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Staff).offset(skip).limit(limit).all()

def get_sections(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Section).offset(skip).limit(limit).all()

def get_single_staff(db: Session, staff_id: str):
    return db.query(models.Staff).filter(models.Staff.id == staff_id).first()

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
        position_id=staff_data["position_id"],
        phone=staff_data.get("phone"),
        salary=staff_data.get("salary"),
        education=staff_data.get("education"),
        address=staff_data.get("address"),
        passport_series=staff_data.get("passport_series"),
        passport_number=staff_data.get("passport_number")
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff

def delete_staff(db: Session, staff_id: str):
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if staff:
        db.delete(staff)
        db.commit()
        return True
    return False

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user_data: dict):
    user_id = generate_id()
    hashed_password = get_password_hash(user_data["password"])
    user = models.User(
        id=user_id,
        username=user_data["username"],
        password=hashed_password,
        role=user_data["role"],
        client_id=user_data.get("client_id"),
        staff_id=user_data.get("staff_id")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user