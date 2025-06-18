# routers/client.py
# --- Упрощена логика, используются правильные зависимости ---

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import crud, models, get_db
from services.auth import require_role
from datetime import datetime

router = APIRouter()
ProtectedUser = Depends(require_role("client"))

@router.get("/dashboard", response_class=RedirectResponse)
async def client_dashboard(
    request: Request, 
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db)
):
    client = crud.get_client(db, user.client_id)
    subscriptions = crud.get_client_subscriptions(db, user.client_id)
    attendances = crud.get_client_attendances(db, user.client_id)
    
    # Все доступные тренировки для записи
    available_trainings = db.query(models.Training).filter(
        models.Training.start_time > datetime.now()
    ).all()
    
    context = {
        "request": request,
        "client": client,
        "subscriptions": subscriptions,
        "attendances": attendances,
        "available_trainings": available_trainings
    }
    return request.app.state.templates.TemplateResponse("client.html", context)

@router.post("/update_profile")
async def update_profile(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: str = Form(None)
    # Контакты можно добавить как отдельные поля, если нужно
):
    client = crud.get_client(db, user.client_id)
    if client:
        client.last_name = last_name
        client.first_name = first_name
        client.middle_name = middle_name
        db.commit()
        return RedirectResponse(url="/client/dashboard?message=Профиль успешно обновлен", status_code=303)
    return RedirectResponse(url="/client/dashboard?error=Клиент не найден", status_code=303)

@router.post("/book_training")
async def book_training(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    training_id: str = Form(...)
):
    # Проверка, не записан ли уже клиент
    existing_booking = db.query(models.TrainingParticipant).filter_by(
        training_id=training_id, client_id=user.client_id
    ).first()
    
    if existing_booking:
        return RedirectResponse(url="/client/dashboard?error=Вы уже записаны на эту тренировку", status_code=303)
    
    # Проверка лимита участников (триггер в БД должен это делать, но дублируем для UX)
    training = db.query(models.Training).get(training_id)
    current_participants = db.query(models.TrainingParticipant).filter_by(training_id=training_id).count()

    if current_participants >= training.max_participants:
         return RedirectResponse(url="/client/dashboard?error=На тренировку нет мест", status_code=303)

    new_booking = models.TrainingParticipant(
        training_id=training_id,
        client_id=user.client_id,
        status_name="confirmed"
    )
    db.add(new_booking)
    db.commit()
    return RedirectResponse(url="/client/dashboard?message=Вы успешно записаны на тренировку", status_code=303)