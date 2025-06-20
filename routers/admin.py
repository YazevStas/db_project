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
    # --- 1. ЗАГРУЗКА ДАННЫХ ---
    # Загружаем все данные, которые нам понадобятся на странице
    all_clients = db.query(models.Client).options(joinedload(models.Client.contacts)).order_by(models.Client.last_name).all()
    all_staff = db.query(models.Staff).options(joinedload(models.Staff.position)).order_by(models.Staff.last_name).all()
    all_client_subscriptions = db.query(models.ClientSubscription).options(joinedload(models.ClientSubscription.client), joinedload(models.ClientSubscription.subscription_type), joinedload(models.ClientSubscription.status)).all()
    all_sections = db.query(models.Section).order_by(models.Section.name).all()
    
    # Загружаем тренировки и все связанные с ними данные одним запросом
    all_trainings = db.query(models.Training).options(
        joinedload(models.Training.section), 
        joinedload(models.Training.trainer), 
        joinedload(models.Training.allowed_subscriptions), 
        joinedload(models.Training.participants).joinedload(models.TrainingParticipant.client)
    ).order_by(models.Training.start_time.desc()).all()
    
    # --- 2. ОТЛАДОЧНЫЙ ВЫВОД В КОНСОЛЬ ---
    # Этот блок поможет нам понять, правильно ли сохраняются связи
    print("\n--- ОТЛАДКА ТРЕНИРОВОК В АДМИНКЕ ---")
    for t in all_trainings:
        allowed_subs_names = [s.name for s in t.allowed_subscriptions]
        trainer_name = f"{t.trainer.first_name} {t.trainer.last_name}" if t.trainer else "НЕТ"
        print(f"Тренировка '{t.name}' (ID: {t.id}), Тренер: {trainer_name} (ID: {t.trainer_id}), Доступ для: {allowed_subs_names}")
    print("--- КОНЕЦ ОТЛАДКИ ---\n")

    # --- 3. ДАННЫЕ ДЛЯ ФОРМ В МОДАЛЬНЫХ ОКНАХ ---
    all_subscription_types = db.query(models.SubscriptionType).order_by(models.SubscriptionType.name).all()
    all_trainers = db.query(models.Staff).join(models.Position).filter(models.Position.name == 'Тренер').all()
    all_positions = db.query(models.Position).all()
    all_statuses = db.query(models.Status).all()
    
    # --- 4. ФОРМИРОВАНИЕ КОНТЕКСТА ДЛЯ ШАБЛОНА ---
    context = {
        "request": request,
        "current_user": user,
        
        # Переменные для отображения в таблицах
        "clients": all_clients,
        "staff": all_staff,
        "client_subscriptions": all_client_subscriptions,
        "sections": all_sections,
        "trainings": all_trainings,
        
        # Переменные для выпадающих списков в формах
        "all_clients": all_clients, 
        "all_subscription_types": all_subscription_types,
        "all_sections": all_sections,
        "trainers": all_trainers,
        "all_statuses": all_statuses,
        "positions": all_positions,
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
    # Все поля из формы
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
    # --- БЛОК ПРЕДВАРИТЕЛЬНОЙ ВАЛИДАЦИИ ---

    # 1. Проверка обязательных полей
    if not position_id:
        return RedirectResponse(url="/admin/dashboard?error=Необходимо выбрать должность.", status_code=303)

    # 2. Валидация ИНН (строго 12 цифр)
    if not (inn and inn.isdigit() and len(inn) == 12):
        return RedirectResponse(url="/admin/dashboard?error=ИНН должен состоять ровно из 12 цифр.", status_code=303)
        
    # 3. Валидация СНИЛС (строго 11 цифр)
    if not (snils and snils.isdigit() and len(snils) == 11):
        return RedirectResponse(url="/admin/dashboard?error=СНИЛС должен состоять ровно из 11 цифр.", status_code=303)

    # 4. Валидация паспорта (если поля заполнены)
    if passport_series and not (passport_series.isdigit() and len(passport_series) == 4):
        return RedirectResponse(url="/admin/dashboard?error=Серия паспорта должна состоять ровно из 4 цифр.", status_code=303)
    if passport_number and not (passport_number.isdigit() and len(passport_number) == 6):
        return RedirectResponse(url="/admin/dashboard?error=Номер паспорта должен состоять ровно из 6 цифр.", status_code=303)

    # 5. Валидация дат
    try:
        birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
        hire_date_obj = datetime.strptime(hire_date, '%Y-%m-%d').date()
    except ValueError:
        return RedirectResponse(url="/admin/dashboard?error=Неверный формат даты. Используйте ГГГГ-ММ-ДД.", status_code=303)

    # Проверка, что дата приема не в будущем
    if hire_date_obj > datetime.now().date():
        return RedirectResponse(url="/admin/dashboard?error=Дата приема на работу не может быть в будущем.", status_code=303)
    
    # Проверка возраста (18 лет)
    # Используем `relativedelta` для точного расчета
    from dateutil.relativedelta import relativedelta
    age = relativedelta(datetime.now().date(), birth_date_obj).years
    if age < 18:
        return RedirectResponse(url="/admin/dashboard?error=Сотруднику должно быть не менее 18 лет.", status_code=303)


    # --- КОНЕЦ БЛОКА ВАЛИДАЦИИ ---

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
        # Этот блок теперь будет ловить в основном только ошибки уникальности (дубликаты)
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