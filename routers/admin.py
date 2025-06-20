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

# --- Главная панель администратора ---
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
    all_clients_for_form = crud.get_clients(db)
    all_positions = db.query(models.Position).all()

    context = {
        "request": request, "current_user": user, "clients": all_clients, "staff": all_staff,
        "client_subscriptions": all_client_subscriptions, "sections": all_sections, "trainings": all_trainings,
        "all_clients": all_clients_for_form, "all_subscription_types": all_subscription_types,
        "all_sections": all_sections, "trainers": all_trainers, "positions": all_positions,
    }
    return request.app.state.templates.TemplateResponse("admin.html", context)

# --- УПРАВЛЕНИЕ КЛИЕНТАМИ ---

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


# --- УПРАВЛЕНИЕ СОТРУДНИКАМИ ---

@router.post("/add_staff")
async def add_staff(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
    last_name: str = Form(...), first_name: str = Form(...), middle_name: str = Form(None),
    birth_date: str = Form(...), gender: str = Form(...), inn: str = Form(...),
    snils: str = Form(...), hire_date: str = Form(...), position_id: str = Form(...),
    phone: str = Form(None), salary: float = Form(None), education: str = Form(None),
    address: str = Form(None), passport_series: str = Form(None), passport_number: str = Form(None)
):
    staff_data = {
        "last_name": last_name, "first_name": first_name, "middle_name": middle_name,
        "birth_date": datetime.strptime(birth_date, '%Y-%m-%d').date(), 
        "gender": gender, "inn": inn, "snils": snils,
        "hire_date": datetime.strptime(hire_date, '%Y-%m-%d').date(), 
        "position_id": position_id, "phone": phone, "salary": salary, "education": education,
        "address": address, "passport_series": passport_series, "passport_number": passport_number
    }
    try:
        crud.create_staff(db, staff_data)
        return RedirectResponse(url="/admin/dashboard?message=Сотрудник успешно добавлен", status_code=303)
    except (IntegrityError, DataError, InternalError) as e:
        db.rollback()
        error_message = "Произошла ошибка при добавлении."
        original_error = getattr(e, 'orig', None)

        if original_error:
            error_str = str(original_error).lower()
            if "validate_staff_age" in error_str or "старше 18 лет" in error_str:
                error_message = "Ошибка: Сотруднику должно быть не менее 18 лет."
            elif "duplicate key value" in error_str:
                if "inn" in error_str:
                    error_message = "Ошибка: Сотрудник с таким ИНН уже существует."
                elif "snils" in error_str:
                    error_message = "Ошибка: Сотрудник с таким СНИЛС уже существует."
                else:
                    error_message = "Ошибка: Запись с такими уникальными данными уже существует."
            elif "value too long for type character varying" in error_str:
                # Более точная проверка для полей паспорта
                if "character varying(4)" in error_str:
                    error_message = "Ошибка: Серия паспорта не должна превышать 4 символа."
                elif "character varying(6)" in error_str:
                    error_message = "Ошибка: Номер паспорта не должен превышать 6 символов."
                elif "character varying(11)" in error_str:
                    error_message = "Ошибка: СНИЛС не должен превышать 11 символов."
                elif "character varying(12)" in error_str:
                    error_message = "Ошибка: ИНН не должен превышать 12 символов."
                else:
                    error_message = "Ошибка: Одно из текстовых полей слишком длинное."
            else:
                error_message = "Ошибка базы данных. Проверьте корректность введенных данных."
        
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


# --- ОСТАЛЬНЫЕ ФУНКЦИИ АДМИНИСТРАТОРА (без изменений) ---

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

@router.post("/add_training")
async def add_training(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
    name: str = Form(...),
    section_id: str = Form(...),
    start_time: datetime = Form(...),
    end_time: datetime = Form(...),
    is_group: bool = Form(False),
    trainer_id: str = Form(None),
    max_participants: Optional[int] = Form(None),
    client_id: Optional[str] = Form(None),
    allowed_subscription_type_ids: Optional[List[str]] = Form(None)
):
    try:
        if not is_group:
            if not client_id:
                return RedirectResponse(url="/admin/dashboard?error=Для индивидуальной тренировки необходимо выбрать клиента", status_code=303)
            new_training = models.Training(
                id=generate_id(), name=name, section_id=section_id,
                trainer_id=trainer_id if trainer_id else None,
                start_time=start_time, end_time=end_time,
                is_group=False, max_participants=1
            )
            db.add(new_training)
            db.flush()
            participant = models.TrainingParticipant(
                training_id=new_training.id, client_id=client_id, status_name='confirmed'
            )
            db.add(participant)
            message = "Индивидуальная тренировка создана и клиент записан"
        else:
            if not allowed_subscription_type_ids:
                return RedirectResponse(url="/admin/dashboard?error=Для групповой тренировки необходимо выбрать хотя бы один тип абонемента для доступа", status_code=303)
            if not max_participants or max_participants < 1:
                return RedirectResponse(url="/admin/dashboard?error=Для групповой тренировки необходимо указать лимит участников (больше 0)", status_code=303)
            allowed_subs = db.query(models.SubscriptionType).filter(
                models.SubscriptionType.id.in_(allowed_subscription_type_ids)
            ).all()
            new_training = models.Training(
                id=generate_id(), name=name, section_id=section_id,
                trainer_id=trainer_id if trainer_id else None,
                start_time=start_time, end_time=end_time,
                is_group=True, max_participants=max_participants,
                allowed_subscriptions=allowed_subs
            )
            db.add(new_training)
            message = "Групповая тренировка успешно создана"
        db.commit()
        return RedirectResponse(url=f"/admin/dashboard?message={message}", status_code=303)
    except Exception as e:
        db.rollback()
        print(f"ОШИБКА при создании тренировки: {e}")
        return RedirectResponse(url="/admin/dashboard?error=Произошла ошибка при создании тренировки", status_code=303)