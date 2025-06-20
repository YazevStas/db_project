from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Optional

from database import crud, models, get_db
from services.auth import require_role
from services.utils import generate_id

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def tech_admin_dashboard(
    request: Request,
    user: models.User = Depends(require_role("tech_admin")),
    db: Session = Depends(get_db)
):
    equipment_list = db.query(models.Equipment).all()
    sections = crud.get_sections(db)

    # Добавляем рассчитанную дату окончания эксплуатации
    for item in equipment_list:
        if item.purchase_date and item.warranty_months:
            item.end_of_life_date = item.purchase_date + relativedelta(months=item.warranty_months)
        else:
            item.end_of_life_date = None

    context = {
        "request": request,
        "current_user": user,
        "equipment_list": equipment_list,
        "sections": sections,
        "now": datetime.now().date()
    }
    return request.app.state.templates.TemplateResponse("tech_admin.html", context)

@router.post("/add_equipment")
async def add_equipment(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("tech_admin")),
    name: str = Form(...),
    model: str = Form(None),
    section_id: str = Form(...),
    purchase_date: str = Form(...),
    warranty_months: int = Form(...),
    last_maintenance_date: Optional[str] = Form(None),
    quantity: int = Form(...)
):
    # Преобразуем строки в даты вручную
    try:
        purchase_date_obj = datetime.strptime(purchase_date, '%Y-%m-%d').date()
        
        last_maintenance_date_obj = None
        # Проверяем, что строка не пустая, перед преобразованием
        if last_maintenance_date:
            last_maintenance_date_obj = datetime.strptime(last_maintenance_date, '%Y-%m-%d').date()
    except ValueError:
        # Если формат даты неправильный
        return RedirectResponse(url="/tech_admin/dashboard?error=Неверный формат даты. Используйте ГГГГ-ММ-ДД.", status_code=303)

    new_equipment = models.Equipment(
        id=generate_id(),
        name=name,
        model=model,
        section_id=section_id,
        purchase_date=purchase_date_obj,
        warranty_months=warranty_months,
        last_maintenance_date=last_maintenance_date_obj,
        quantity=quantity
    )
    db.add(new_equipment)
    db.commit()
    return RedirectResponse(url="/tech_admin/dashboard?message=Оборудование успешно добавлено", status_code=303)

@router.post("/increase_quantity/{equipment_id}")
async def increase_quantity(
    equipment_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("tech_admin")),
    amount: int = Form(...)
):
    equipment = db.query(models.Equipment).filter_by(id=equipment_id).first()
    if not equipment:
        return RedirectResponse(url="/tech_admin/dashboard?error=Оборудование не найдено", status_code=303)
    
    if amount <= 0:
        return RedirectResponse(url="/tech_admin/dashboard?error=Количество для добавления должно быть положительным", status_code=303)

    equipment.quantity += amount
    db.commit()
    return RedirectResponse(url=f"/tech_admin/dashboard?message=Количество для '{equipment.name}' увеличено на {amount}", status_code=303)