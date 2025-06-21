from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, DataError, InternalError
from typing import Optional, List
from datetime import datetime

from database import crud, models, get_db
from services.auth import require_role
from services.utils import generate_id

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    user: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    all_clients = db.query(models.Client).options(joinedload(models.Client.contacts)).order_by(models.Client.last_name).all()
    all_staff = db.query(models.Staff).options(joinedload(models.Staff.position)).order_by(models.Staff.last_name).all()
    all_client_subscriptions = db.query(models.ClientSubscription).options(joinedload(models.ClientSubscription.client), joinedload(models.ClientSubscription.subscription_type), joinedload(models.ClientSubscription.status)).all()
    all_sections = db.query(models.Section).order_by(models.Section.name).all()
    all_trainings = db.query(models.Training).options(joinedload(models.Training.section), joinedload(models.Training.trainer), joinedload(models.Training.allowed_subscriptions), joinedload(models.Training.participants).joinedload(models.TrainingParticipant.client)).order_by(models.Training.start_time.desc()).all()
    
    all_subscription_types = db.query(models.SubscriptionType).order_by(models.SubscriptionType.name).all()
    all_trainers = db.query(models.Staff).join(models.Position).filter(models.Position.name == 'Тренер').all()
    all_positions = db.query(models.Position).all()
    all_statuses = db.query(models.Status).all()

    clients_for_js = [serialize_client(c) for c in all_clients]
    
    context = {
        "request": request,
        "current_user": user,
        "clients": all_clients,
        "staff": all_staff,
        "client_subscriptions": all_client_subscriptions,
        "sections": all_sections,
        "trainings": all_trainings,
        "all_clients": all_clients, 
        "all_subscription_types": all_subscription_types,
        "all_sections": all_sections,
        "trainers": all_trainers,
        "all_statuses": all_statuses,
        "positions": all_positions,
        "clients_for_js": clients_for_js,
    }
    return request.app.state.templates.TemplateResponse("admin.html", context)

@router.post("/add_client")
async def add_client(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: str = Form(None),
    discount: float = Form(0.0)
):
    client_data = {
        "last_name": last_name, "first_name": first_name,
        "middle_name": middle_name, "reg_date": datetime.now().date(), "discount": discount
    }
    crud.create_client(db, client_data)
    return RedirectResponse(url="/admin/dashboard?message=Клиент успешно добавлен", status_code=303)

@router.post("/client/{client_id}/delete")
async def delete_client(
    client_id: str,
    user: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    if crud.delete_client(db, client_id):
        return RedirectResponse(url="/admin/dashboard?message=Клиент успешно удален", status_code=303)
    return RedirectResponse(url="/admin/dashboard?error=Не удалось удалить клиента", status_code=303)

@router.post("/add_staff")
async def add_staff(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: Optional[str] = Form(None),
    birth_date: str = Form(...),
    gender: str = Form(...),
    inn: str = Form(...),
    snils: str = Form(...),
    hire_date: str = Form(...),
    position_id: str = Form(...),
    phone: Optional[str] = Form(None),
    salary: Optional[float] = Form(None),
    education: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    passport_series: Optional[str] = Form(None),
    passport_number: Optional[str] = Form(None)
):

    if not position_id:
        return RedirectResponse(url="/admin/dashboard?error=Необходимо выбрать должность.", status_code=303)
    if not (inn and inn.isdigit() and len(inn) == 12):
        return RedirectResponse(url="/admin/dashboard?error=ИНН должен состоять ровно из 12 цифр.", status_code=303)  
    if not (snils and snils.isdigit() and len(snils) == 11):
        return RedirectResponse(url="/admin/dashboard?error=СНИЛС должен состоять ровно из 11 цифр.", status_code=303)
    if passport_series and not (passport_series.isdigit() and len(passport_series) == 4):
        return RedirectResponse(url="/admin/dashboard?error=Серия паспорта должна состоять ровно из 4 цифр.", status_code=303)
    if passport_number and not (passport_number.isdigit() and len(passport_number) == 6):
        return RedirectResponse(url="/admin/dashboard?error=Номер паспорта должен состоять ровно из 6 цифр.", status_code=303)
    try:
        birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
        hire_date_obj = datetime.strptime(hire_date, '%Y-%m-%d').date()
    except ValueError:
        return RedirectResponse(url="/admin/dashboard?error=Неверный формат даты. Используйте ГГГГ-ММ-ДД.", status_code=303)
    if hire_date_obj > datetime.now().date():
        return RedirectResponse(url="/admin/dashboard?error=Дата приема на работу не может быть в будущем.", status_code=303)
    
    from dateutil.relativedelta import relativedelta
    age = relativedelta(datetime.now().date(), birth_date_obj).years
    if age < 18:
        return RedirectResponse(url="/admin/dashboard?error=Сотруднику должно быть не менее 18 лет.", status_code=303)

    staff_data = {
        "last_name": last_name, "first_name": first_name, "middle_name": middle_name,
        "birth_date": birth_date_obj, 
        "gender": gender, "inn": inn, "snils": snils,
        "hire_date": hire_date_obj, 
        "position_id": position_id, "phone": phone, "salary": salary, "education": education,
        "address": address, "passport_series": passport_series, "passport_number": passport_number
    }
    
    try:
        crud.create_staff(db, staff_data)
        return RedirectResponse(url="/admin/dashboard?message=Сотрудник успешно добавлен", status_code=303)
    except (IntegrityError, DataError) as e:
        db.rollback()
        error_message = "Произошла ошибка при добавлении."
        original_error = getattr(e, 'orig', None)
        if original_error and "duplicate key value" in str(original_error).lower():
            if "inn" in str(original_error).lower():
                error_message = "Ошибка: Сотрудник с таким ИНН уже существует."
            elif "snils" in str(original_error).lower():
                error_message = "Ошибка: Сотрудник с таким СНИЛС уже существует."
        return RedirectResponse(url=f"/admin/dashboard?error={error_message}", status_code=303)

@router.post("/staff/{staff_id}/delete")
async def delete_staff(
    staff_id: str,
    user: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    if crud.delete_staff(db, staff_id):
        return RedirectResponse(url="/admin/dashboard?message=Сотрудник успешно удален", status_code=303)
    return RedirectResponse(url="/admin/dashboard?error=Не удалось удалить сотрудника", status_code=303)

@router.post("/add_subscription_type")
async def add_subscription_type(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
    name: str = Form(...),
    cost: float = Form(...),
    description: str = Form(None)
):
    sub_type = models.SubscriptionType(id=generate_id(), name=name, cost=cost, description=description)
    db.add(sub_type)
    db.commit()
    return RedirectResponse(url="/admin/dashboard?message=Тип абонемента создан", status_code=303)

@router.post("/add_section")
async def add_section(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
    name: str = Form(...),
    status_name: str = Form(...)
):
    section = models.Section(id=generate_id(), name=name, status_name=status_name)
    db.add(section)
    db.commit()
    return RedirectResponse(url="/admin/dashboard?message=Секция успешно добавлена", status_code=303)

def serialize_client(client: models.Client) -> dict:
    """Преобразует объект Client SQLAlchemy в словарь, готовый для JSON."""
    return {
        "id": client.id,
        "last_name": client.last_name,
        "first_name": client.first_name,
        "middle_name": client.middle_name,
        "reg_date": client.reg_date.isoformat() if client.reg_date else None,
        "discount": float(client.discount),
        "contacts": [
            {"contact_type": c.contact_type, "contact_value": c.contact_value}
            for c in client.contacts
        ]
    }