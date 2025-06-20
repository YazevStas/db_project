from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import Optional

from database import crud, models, get_db
from services.auth import require_role

from sqlalchemy.exc import IntegrityError, DataError, InternalError

router = APIRouter()

# --- Главная панель менеджера ---
@router.get("/dashboard", response_class=HTMLResponse)
async def manager_dashboard(
    request: Request,
    user: models.User = Depends(require_role("manager")),
    db: Session = Depends(get_db)
):
    all_clients = db.query(models.Client).options(joinedload(models.Client.contacts)).order_by(models.Client.last_name).all()
    all_staff = db.query(models.Staff).options(joinedload(models.Staff.position)).order_by(models.Staff.last_name).all()
    
    context = {
        "request": request,
        "current_user": user,
        "clients": all_clients,
        "staff": all_staff,
    }
    return request.app.state.templates.TemplateResponse("manager.html", context)


# --- УПРАВЛЕНИЕ КЛИЕНТАМИ (для Менеджера) ---
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
async def update_client(
    client_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("manager")),
    # Аргументы из формы
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: Optional[str] = Form(None),
    discount: float = Form(...),
    phone: Optional[str] = Form(None),
    # Добавим email для полноты, даже если его нет в форме сейчас
    email: Optional[str] = Form(None) 
):
    # --- БЛОК ВАЛИДАЦИИ ТЕЛЕФОНА ---
    phone_to_save = None
    if phone and phone.strip(): # Проверяем, что поле не пустое и не состоит из пробелов
        # Убираем все символы, кроме цифр и знака '+'
        cleaned_phone = "".join(filter(lambda char: char.isdigit() or char == '+', phone.strip()))
        
        # Проверяем, начинается ли номер с '+'
        if cleaned_phone.startswith('+'):
            if len(cleaned_phone) != 12 or not cleaned_phone[1:].isdigit():
                error = "Формат телефона: '+' и 11 цифр (например, +79991234567)."
                # Редирект обратно на страницу редактирования с ошибкой
                return RedirectResponse(url=f"/manager/client/{client_id}/edit?error={error}", status_code=303)
        # Проверяем, начинается ли номер с '8'
        elif cleaned_phone.startswith('8'):
            if len(cleaned_phone) != 11 or not cleaned_phone.isdigit():
                error = "Формат телефона: '8' и 10 цифр (например, 89991234567)."
                return RedirectResponse(url=f"/manager/client/{client_id}/edit?error={error}", status_code=303)
        # Если номер начинается с чего-то другого
        else:
            error = "Номер телефона должен начинаться с '+' или '8'."
            return RedirectResponse(url=f"/manager/client/{client_id}/edit?error={error}", status_code=303)
        
        # Если валидация пройдена, используем очищенный номер
        phone_to_save = cleaned_phone
    # --- КОНЕЦ БЛОКА ВАЛИДАЦИИ ---

    # Загружаем клиента вместе с его контактами для эффективного обновления
    client = db.query(models.Client).options(joinedload(models.Client.contacts)).filter_by(id=client_id).first()
    if not client:
        return RedirectResponse(url="/manager/dashboard?error=Клиент не найден", status_code=303)
    
    # Обновляем основные данные клиента
    client.last_name = last_name
    client.first_name = first_name
    client.middle_name = middle_name
    client.discount = discount

    # Обновляем или создаем/удаляем контакты
    contact_details = {"phone": phone_to_save, "email": email}
    for c_type, c_value in contact_details.items():
        # Находим существующий контакт этого типа (если он есть)
        existing_contact = next((c for c in client.contacts if c.contact_type == c_type), None)
        
        if c_value and c_value.strip(): # Если передано непустое значение
            if existing_contact:
                existing_contact.contact_value = c_value # Обновляем
            else:
                # Создаем новый контакт
                db.add(models.ClientContact(client_id=client_id, contact_type=c_type, contact_value=c_value))
        elif existing_contact:
            # Если значение не передано (или пустое), а контакт в базе есть - удаляем его
            db.delete(existing_contact)
            
    db.commit()
    return RedirectResponse(url="/manager/dashboard?message=Данные клиента успешно обновлены", status_code=303)


# --- УПРАВЛЕНИЕ СОТРУДНИКАМИ (Обновлено) ---

@router.get("/staff/{staff_id}/edit", response_class=HTMLResponse)
async def edit_staff_form(
    request: Request,
    staff_id: str,
    user: models.User = Depends(require_role("manager")),
    db: Session = Depends(get_db)
):
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
    # ... (все Form-поля)
    last_name: str = Form(...), first_name: str = Form(...), middle_name: Optional[str] = Form(None),
    birth_date: str = Form(...), gender: str = Form(...), phone: Optional[str] = Form(None),
    passport_series: Optional[str] = Form(None), passport_number: Optional[str] = Form(None),
    address: Optional[str] = Form(None), education: Optional[str] = Form(None),
    inn: str = Form(...), snils: str = Form(...), hire_date: str = Form(...),
    position_id: str = Form(...), salary: Optional[float] = Form(None)
):
    # --- БЛОК ВАЛИДАЦИИ ДАННЫХ ИЗ ФОРМЫ ---
    
    # 1. Валидация телефона (уже есть)
    phone_to_save = None
    if phone and phone.strip():
        # ... (код валидации телефона без изменений)
        cleaned_phone = "".join(filter(lambda char: char.isdigit() or char == '+', phone.strip()))
        if cleaned_phone.startswith('+'):
            if len(cleaned_phone) != 12 or not cleaned_phone[1:].isdigit():
                error = "Формат телефона: '+' и 11 цифр."
                return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error={error}", status_code=303)
        elif cleaned_phone.startswith('8'):
            if len(cleaned_phone) != 11 or not cleaned_phone.isdigit():
                error = "Формат телефона: '8' и 10 цифр."
                return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error={error}", status_code=303)
        else:
            error = "Номер телефона должен начинаться с '+' или '8'."
            return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error={error}", status_code=303)
        phone_to_save = cleaned_phone

    # 2. НОВАЯ ВАЛИДАЦИЯ: Дата приема на работу
    try:
        hire_date_obj = datetime.strptime(hire_date, '%Y-%m-%d').date()
        if hire_date_obj > datetime.now().date():
            error = "Дата приема на работу не может быть в будущем."
            return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error={error}", status_code=303)
    except ValueError:
        error = "Некорректный формат даты приема на работу."
        return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error={error}", status_code=303)

    # 3. Преобразование даты рождения
    try:
        birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d').date()
    except ValueError:
        error = "Некорректный формат даты рождения."
        return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error={error}", status_code=303)

    # --- КОНЕЦ БЛОКА ВАЛИДАЦИИ ---

    staff = crud.get_single_staff(db, staff_id=staff_id)
    if not staff:
        return RedirectResponse(url="/manager/dashboard?error=Сотрудник не найден", status_code=303)

    try:
        # Обновляем все поля, используя уже проверенные и преобразованные данные
        staff.last_name, staff.first_name, staff.middle_name = last_name, first_name, middle_name
        staff.birth_date = birth_date_obj
        staff.gender, staff.phone = gender, phone_to_save
        staff.passport_series, staff.passport_number = passport_series, passport_number
        staff.address, staff.education = address, education
        staff.inn, staff.snils = inn, snils
        staff.hire_date = hire_date_obj
        staff.position_id, staff.salary = position_id, salary
        
        db.commit()
        return RedirectResponse(url="/manager/dashboard?message=Данные сотрудника обновлены", status_code=303)

    except (IntegrityError, DataError, InternalError) as e:
        db.rollback()
        # ... (код обработки ошибок возраста и т.д. остается без изменений) ...
        error_message = "Произошла ошибка при обновлении."
        original_error = getattr(e, 'orig', None)
        if original_error:
            error_str = str(original_error).lower()
            if "validate_staff_age" in error_str or "старше 18 лет" in error_str:
                error_message = "Ошибка: Сотруднику должно быть не менее 18 лет."
            elif "duplicate key value" in error_str:
                error_message = "Ошибка: Сотрудник с таким ИНН или СНИЛС уже существует."
            else:
                error_message = "Ошибка базы данных. Проверьте корректность введенных данных."
        return RedirectResponse(url=f"/manager/staff/{staff_id}/edit?error={error_message}", status_code=303)