# routers/cashier.py
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime

from database import crud, models, get_db
from services.auth import require_role

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def cashier_dashboard(
    request: Request,
    user: models.User = Depends(require_role("cashier")), # <--- Зависимость здесь
    db: Session = Depends(get_db)
):
    payments = db.query(models.Payment).order_by(models.Payment.date.desc()).limit(50).all()
    subscriptions = db.query(models.ClientSubscription).filter(models.ClientSubscription.status_name == 'active').all()
    clients = crud.get_clients(db)
    
    context = {
        "request": request, "payments": payments, 
        "subscriptions": subscriptions, "clients": clients
    }
    return request.app.state.templates.TemplateResponse("cashier.html", context)

@router.post("/add_payment")
async def add_payment(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("cashier")), # <--- Зависимость здесь
    subscription_id: str = Form(...),
    amount: float = Form(...),
    method_id: str = Form(...)
):
    new_payment = models.Payment(
        id=crud.generate_id(), client_subscription_id=subscription_id,
        amount=amount, date=datetime.now().date(), method_id=method_id
    )
    db.add(new_payment)
    db.commit()
    return RedirectResponse(url="/cashier/dashboard?message=Платеж успешно зарегистрирован", status_code=303)

@router.post("/register_client")
async def register_client(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("cashier")), # <--- Зависимость здесь
    last_name: str = Form(...),
    first_name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...)
):
    new_client = crud.create_client(db, {
        "last_name": last_name, "first_name": first_name, "reg_date": datetime.now().date()
    })
    crud.create_user(db, {
        "username": username, "password": password, 
        "role": "client", "client_id": new_client.id
    })
    return RedirectResponse(url="/cashier/dashboard?message=Новый клиент успешно зарегистрирован", status_code=303)