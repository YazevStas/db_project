# routers/manager.py

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError, DataError, InternalError
from datetime import datetime
from typing import Optional, List

from database import crud, models, get_db
from services.auth import require_role
from services.utils import generate_id

router = APIRouter()

# --- Главная панель менеджера ---
@router.get("/dashboard", response_class=HTMLResponse)
async def manager_dashboard(
    request: Request,
    user: models.User = Depends(require_role("manager")),
    db: Session = Depends(get_db)
):
    # Загружаем все необходимые данные для отображения на панели
    all_clients = db.query(models.Client).options(joinedload(models.Client.contacts)).order_by(models.Client.last_name).all()
    all_staff = db.query(models.Staff).options(joinedload(models.Staff.position)).order_by(models.Staff.last_name).all()
    all_trainings = db.query(models.Training).options(joinedload(models.Training.section), joinedload(models.Training.trainer), joinedload(models.Training.participants)).order_by(models.Training.start_time.desc()).all()
    
    # Данные, необходимые для модальных окон
    all_sections = crud.get_sections(db)
    all_trainers = db.query(models.Staff).join(models.Position).filter(models.Position.name == 'Тренер').all()
    all_subscription_types = db.query(models.SubscriptionType).order_by(models.SubscriptionType.name).all()

    context = {
        "request": request,
        "current_user": user,
        "clients": all_clients,
        "staff": all_staff,
        "trainings": all_trainings,
        # Передаем данные для форм
        "all_clients": all_clients,
        "all_sections": all_sections,
        "trainers": all_trainers,
        "all_subscription_types": all_subscription_types
    }
    return request.app.state.templates.TemplateResponse("manager.html", context)


# --- УПРАВЛЕНИЕ КЛИЕНТАМИ ---
@router.get("/client/{client_id}/edit", response_class=HTMLResponse)
async def edit_client_form(
    request: Request,
    client_id: str,
    user: models.User = Depends(require_role("manager")),
    db: Session = Depends(get_db)
):
    client = db.query(models.Client).options(joinedload(models.Client.contacts)).filter_by(id=client_id).first()
    if not client:
        return RedirectResponse(url="/manager/dashboard?error=Клиент не найден", status_code=303)
    
    context = {"request": request, "client": client, "current_role": user.role}
    return request.app.state.templates.TemplateResponse("edit_client.html", context)

@router.post("/client/{client_id}/edit")
async def update_client_by_manager(
    client_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("manager")),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: Optional[str] = Form(None),
    discount: float = Form(...),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None)
):
    phone_to_save = None
    if phone and phone.strip():
        cleaned_phone = "".join(filter(lambda char: char.isdigit() or char == '+', phone.strip()))
        if cleaned_phone.startswith('+'):
            if len(cleaned_phone) != 12 or not cleaned_phone[1:].isdigit():
                return RedirectResponse(url=f"/manager/client/{client_id}/edit?error=Формат телефона: '+' и 11 цифр.", status_code=303)
        elif cleaned_phone.startswith('8'):
            if len(cleaned_phone) != 11 or not cleaned_phone.isdigit():
                return RedirectResponse(url=f"/manager/client/{client_id}/edit?error=Формат телефона: '8' и 10 цифр.", status_code=303)
        else:
            return RedirectResponse(url=f"/manager/client/{client_id}/edit?error=Номер телефона должен начинаться с '+' или '8'.", status_code=303)
        phone_to_save = cleaned_phone

    client = crud.get_client(db, client_id)
    if not client:
        return RedirectResponse(url="/manager/dashboard?error=Клиент не найден", status_code=303)
    
    client.last_name, client.first_name, client.middle_name, client.discount = last_name, first_name, middle_name, discount
    
    contact_details = {"phone": phone_to_save, "email": email}
    for c_type, c_value in contact_details.items():
        existing_contact = db.query(models.ClientContact).filter_by(client_id=client_id, contact_type=c_type).first()
        if c_value:
            if existing_contact: existing_contact.contact_value = c_value
            else: db.add(models.ClientContact(client_id=client.id, contact_type=c_type, contact_value=c_value))
        elif existing_contact: db.delete(existing_contact)
            
    db.commit()
    return RedirectResponse(url="/manager/dashboard?message=Данные клиента обновлены", status_code=303)


# --- УПРАВЛЕНИЕ СОТРУДНИКАМИ ---
@router.get("/staff/{staff_id}/edit", response_class=HTMLResponse)
async def edit_staff_form(request: Request, staff_id: str, user: models.User = Depends(require_role("manager")), db: Session = Depends(get_db)):
    staff = crud.get_single_staff(db, staff_id=staff_id)
    if not staff:
        return RedirectResponse(url="/manager/dashboard?error=Сотрудник не найден", status_code=303)
    positions = db.query(models.Position).all()
    context = {"request": request, "staff": staff, "positions": positions, "current_role": user.role}
    return request.app.state.templates.TemplateResponse("edit_staff.html", context)

@router.post("/staff/{staff_id}/edit")
async def update_staff(
    staff_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("manager")),
    last_name: str = Form(...), first_name: str = Form(...), middle_name: Optional[str] = Form(None),
    birth_date: str = Form(...), gender: str = Form(...), phone: Optional[str] = Form(None),
    passport_series: Optional[str] = Form(None), passport_number: Optional[str] = Form(None),
    address: Optional[str] = Form(None), education: Optional[str] = Form(None),
    inn: str = Form(...), snils: str = Form(...), hire_date: str = Form(...),
    position_id: str = Form(...), salary: Optional[float] = Form(None)
):
    phone_to_save = None
    if phone and phone.strip():
        cleaned_phone = "".join(filter(lambda char: char.isdigit() or char == '+', phone.strip()))
        if cleaned_phone.startswith('+'):
            if len(cleaned_phone) != 12 or not cleaned_phone[1:].isdigit():
                return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error=Формат телефона: '+' и 11 цифр.", status_code=303)
        elif cleaned_phone.startswith('8'):
            if len(cleaned_phone) != 11 or not cleaned_phone.isdigit():
                return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error=Формат телефона: '8' и 10 цифр.", status_code=303)
        else:
            return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error=Номер должен начинаться с '+' или '8'.", status_code=303)
        phone_to_save = cleaned_phone

    try:
        hire_date_obj = datetime.strptime(hire_date, '%Y-%m-%d').date()
        if hire_date_obj > datetime.now().date():
            return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error=Дата приема не может быть в будущем.", status_code=303)
        birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
    except ValueError:
        return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error=Неверный формат даты.", status_code=303)

    staff = crud.get_single_staff(db, staff_id=staff_id)
    if not staff: return RedirectResponse(url="/manager/dashboard?error=Сотрудник не найден", status_code=303)

    try:
        staff.last_name, staff.first_name, staff.middle_name = last_name, first_name, middle_name
        staff.birth_date, staff.gender, staff.phone = birth_date_obj, gender, phone_to_save
        staff.passport_series, staff.passport_number = passport_series, passport_number
        staff.address, staff.education = address, education
        staff.inn, staff.snils, staff.hire_date = inn, snils, hire_date_obj
        staff.position_id, staff.salary = position_id, salary
        
        db.commit()
        return RedirectResponse(url="/manager/dashboard?message=Данные сотрудника обновлены", status_code=303)
    except (IntegrityError, DataError, InternalError) as e:
        db.rollback()
        error_message = "Произошла ошибка при обновлении."
        original_error = getattr(e, 'orig', None)
        if original_error:
            error_str = str(original_error).lower()
            if "validate_staff_age" in error_str or "старше 18 лет" in error_str: error_message = "Ошибка: Сотруднику должно быть не менее 18 лет."
            elif "duplicate key value" in error_str: error_message = "Ошибка: Сотрудник с таким ИНН или СНИЛС уже существует."
            else: error_message = "Ошибка базы данных."
        return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error={error_message}", status_code=303)


# --- УПРАВЛЕНИЕ ТРЕНИРОВКАМИ ---
@router.post("/add_training")
async def add_training_by_manager(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("manager")),
    name: str = Form(...),
    section_id: str = Form(...),
    start_time: datetime = Form(...),
    end_time: datetime = Form(...),
    is_group: bool = Form(False),
    trainer_id: Optional[str] = Form(None),
    max_participants: Optional[int] = Form(None),
    client_id: Optional[str] = Form(None),
    allowed_subscription_type_ids: Optional[List[str]] = Form(None)
):
    try:
        # --- Шаг 1: Создаем основную запись о тренировке ---
        new_training = models.Training(
            id=generate_id(),
            name=name,
            section_id=section_id,
            trainer_id=trainer_id if trainer_id else None,
            start_time=start_time,
            end_time=end_time,
            is_group=is_group,
            max_participants=1 if not is_group else max_participants
        )
        db.add(new_training)
        # Делаем первый коммит, чтобы тренировка появилась в базе
        db.commit()
        db.refresh(new_training)
        
        message = ""

        # --- Шаг 2: Добавляем связи (участников или доступы) ---
        if not is_group:
            if not client_id:
                # Если это произошло, откатываем создание тренировки
                db.delete(new_training)
                db.commit()
                return RedirectResponse(url="/manager/dashboard?error=Для индивидуальной тренировки необходимо выбрать клиента", status_code=303)
            
            # Создаем запись об участнике
            participant = models.TrainingParticipant(
                training_id=new_training.id, client_id=client_id, status_name='confirmed'
            )
            db.add(participant)
            message = "Индивидуальная тренировка создана и клиент записан"
        else: # Если групповая
            if not allowed_subscription_type_ids:
                db.delete(new_training)
                db.commit()
                return RedirectResponse(url="/manager/dashboard?error=Для групповой тренировки необходимо выбрать тип абонемента", status_code=303)
            
            # Находим объекты абонементов и добавляем их в связь
            allowed_subs = db.query(models.SubscriptionType).filter(
                models.SubscriptionType.id.in_(allowed_subscription_type_ids)
            ).all()
            new_training.allowed_subscriptions.extend(allowed_subs)
            message = "Групповая тренировка успешно создана"

        # Финальный коммит для сохранения связей
        db.commit()
        return RedirectResponse(url=f"/manager/dashboard?message={message}", status_code=303)

    except Exception as e:
        db.rollback()
        print(f"ОШИБКА при создании тренировки менеджером: {e}")
        return RedirectResponse(url=f"/manager/dashboard?error=Произошла ошибка при создании тренировки", status_code=303)