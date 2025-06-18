from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import crud, models
from database.session import get_db
from services.auth import get_current_user
from datetime import datetime

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def client_dashboard(
    request: Request, 
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "client":
        return RedirectResponse(url="/", status_code=303)
    
    # Получение данных текущего клиента
    client = db.query(models.Client).filter(models.Client.id == user.client_id).first()
    subscriptions = crud.get_client_subscriptions(db, user.client_id)
    attendances = crud.get_client_attendances(db, user.client_id)
    trainings = db.query(models.Training).join(
        models.TrainingParticipant,
        models.TrainingParticipant.training_id == models.Training.id
    ).filter(
        models.TrainingParticipant.client_id == user.client_id,
        models.Training.start_time > datetime.now()
    ).all()
    
    return request.app.templates.TemplateResponse(
        "client.html",
        {
            "request": request,
            "client": client,
            "subscriptions": subscriptions,
            "attendances": attendances,
            "trainings": trainings,
            "current_user": user
        }
    )

@router.post("/update_profile")
async def update_profile(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "client":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    client = db.query(models.Client).filter(models.Client.id == user.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client.last_name = form_data.get("last_name", client.last_name)
    client.first_name = form_data.get("first_name", client.first_name)
    client.middle_name = form_data.get("middle_name", client.middle_name)
    
    # Обновление контактов
    phone = form_data.get("phone")
    email = form_data.get("email")
    
    # Обновление или добавление телефона
    phone_contact = db.query(models.ClientContact).filter(
        models.ClientContact.client_id == user.client_id,
        models.ClientContact.contact_type == "phone"
    ).first()
    
    if phone_contact:
        phone_contact.contact_value = phone
    else:
        phone_contact = models.ClientContact(
            client_id=user.client_id,
            contact_type="phone",
            contact_value=phone
        )
        db.add(phone_contact)
    
    # Обновление или добавление email
    email_contact = db.query(models.ClientContact).filter(
        models.ClientContact.client_id == user.client_id,
        models.ClientContact.contact_type == "email"
    ).first()
    
    if email_contact:
        email_contact.contact_value = email
    else:
        email_contact = models.ClientContact(
            client_id=user.client_id,
            contact_type="email",
            contact_value=email
        )
        db.add(email_contact)
    
    db.commit()
    return RedirectResponse(url="/client/dashboard", status_code=303)

@router.post("/book_training")
async def book_training(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "client":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    training_id = form_data.get("training_id")
    
    # Проверка, не записан ли уже клиент
    existing_booking = db.query(models.TrainingParticipant).filter(
        models.TrainingParticipant.training_id == training_id,
        models.TrainingParticipant.client_id == user.client_id
    ).first()
    
    if existing_booking:
        return RedirectResponse(url="/client/dashboard", status_code=303)
    
    new_booking = models.TrainingParticipant(
        training_id=training_id,
        client_id=user.client_id,
        status_name="pending"  # Ожидает подтверждения
    )
    db.add(new_booking)
    db.commit()
    return RedirectResponse(url="/client/dashboard", status_code=303)