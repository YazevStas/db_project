# routers/tech_admin.py
# --- Код исправлен и соответствует новой архитектуре ---

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import crud, models, get_db
from services.auth import require_role
from datetime import datetime

router = APIRouter()
ProtectedUser = Depends(require_role("tech_admin"))

@router.get("/dashboard", response_class=RedirectResponse)
async def tech_admin_dashboard(
    request: Request, 
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db)
):
    equipment = db.query(models.Equipment).all()
    sections = crud.get_sections(db)
    
    context = {
        "request": request,
        "equipment": equipment,
        "sections": sections
    }
    return request.app.state.templates.TemplateResponse("tech_admin.html", context)

@router.post("/add_equipment")
async def add_equipment(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    section_id: str = Form(...),
    name: str = Form(...),
    model: str = Form(...),
    purchase_date: datetime = Form(...),
    warranty_months: int = Form(...),
    quantity: int = Form(...)
):
    new_equipment = models.Equipment(
        id=crud.generate_id(), section_id=section_id, name=name, model=model,
        purchase_date=purchase_date.date(), warranty_months=warranty_months,
        quantity=quantity
    )
    db.add(new_equipment)
    db.commit()
    return RedirectResponse(url="/tech_admin/dashboard?message=Оборудование успешно добавлено", status_code=303)

@router.post("/update_equipment/{equipment_id}")
async def update_equipment(
    equipment_id: str,
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    name: str = Form(...),
    model: str = Form(...),
    quantity: int = Form(...)
):
    equipment = db.query(models.Equipment).filter_by(id=equipment_id).first()
    if equipment:
        equipment.name = name
        equipment.model = model
        equipment.quantity = quantity
        db.commit()
        return RedirectResponse(url="/tech_admin/dashboard?message=Оборудование обновлено", status_code=303)
    return RedirectResponse(url="/tech_admin/dashboard?error=Оборудование не найдено", status_code=303)