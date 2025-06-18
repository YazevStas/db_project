# routers/manager.py
# --- Код исправлен и соответствует новой архитектуре ---

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import crud, models, get_db
from services.auth import require_role
from datetime import datetime

router = APIRouter()
ProtectedUser = Depends(require_role("manager"))

@router.get("/dashboard", response_class=RedirectResponse)
async def manager_dashboard(
    request: Request, 
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db)
):
    clients = crud.get_clients(db)
    subscriptions = crud.get_subscriptions(db)
    trainings = crud.get_upcoming_trainings(db)
    sections = crud.get_sections(db)
    
    context = {
        "request": request,
        "clients": clients,
        "subscriptions": subscriptions,
        "trainings": trainings,
        "sections": sections
    }
    return request.app.state.templates.TemplateResponse("manager.html", context)

@router.post("/add_training")
async def add_training(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    section_id: str = Form(...),
    trainer_id: str = Form(None),
    training_type: str = Form(...),
    start_time: datetime = Form(...),
    end_time: datetime = Form(...),
    max_participants: int = Form(...)
):
    training = models.Training(
        id=crud.generate_id(), section_id=section_id, trainer_id=trainer_id,
        training_type=training_type, start_time=start_time, end_time=end_time,
        max_participants=max_participants
    )
    db.add(training)
    db.commit()
    return RedirectResponse(url="/manager/dashboard?message=Тренировка успешно добавлена", status_code=303)

@router.post("/update_client_discount")
async def update_client_discount(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    client_id: str = Form(...),
    discount: float = Form(...)
):
    client = crud.get_client(db, client_id)
    if client:
        client.discount = discount
        db.commit()
        return RedirectResponse(url="/manager/dashboard?message=Скидка для клиента обновлена", status_code=303)
    return RedirectResponse(url="/manager/dashboard?error=Клиент не найден", status_code=303)