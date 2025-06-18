from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import crud, models
from database.session import get_db
from services.auth import get_current_user
from datetime import datetime
from services.utils import generate_id

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def manager_dashboard(
    request: Request, 
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "manager":
        return RedirectResponse(url="/", status_code=303)
    
    clients = crud.get_clients(db)
    subscriptions = crud.get_subscriptions(db)
    trainings = crud.get_upcoming_trainings(db)
    sections = crud.get_sections(db)
    
    return request.app.templates.TemplateResponse(
        "manager.html",
        {
            "request": request,
            "clients": clients,
            "subscriptions": subscriptions,
            "trainings": trainings,
            "sections": sections,
            "current_user": user
        }
    )

@router.post("/add_training")
async def add_training(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "manager":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    new_training = models.Training(
        id=generate_id(),
        section_id=form_data.get("section_id"),
        trainer_id=form_data.get("trainer_id"),
        training_type=form_data.get("training_type"),
        start_time=datetime.strptime(form_data.get("start_time"), "%Y-%m-%dT%H:%M"),
        end_time=datetime.strptime(form_data.get("end_time"), "%Y-%m-%dT%H:%M"),
        max_participants=int(form_data.get("max_participants", 0))
    )
    db.add(new_training)
    db.commit()
    return RedirectResponse(url="/manager/dashboard", status_code=303)

@router.post("/update_client_discount")
async def update_client_discount(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "manager":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    client_id = form_data.get("client_id")
    discount = float(form_data.get("discount", 0))
    
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client.discount = discount
    db.commit()
    return RedirectResponse(url="/manager/dashboard", status_code=303)