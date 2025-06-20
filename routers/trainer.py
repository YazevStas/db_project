# routers/trainer.py

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from database import models, get_db
from services.auth import require_role

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def trainer_dashboard(
    request: Request,
    user: models.User = Depends(require_role("trainer")), # Защищаем эндпоинт
    db: Session = Depends(get_db)
):
    # 1. Находим все будущие тренировки, где 'trainer_id' совпадает с ID текущего пользователя
    #    используем joinedload для эффективной загрузки связанных данных
    my_upcoming_trainings = db.query(models.Training).options(
        joinedload(models.Training.section),
        joinedload(models.Training.participants).joinedload(models.TrainingParticipant.client)
    ).filter(
        models.Training.trainer_id == user.staff_id,
        models.Training.start_time > datetime.now()
    ).order_by(
        models.Training.start_time
    ).all()

    # 2. Формируем контекст для передачи в шаблон
    context = {
        "request": request,
        "current_user": user,
        "trainings": my_upcoming_trainings
    }

    # 3. Рендерим шаблон
    return request.app.state.templates.TemplateResponse("trainer.html", context)