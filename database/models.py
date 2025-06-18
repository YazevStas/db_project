from sqlalchemy import Column, String, Date, Integer, ForeignKey, Boolean, Float, TIMESTAMP, Time, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Status(Base):
    __tablename__ = 'statuses'
    name = Column(String(50), primary_key=True)
    description = Column(String(200))

class Client(Base):
    __tablename__ = 'clients'
    id = Column(String(12), primary_key=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50))
    reg_date = Column(Date, nullable=False)
    discount = Column(Numeric(5, 2), default=0.0)
    
    subscriptions = relationship("Subscription", back_populates="client")
    contacts = relationship("ClientContact", back_populates="client")
    warnings = relationship("Warning", back_populates="client")
    attendances = relationship("Attendance", back_populates="client")
    training_participants = relationship("TrainingParticipant", back_populates="client")

class Position(Base):
    __tablename__ = 'positions'
    id = Column(String(12), primary_key=True)
    name = Column(String(50), nullable=False)
    min_salary = Column(Numeric(10, 2), nullable=False)
    max_salary = Column(Numeric(10, 2), nullable=False)

class Staff(Base):
    __tablename__ = 'staff'
    id = Column(String(12), primary_key=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50))
    birth_date = Column(Date, nullable=False)
    gender = Column(String(1))
    inn = Column(String(12), unique=True, nullable=False)
    snils = Column(String(11), unique=True, nullable=False)
    hire_date = Column(Date, nullable=False)
    position_id = Column(String(12), ForeignKey('positions.id'))
    
    position = relationship("Position")
    contacts = relationship("StaffContact", back_populates="staff")
    addresses = relationship("StaffAddress", back_populates="staff")
    education = relationship("StaffEducation", back_populates="staff")
    warnings = relationship("Warning", back_populates="staff")
    section_staff = relationship("SectionStaff", back_populates="staff")
    trainings = relationship("Training", back_populates="trainer")
    work_schedules = relationship("WorkSchedule", back_populates="staff")

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(String(12), primary_key=True)
    client_id = Column(String(12), ForeignKey('clients.id'), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status_name = Column(String(50), ForeignKey('statuses.name'))
    cost = Column(Numeric(10, 2), nullable=False)
    
    client = relationship("Client", back_populates="subscriptions")
    status = relationship("Status")
    payments = relationship("Payment", back_populates="subscription")

class Section(Base):
    __tablename__ = 'sections'
    id = Column(String(12), primary_key=True)
    name = Column(String(50), nullable=False)
    status_name = Column(String(50), ForeignKey('statuses.name'))
    
    status = relationship("Status")
    equipment = relationship("Equipment", back_populates="section")
    trainings = relationship("Training", back_populates="section")
    attendances = relationship("Attendance", back_populates="section")
    section_staff = relationship("SectionStaff", back_populates="section")
    schedules = relationship("SectionSchedule", back_populates="section")

class Training(Base):
    __tablename__ = 'trainings'
    id = Column(String(12), primary_key=True)
    section_id = Column(String(12), ForeignKey('sections.id'), nullable=False)
    trainer_id = Column(String(12), ForeignKey('staff.id'))
    training_type = Column(String(20), nullable=False)
    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    max_participants = Column(Integer)
    
    section = relationship("Section", back_populates="trainings")
    trainer = relationship("Staff", back_populates="trainings")
    participants = relationship("TrainingParticipant", back_populates="training")

class ClientContact(Base):
    __tablename__ = 'client_contacts'
    client_id = Column(String(12), ForeignKey('clients.id'), primary_key=True)
    contact_type = Column(String(20), primary_key=True)
    contact_value = Column(String(254), nullable=False)
    
    client = relationship("Client", back_populates="contacts")

class StaffContact(Base):
    __tablename__ = 'staff_contacts'
    staff_id = Column(String(12), ForeignKey('staff.id'), primary_key=True)
    contact_type = Column(String(20), primary_key=True)
    contact_value = Column(String(254), nullable=False)
    
    staff = relationship("Staff", back_populates="contacts")

class StaffAddress(Base):
    __tablename__ = 'staff_addresses'
    staff_id = Column(String(12), ForeignKey('staff.id'), primary_key=True)
    address_value = Column(String(200), nullable=False)
    
    staff = relationship("Staff", back_populates="addresses")

class StaffEducation(Base):
    __tablename__ = 'staff_education'
    staff_id = Column(String(12), ForeignKey('staff.id'), primary_key=True)
    education_level = Column(String(50), nullable=False)
    specialty = Column(String(100), nullable=False)
    diploma_num = Column(String(50))
    graduation_date = Column(Date)
    
    staff = relationship("Staff", back_populates="education")

class Equipment(Base):
    __tablename__ = 'equipment'
    id = Column(String(12), primary_key=True)
    section_id = Column(String(12), ForeignKey('sections.id'), nullable=False)
    name = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    purchase_date = Column(Date, nullable=False)
    warranty_months = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    
    section = relationship("Section", back_populates="equipment")

class Attendance(Base):
    __tablename__ = 'attendances'
    client_id = Column(String(12), ForeignKey('clients.id'), primary_key=True)
    section_id = Column(String(12), ForeignKey('sections.id'), primary_key=True)
    entry_time = Column(TIMESTAMP, primary_key=True)
    exit_time = Column(TIMESTAMP)
    
    client = relationship("Client", back_populates="attendances")
    section = relationship("Section", back_populates="attendances")

class Warning(Base):
    __tablename__ = 'warnings'
    client_id = Column(String(12), ForeignKey('clients.id'), primary_key=True)
    staff_id = Column(String(12), ForeignKey('staff.id'), primary_key=True)
    date = Column(Date, primary_key=True)
    reason = Column(String(200), nullable=False)
    
    client = relationship("Client", back_populates="warnings")
    staff = relationship("Staff", back_populates="warnings")

class SectionStaff(Base):
    __tablename__ = 'section_staff'
    section_id = Column(String(12), ForeignKey('sections.id'), primary_key=True)
    staff_id = Column(String(12), ForeignKey('staff.id'), primary_key=True)
    is_primary = Column(Boolean, default=False)
    
    section = relationship("Section", back_populates="section_staff")
    staff = relationship("Staff", back_populates="section_staff")

class TrainingParticipant(Base):
    __tablename__ = 'training_participants'
    training_id = Column(String(12), ForeignKey('trainings.id'), primary_key=True)
    client_id = Column(String(12), ForeignKey('clients.id'), primary_key=True)
    status_name = Column(String(50), ForeignKey('statuses.name'))
    
    training = relationship("Training", back_populates="participants")
    client = relationship("Client", back_populates="training_participants")
    status = relationship("Status")

class WorkSchedule(Base):
    __tablename__ = 'work_schedules'
    staff_id = Column(String(12), ForeignKey('staff.id'), primary_key=True)
    day_of_week = Column(String(3), primary_key=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    staff = relationship("Staff", back_populates="work_schedules")

class SectionSchedule(Base):
    __tablename__ = 'section_schedules'
    section_id = Column(String(12), ForeignKey('sections.id'), primary_key=True)
    day_of_week = Column(String(3), primary_key=True)
    open_time = Column(Time, nullable=False)
    close_time = Column(Time, nullable=False)
    
    section = relationship("Section", back_populates="schedules")

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(String(12), primary_key=True)
    subscription_id = Column(String(12), ForeignKey('subscriptions.id'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(Date, nullable=False)
    method_id = Column(String(20), ForeignKey('payment_methods.id'), nullable=False)
    
    subscription = relationship("Subscription", back_populates="payments")
    method = relationship("PaymentMethod")

class PaymentMethod(Base):
    __tablename__ = 'payment_methods'
    id = Column(String(20), primary_key=True)
    name = Column(String(50), nullable=False)

class User(Base):
    __tablename__ = 'users'
    id = Column(String(12), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)  # admin, tech_admin, manager, cashier, trainer, client
    client_id = Column(String(12), ForeignKey('clients.id'))
    staff_id = Column(String(12), ForeignKey('staff.id'))
    
    client = relationship("Client", backref="user")
    staff = relationship("Staff", backref="user")