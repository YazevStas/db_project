# routers/cashier.py
# --- Исправлена логика, добавлено хеширование пароля при регистрации клиента ---

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import crud, models, get_db
from services.auth import require_role
from datetime import datetime

router = APIRouter()
ProtectedUser = Depends(require_role("cashier"))

@router.get("/dashboard", response_class=RedirectResponse)
async def cashier_dashboard(
    request: Request, 
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db)
):
    payments = db.query(models.Payment).order_by(models.Payment.date.desc()).limit(50).all()
    subscriptions = crud.get_active_subscriptions(db)
    clients = crud.get_clients(db) # Для формы регистрации
    
    context = {
        "request": request,
        "payments": payments,
        "subscriptions": subscriptions,
        "clients": clients
    }
    return request.app.state.templates.TemplateResponse("cashier.html", context)

@router.post("/add_payment")
async def add_payment(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    subscription_id: str = Form(...),
    amount: float = Form(...),
    method_id: str = Form(...)
):
    new_payment = models.Payment(
        id=crud.generate_id(),
        subscription_id=subscription_id,
        amount=amount,
        date=datetime.now().date(),
        method_id=method_id
    )
    db.add(new_payment)
    db.commit()
    return RedirectResponse(url="/cashier/dashboard?message=Платеж успешно зарегистрирован", status_code=303)

@router.post("/register_client")
async def register_client(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    last_name: str = Form(...),
    first_name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...)
):
    # Сначала создаем клиента
    new_client = crud.create_client(db, {
        "last_name": last_name,
        "first_name": first_name,
        "reg_date": datetime.now().date()
    })
    
    # Затем создаем для него пользователя с хешированным паролем
    crud.create_user(db, {
        "username": username,
        "password": password,  # crud.create_user хеширует пароль
        "role": "client",
        "client_id": new_client.id
    })
    
    return RedirectResponse(url="/cashier/dashboard?message=Новый клиент успешно зарегистрирован", status_code=303)