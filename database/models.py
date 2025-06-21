# database/models.py

from sqlalchemy import (
    Column, String, Date, Integer, ForeignKey, Boolean, Numeric, TIMESTAMP, Table
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

training_subscription_access = Table('training_subscription_access', Base.metadata,
    Column('training_id', String(50), ForeignKey('trainings.id'), primary_key=True),
    Column('subscription_type_id', String(50), ForeignKey('subscription_types.id'), primary_key=True)
)

class Status(Base): __tablename__ = 'statuses'; name = Column(String(50), primary_key=True); description = Column(String(200))
class Position(Base): __tablename__ = 'positions'; id = Column(String(50), primary_key=True); name = Column(String(50), nullable=False); min_salary = Column(Numeric(10, 2), nullable=False); max_salary = Column(Numeric(10, 2), nullable=False)
class PaymentMethod(Base): __tablename__ = 'payment_methods'; id = Column(String(20), primary_key=True); name = Column(String(50), nullable=False)

class Client(Base):
    __tablename__ = 'clients'
    id = Column(String(50), primary_key=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50))
    reg_date = Column(Date, nullable=False)
    discount = Column(Numeric(5, 2), default=0.0)
    
    user = relationship("User", back_populates="client", uselist=False, cascade="all, delete-orphan")
    subscriptions = relationship("ClientSubscription", back_populates="client", cascade="all, delete-orphan")
    participants = relationship("TrainingParticipant", back_populates="client", cascade="all, delete-orphan")
    warnings = relationship("Warning", back_populates="client", cascade="all, delete-orphan")
    contacts = relationship("ClientContact", back_populates="client", cascade="all, delete-orphan")

class Staff(Base):
    __tablename__ = 'staff'
    id = Column(String(50), primary_key=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50))
    birth_date = Column(Date, nullable=False)
    gender = Column(String(1))
    phone = Column(String(20), nullable=True)
    
    passport_series = Column(String(4), nullable=True)
    passport_number = Column(String(6), nullable=True)
    address = Column(String(255), nullable=True)
    education = Column(String(255), nullable=True)
    
    inn = Column(String(12), unique=True, nullable=False)
    snils = Column(String(11), unique=True, nullable=False)
    hire_date = Column(Date, nullable=False)
    position_id = Column(String(50), ForeignKey('positions.id'))
    salary = Column(Numeric(10, 2), nullable=True) # Оклад

    position = relationship("Position")
    user = relationship("User", back_populates="staff", uselist=False, cascade="all, delete-orphan")
    trainings = relationship("Training", back_populates="trainer")
    warnings = relationship("Warning", back_populates="staff")

class Equipment(Base):
    __tablename__ = 'equipment'
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    model = Column(String(100), nullable=True)
    section_id = Column(String(50), ForeignKey('sections.id'), nullable=False)
    
    purchase_date = Column(Date, nullable=False) # Дата покупки
    warranty_months = Column(Integer, nullable=False) # Срок гарантии в месяцах
    
    last_maintenance_date = Column(Date, nullable=True) 
    
    quantity = Column(Integer, default=1, nullable=False)

    section = relationship("Section")

class User(Base):
    __tablename__ = 'users'
    id = Column(String(50), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)
    client_id = Column(String(50), ForeignKey('clients.id'))
    staff_id = Column(String(50), ForeignKey('staff.id'))
    
    client = relationship("Client", back_populates="user")
    staff = relationship("Staff", back_populates="user")

class Section(Base):
    __tablename__ = 'sections'
    id = Column(String(50), primary_key=True)
    name = Column(String(50), nullable=False)
    status_name = Column(String(50), ForeignKey('statuses.name'))

class SubscriptionType(Base):
    __tablename__ = 'subscription_types'
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    cost = Column(Numeric(10, 2), nullable=False)
    description = Column(String(255))
    
    instances = relationship("ClientSubscription", back_populates="subscription_type")
    accessible_trainings = relationship("Training", secondary=training_subscription_access, back_populates="allowed_subscriptions")

class Training(Base):
    __tablename__ = 'trainings'
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    section_id = Column(String(50), ForeignKey('sections.id'), nullable=False)
    trainer_id = Column(String(50), ForeignKey('staff.id'), nullable=True)
    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    is_group = Column(Boolean, default=False, nullable=False)
    max_participants = Column(Integer, default=1, nullable=False)
    
    section = relationship("Section")
    trainer = relationship("Staff", back_populates="trainings")
    participants = relationship("TrainingParticipant", back_populates="training", cascade="all, delete-orphan")
    allowed_subscriptions = relationship("SubscriptionType", secondary=training_subscription_access, back_populates="accessible_trainings")

class ClientSubscription(Base): __tablename__ = 'client_subscriptions'; id = Column(String(50), primary_key=True); client_id = Column(String(50), ForeignKey('clients.id'), nullable=False); subscription_type_id = Column(String(50), ForeignKey('subscription_types.id'), nullable=False); start_date = Column(Date, nullable=False); end_date = Column(Date, nullable=False); status_name = Column(String(50), ForeignKey('statuses.name')); client = relationship("Client", back_populates="subscriptions"); subscription_type = relationship("SubscriptionType", back_populates="instances"); status = relationship("Status"); payment = relationship("Payment", back_populates="client_subscription", uselist=False, cascade="all, delete-orphan")
class TrainingParticipant(Base): __tablename__ = 'training_participants'; training_id = Column(String(50), ForeignKey('trainings.id'), primary_key=True); client_id = Column(String(50), ForeignKey('clients.id'), primary_key=True); status_name = Column(String(50), ForeignKey('statuses.name')); training = relationship("Training", back_populates="participants"); client = relationship("Client", back_populates="participants"); status = relationship("Status")
class ClientContact(Base): __tablename__ = 'client_contacts'; client_id = Column(String(50), ForeignKey('clients.id'), primary_key=True); contact_type = Column(String(20), primary_key=True); contact_value = Column(String(254), nullable=False); client = relationship("Client", back_populates="contacts")
class Payment(Base): __tablename__ = 'payments'; id = Column(String(50), primary_key=True); client_subscription_id = Column(String(50), ForeignKey('client_subscriptions.id'), nullable=False, unique=True); amount = Column(Numeric(10, 2), nullable=False); date = Column(Date, nullable=False); method_id = Column(String(20), ForeignKey('payment_methods.id'), nullable=False); client_subscription = relationship("ClientSubscription", back_populates="payment"); method = relationship("PaymentMethod")
class Warning(Base): __tablename__ = 'warnings'; id = Column(Integer, primary_key=True, autoincrement=True); client_id = Column(String(50), ForeignKey('clients.id'), nullable=False); staff_id = Column(String(50), ForeignKey('staff.id'), nullable=False); date = Column(Date, nullable=False); reason = Column(String(200), nullable=False); client = relationship("Client", back_populates="warnings"); staff = relationship("Staff", back_populates="warnings")