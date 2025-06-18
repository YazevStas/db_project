from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import crud, models
from database.session import get_db
from services.auth import get_current_user
from datetime import datetime

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def trainer_dashboard(
    request: Request, 
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "trainer":
        return RedirectResponse(url="/", status_code=303)
    
    # Получение тренировок текущего тренера
    trainings = db.query(models.Training).filter(
        models.Training.trainer_id == user.staff_id,
        models.Training.start_time > datetime.now()
    ).all()
    
    # Получение участников тренировок
    participants = {}
    for training in trainings:
        participants[training.id] = db.query(models.TrainingParticipant).filter(
            models.TrainingParticipant.training_id == training.id
        ).all()
    
    return request.app.templates.TemplateResponse(
        "trainer.html",
        {
            "request": request,
            "trainings": trainings,
            "participants": participants,
            "current_user": user
        }
    )

@router.post("/add_attendance")
async def add_attendance(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "trainer":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    new_attendance = models.Attendance(
        client_id=form_data.get("client_id"),
        section_id=form_data.get("section_id"),
        entry_time=datetime.now(),
        exit_time=None  # Выход будет отмечен позже
    )
    db.add(new_attendance)
    db.commit()
    return RedirectResponse(url="/trainer/dashboard", status_code=303)

@router.post("/mark_exit")
async def mark_exit(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "trainer":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    attendance = db.query(models.Attendance).filter(
        models.Attendance.client_id == form_data.get("client_id"),
        models.Attendance.section_id == form_data.get("section_id"),
        models.Attendance.entry_time == form_data.get("entry_time")
    ).first()
    
    if not attendance:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    attendance.exit_time = datetime.now()
    db.commit()
    return RedirectResponse(url="/trainer/dashboard", status_code=303)

@router.post("/add_warning")
async def add_warning(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "trainer":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    new_warning = models.Warning(
        client_id=form_data.get("client_id"),
        staff_id=user.staff_id,
        date=datetime.now().date(),
        reason=form_data.get("reason")
    )
    db.add(new_warning)
    db.commit()
    return RedirectResponse(url="/trainer/dashboard", status_code=303)