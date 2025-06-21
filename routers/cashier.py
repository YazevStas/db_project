from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from database import crud, models, get_db
from services.auth import require_role
from services.utils import generate_id

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def cashier_dashboard(
    request: Request,
    user: models.User = Depends(require_role("cashier")),
    db: Session = Depends(get_db)
):
    payments = db.query(models.Payment).options(
        joinedload(models.Payment.client_subscription).joinedload(models.ClientSubscription.client),
        joinedload(models.Payment.method)
    ).order_by(models.Payment.date.desc()).limit(50).all()
    all_clients = db.query(models.Client).order_by(models.Client.last_name).all()
    all_subscription_types = db.query(models.SubscriptionType).order_by(models.SubscriptionType.name).all()
    payment_methods = db.query(models.PaymentMethod).all()

    context = {
        "request": request,
        "current_user": user,
        "payments": payments,
        "all_clients": all_clients,
        "all_subscription_types": all_subscription_types,
        "payment_methods": payment_methods
    }
    return request.app.state.templates.TemplateResponse("cashier.html", context)


@router.post("/sell_subscription")
async def sell_subscription(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("cashier")),
    client_id: str = Form(...),
    subscription_type_id: str = Form(...),
    start_date: datetime = Form(...),
    end_date: datetime = Form(...),
    method_id: str = Form(...)
):
    client_sub = models.ClientSubscription(
        id=generate_id(), 
        client_id=client_id, 
        subscription_type_id=subscription_type_id,
        start_date=start_date.date(), 
        end_date=end_date.date(), 
        status_name='pending'
    )
    db.add(client_sub)
    db.commit()
    
    sub_type = db.query(models.SubscriptionType).filter_by(id=subscription_type_id).first()
    amount = sub_type.cost if sub_type else 0

    if amount > 0:
        new_payment = models.Payment(
            id=generate_id(), 
            client_subscription_id=client_sub.id,
            amount=amount, 
            date=datetime.now().date(), 
            method_id=method_id
        )
        db.add(new_payment)
        db.commit()

    return RedirectResponse(url="/cashier/dashboard?message=Абонемент успешно продан и платеж зарегистрирован", status_code=303)


@router.post("/add_payment")
async def add_payment(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_role("cashier")),
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
    user: models.User = Depends(require_role("cashier")),
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