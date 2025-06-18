from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import crud, models
from database.session import get_db
from services.auth import get_current_user
from services.utils import generate_id

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def tech_admin_dashboard(
    request: Request, 
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "tech_admin":
        return RedirectResponse(url="/", status_code=303)
    
    equipment = db.query(models.Equipment).all()
    sections = crud.get_sections(db)
    
    return request.app.templates.TemplateResponse(
        "tech_admin.html",
        {
            "request": request,
            "equipment": equipment,
            "sections": sections,
            "current_user": user
        }
    )

@router.post("/add_equipment")
async def add_equipment(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "tech_admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    new_equipment = models.Equipment(
        id=generate_id(),
        section_id=form_data.get("section_id"),
        name=form_data.get("name"),
        model=form_data.get("model"),
        purchase_date=form_data.get("purchase_date"),
        warranty_months=int(form_data.get("warranty_months")),
        quantity=int(form_data.get("quantity"))
    )
    db.add(new_equipment)
    db.commit()
    return RedirectResponse(url="/tech_admin/dashboard", status_code=303)

@router.post("/update_equipment/{equipment_id}")
async def update_equipment(
    equipment_id: str,
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "tech_admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    equipment = db.query(models.Equipment).filter(models.Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    equipment.name = form_data.get("name", equipment.name)
    equipment.model = form_data.get("model", equipment.model)
    equipment.quantity = int(form_data.get("quantity", equipment.quantity))
    
    db.commit()
    return RedirectResponse(url="/tech_admin/dashboard", status_code=303)