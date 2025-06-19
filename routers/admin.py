# routers/admin.py

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, DataError, InternalError
from typing import List, Optional
from datetime import datetime

from database import crud, models, get_db
from services.auth import require_role
from services.utils import generate_id

router = APIRouter()

# Мы убрали глобальное определение ProtectedUser отсюда

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    user: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    # Загружаем все данные, которые нам понадобятся на странице
    
    # Данные для таблиц
    all_clients = db.query(models.Client).order_by(models.Client.last_name).all()
    all_staff = db.query(models.Staff).options(joinedload(models.Staff.position)).order_by(models.Staff.last_name).all()
    all_client_subscriptions = db.query(models.ClientSubscription).options(joinedload(models.ClientSubscription.client), joinedload(models.ClientSubscription.subscription_type), joinedload(models.ClientSubscription.status)).all()
    all_sections = db.query(models.Section).order_by(models.Section.name).all()
    all_trainings = db.query(models.Training).options(joinedload(models.Training.section), joinedload(models.Training.trainer), joinedload(models.Training.allowed_subscriptions), joinedload(models.Training.participants).joinedload(models.TrainingParticipant.client)).order_by(models.Training.start_time.desc()).all()
    
    # Данные для выпадающих списков в модальных окнах
    all_subscription_types = db.query(models.SubscriptionType).order_by(models.SubscriptionType.name).all()
    all_trainers = db.query(models.Staff).join(models.Position).filter(models.Position.name == 'Тренер').all()
    all_positions = db.query(models.Position).all()
    all_statuses = db.query(models.Status).all()
    
    context = {
        "request": request,
        "current_user": user,
        
        # Переменные для отображения в таблицах
        "clients": all_clients,
        "staff": all_staff,
        "client_subscriptions": all_client_subscriptions,
        "sections": all_sections,
        "trainings": all_trainings,
        
        # Переменные для форм в модальных окнах
        "all_clients": all_clients,
        "all_subscription_types": all_subscription_types,
        "all_sections": all_sections,
        "trainers": all_trainers,
        "all_statuses": all_statuses,
        "positions": all_positions,
    }
    return request.app.state.templates.TemplateResponse("admin.html", context)

# Применяем тот же паттерн для всех остальных функций в этом файле
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

@router.post("/add_staff")
async def add_staff(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: str = Form(None),
    birth_date: datetime = Form(...),
    gender: str = Form(...),
    inn: str = Form(...),
    snils: str = Form(...),
    hire_date: datetime = Form(...),
    position_id: str = Form(...)
):
    staff_data = {
        "last_name": last_name, "first_name": first_name, "middle_name": middle_name,
        "birth_date": birth_date.date(), "gender": gender, "inn": inn, "snils": snils,
        "hire_date": hire_date.date(), "position_id": position_id
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
                error_message = "Сотруднику должно быть не менее 18 лет."
            elif "value too long" in error_str or "не умещается в тип" in error_str:
                error_message = "Одно из полей слишком длинное. Проверьте ИНН (12 цифр) и СНИЛС (11 цифр)."
            elif "duplicate key value" in error_str:
                error_message = "Сотрудник с таким ИНН или СНИЛС уже существует."
            else:
                error_message = "Ошибка базы данных. Проверьте корректность введенных данных."
        return RedirectResponse(url=f"/admin/dashboard?error={error_message}", status_code=303)

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

@router.post("/sell_subscription")
async def sell_subscription(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
    client_id: str = Form(...),
    subscription_type_id: str = Form(...),
    start_date: datetime = Form(...),
    end_date: datetime = Form(...)
):
    client_sub = models.ClientSubscription(
        id=generate_id(), client_id=client_id, subscription_type_id=subscription_type_id,
        start_date=start_date.date(), end_date=end_date.date(), status_name='active'
    )
    db.add(client_sub)
    db.commit()
    return RedirectResponse(url="/admin/dashboard?message=Абонемент продан клиенту", status_code=303)

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
    # Поля, которые могут быть не переданы
    max_participants: Optional[int] = Form(None),
    client_id: Optional[str] = Form(None),
    allowed_subscription_type_ids: Optional[List[str]] = Form(None)
):
    try:
        # --- Сценарий 1: Индивидуальная тренировка ---
        if not is_group:
            if not client_id:
                return RedirectResponse(url="/admin/dashboard?error=Для индивидуальной тренировки необходимо выбрать клиента", status_code=303)
            
            # Создаем тренировку с лимитом 1
            new_training = models.Training(
                id=generate_id(), name=name, section_id=section_id,
                trainer_id=trainer_id if trainer_id else None,
                start_time=start_time, end_time=end_time,
                is_group=False, max_participants=1
            )
            db.add(new_training)
            db.flush() # Получаем ID тренировки до коммита

            # Сразу записываем на нее выбранного клиента
            participant = models.TrainingParticipant(
                training_id=new_training.id, client_id=client_id, status_name='confirmed'
            )
            db.add(participant)
            message = "Индивидуальная тренировка создана и клиент записан"

        # --- Сценарий 2: Групповая тренировка ---
        else:
            if not allowed_subscription_type_ids:
                return RedirectResponse(url="/admin/dashboard?error=Для групповой тренировки необходимо выбрать хотя бы один тип абонемента для доступа", status_code=303)
            if not max_participants or max_participants < 1:
                return RedirectResponse(url="/admin/dashboard?error=Для групповой тренировки необходимо указать лимит участников (больше 0)", status_code=303)

            # Находим типы абонементов по ID
            allowed_subs = db.query(models.SubscriptionType).filter(
                models.SubscriptionType.id.in_(allowed_subscription_type_ids)
            ).all()

            # Создаем тренировку и привязываем к ней правила доступа
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

    except Exception as e:
        db.rollback()
        print(f"ОШИБКА при создании тренировки: {e}")
        return RedirectResponse(url="/admin/dashboard?error=Произошла ошибка при создании тренировки", status_code=303)

@router.get("/client/{client_id}/edit", response_class=HTMLResponse)
async def edit_client_form(
    request: Request,
    client_id: str,
    user: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    client = crud.get_client(db, client_id=client_id)
    if not client:
        return RedirectResponse(url="/admin/dashboard?error=Клиент не найден", status_code=303)
    context = {"request": request, "client": client}
    return request.app.state.templates.TemplateResponse("edit_client.html", context)

@router.post("/client/{client_id}/edit")
async def update_client(
    client_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("admin")),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: str = Form(None),
    discount: float = Form(...)
):
    client = crud.get_client(db, client_id=client_id)
    if client:
        client.last_name = last_name
        client.first_name = first_name
        client.middle_name = middle_name
        client.discount = discount
        db.commit()
        return RedirectResponse(url="/admin/dashboard?message=Данные клиента успешно обновлены", status_code=303)
    return RedirectResponse(url="/admin/dashboard?error=Клиент не найден", status_code=303)