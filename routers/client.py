# routers/client.py

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import Optional

from database import crud, models, get_db
from services.auth import require_role

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def client_dashboard(
    request: Request,
    user: models.User = Depends(require_role("client")),
    db: Session = Depends(get_db)
):
    # 1. Загружаем клиента и его связанные данные
    client = db.query(models.Client).options(
        joinedload(models.Client.subscriptions).joinedload(models.ClientSubscription.subscription_type),
        joinedload(models.Client.participants)
    ).filter_by(id=user.client_id).first()

    if not client:
        return RedirectResponse(url="/?error=Не удалось найти данные клиента.", status_code=303)

    # 2. Логика определения доступных тренировок
    active_subscription_type_ids = {
        sub.subscription_type_id 
        for sub in client.subscriptions 
        if sub.status_name == 'active' and sub.end_date >= datetime.now().date()
    }
    
    my_training_ids = {p.training_id for p in client.participants}
    
    available_trainings = []
    if active_subscription_type_ids:
        # --- ФИНАЛЬНАЯ ИСПРАВЛЕННАЯ ЛОГИКА ЗАПРОСА ---
        # Находим все будущие тренировки, которые...
        query = db.query(models.Training).filter(
            models.Training.start_time > datetime.now(),
            # ...имеют хотя бы один разрешенный абонемент из списка активных у клиента
            models.Training.allowed_subscriptions.any(
                models.SubscriptionType.id.in_(active_subscription_type_ids)
            )
        )

        # Если у клиента уже есть записи, добавляем условие для их исключения
        if my_training_ids:
            query = query.filter(~models.Training.id.in_(my_training_ids))
        
        available_trainings = query.order_by(models.Training.start_time).all()

    # 3. Формирование контекста для шаблона
    my_trainings = db.query(models.Training).join(models.TrainingParticipant).filter(
        models.TrainingParticipant.client_id == user.client_id
    ).order_by(models.Training.start_time).all()

    context = {
        "request": request, "current_user": user, "client": client,
        "subscriptions": client.subscriptions, "my_trainings": my_trainings,
        "available_trainings": available_trainings
    }
    return request.app.state.templates.TemplateResponse("client.html", context)


# Эндпоинт для записи на тренировку. Добавим такую же проверку доступа.
@router.post("/book_training")
async def book_training(
    user: models.User = Depends(require_role("client")),
    db: Session = Depends(get_db),
    training_id: str = Form(...)
):
    active_subscription_type_ids = {
        sub.subscription_type_id for sub in user.client.subscriptions 
        if sub.status_name == 'active' and sub.end_date >= datetime.now().date()
    }
    
    # Проверяем, есть ли у тренировки хотя бы один разрешенный абонемент из активных у клиента
    has_access = db.query(models.Training).filter(
        models.Training.id == training_id,
        models.Training.allowed_subscriptions.any(
            models.SubscriptionType.id.in_(active_subscription_type_ids)
        )
    ).first()

    if not has_access:
        return RedirectResponse(url="/client/dashboard?error=У вас нет доступа к этой тренировке.", status_code=303)

    try:
        new_booking = models.TrainingParticipant(training_id=training_id, client_id=user.client_id, status_name="confirmed")
        db.add(new_booking); db.commit()
        return RedirectResponse(url="/client/dashboard?message=Вы успешно записаны на тренировку!", status_code=303)
    except IntegrityError:
        db.rollback()
        return RedirectResponse(url="/client/dashboard?error=Вы уже записаны на эту тренировку.", status_code=303)

@router.post("/update_profile")
async def update_profile(
    user: models.User = Depends(require_role("client")),
    db: Session = Depends(get_db),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None)
):
    if phone:
        cleaned_phone = "".join(filter(lambda char: char.isdigit() or char == '+', phone))
        if cleaned_phone.startswith('+'):
            if len(cleaned_phone) != 12 or not cleaned_phone[1:].isdigit():
                return RedirectResponse(url="/client/dashboard?error=Неверный формат телефона: +7 и 11 цифр.", status_code=303)
        else:
            if len(cleaned_phone) != 11 or not cleaned_phone.isdigit():
                return RedirectResponse(url="/client/dashboard?error=Неверный формат телефона: 11 цифр.", status_code=303)
        phone_to_save = cleaned_phone
    else:
        phone_to_save = None
    
    client = crud.get_client(db, user.client_id)
    if not client:
        # Добавим проверку, на всякий случай
        return RedirectResponse(url="/?error=Клиент не найден", status_code=303)

    client.last_name = last_name
    client.first_name = first_name
    client.middle_name = middle_name
    
    contact_details = {"phone": phone_to_save, "email": email}
    for c_type, c_value in contact_details.items():
        # Загружаем контакты перед работой с ними
        contact = db.query(models.ClientContact).filter_by(client_id=user.client_id, contact_type=c_type).first()
        if c_value:
            if contact:
                contact.contact_value = c_value
            else:
                contact = models.ClientContact(client_id=user.client_id, contact_type=c_type, contact_value=c_value)
                db.add(contact)
        elif contact:
            db.delete(contact)

    db.commit()
    return RedirectResponse(url="/client/dashboard?message=Профиль успешно обновлен", status_code=303)