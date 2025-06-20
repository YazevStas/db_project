from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from typing import Optional

from database import crud, models, get_db
from services.auth import require_role

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
    last_name: str = Form(...), first_name: str = Form(...), middle_name: str = Form(None),
    discount: float = Form(...), phone: str = Form(None)
):
    client = crud.get_client(db, client_id=client_id)
    if not client:
        return RedirectResponse(url="/manager/dashboard?error=Клиент не найден", status_code=303)
    
    client.last_name, client.first_name, client.middle_name, client.discount = last_name, first_name, middle_name, discount
    phone_contact = db.query(models.ClientContact).filter_by(client_id=client.id, contact_type='phone').first()
    if phone:
        if phone_contact: phone_contact.contact_value = phone
        else: db.add(models.ClientContact(client_id=client.id, contact_type='phone', contact_value=phone))
    elif phone_contact: db.delete(phone_contact)
    db.commit()
    return RedirectResponse(url="/manager/dashboard?message=Данные клиента обновлены", status_code=303)


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
    last_name: str = Form(...), first_name: str = Form(...), middle_name: str = Form(None),
    birth_date: str = Form(...), gender: str = Form(...), phone: str = Form(None),
    passport_series: str = Form(None), passport_number: str = Form(None),
    address: str = Form(None), education: str = Form(None),
    inn: str = Form(...), snils: str = Form(...), hire_date: str = Form(...),
    position_id: str = Form(...), salary: float = Form(None)
):
    staff = crud.get_single_staff(db, staff_id=staff_id)
    if not staff:
        return RedirectResponse(url="/manager/dashboard?error=Сотрудник не найден", status_code=303)

    # Обновляем все поля
    staff.last_name, staff.first_name, staff.middle_name = last_name, first_name, middle_name
    staff.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
    staff.gender, staff.phone = gender, phone
    staff.passport_series, staff.passport_number = passport_series, passport_number
    staff.address, staff.education = address, education
    staff.inn, staff.snils = inn, snils
    staff.hire_date = datetime.strptime(hire_date, '%Y-%m-%d').date()
    staff.position_id, staff.salary = position_id, salary
    
    db.commit()
    return RedirectResponse(url="/manager/dashboard?message=Данные сотрудника обновлены", status_code=303)