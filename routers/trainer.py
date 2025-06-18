# routers/trainer.py
# --- Код исправлен и соответствует новой архитектуре ---

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import crud, models, get_db
from services.auth import require_role
from datetime import datetime

router = APIRouter()
ProtectedUser = Depends(require_role("trainer"))

@router.get("/dashboard", response_class=RedirectResponse)
async def trainer_dashboard(
    request: Request, 
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db)
):
    # Тренировки текущего тренера
    trainings = db.query(models.Training).filter(
        models.Training.trainer_id == user.staff_id,
        models.Training.start_time > datetime.now()
    ).order_by(models.Training.start_time).all()
    
    # Получаем клиентов для формы "Выдать выговор"
    clients = crud.get_clients(db)

    context = {
        "request": request,
        "trainings": trainings,
        "clients": clients
    }
    return request.app.state.templates.TemplateResponse("trainer.html", context)

@router.post("/add_attendance")
async def add_attendance(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    client_id: str = Form(...),
    training_id: str = Form(...)
):
    training = db.query(models.Training).get(training_id)
    if not training:
         return RedirectResponse(url="/trainer/dashboard?error=Тренировка не найдена", status_code=303)

    # Проверяем, есть ли уже открытое посещение
    existing_attendance = db.query(models.Attendance).filter_by(
        client_id=client_id, section_id=training.section_id, exit_time=None
    ).first()

    if existing_attendance:
        return RedirectResponse(url="/trainer/dashboard?message=Посещение для этого клиента уже отмечено", status_code=303)
        
    new_attendance = models.Attendance(
        client_id=client_id,
        section_id=training.section_id,
        entry_time=datetime.now()
    )
    db.add(new_attendance)
    db.commit()
    return RedirectResponse(url="/trainer/dashboard?message=Посещение отмечено", status_code=303)

@router.post("/add_warning")
async def add_warning(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    client_id: str = Form(...),
    reason: str = Form(...)
):
    new_warning = models.Warning(
        client_id=client_id,
        staff_id=user.staff_id,
        date=datetime.now().date(),
        reason=reason
    )
    db.add(new_warning)
    db.commit()
    return RedirectResponse(url="/trainer/dashboard?message=Выговор успешно выдан", status_code=303)