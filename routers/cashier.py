from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import crud, models
from database.session import get_db
from services.auth import get_current_user
from services.utils import generate_id
from datetime import datetime

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def cashier_dashboard(
    request: Request, 
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "cashier":
        return RedirectResponse(url="/", status_code=303)
    
    payments = db.query(models.Payment).order_by(models.Payment.date.desc()).limit(50).all()
    subscriptions = crud.get_active_subscriptions(db)
    
    return request.app.templates.TemplateResponse(
        "cashier.html",
        {
            "request": request,
            "payments": payments,
            "subscriptions": subscriptions,
            "current_user": user
        }
    )

@router.post("/add_payment")
async def add_payment(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "cashier":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    new_payment = models.Payment(
        id=generate_id(),
        subscription_id=form_data.get("subscription_id"),
        amount=float(form_data.get("amount")),
        date=datetime.now().date(),
        method_id=form_data.get("method_id")
    )
    db.add(new_payment)
    db.commit()
    return RedirectResponse(url="/cashier/dashboard", status_code=303)

@router.post("/register_client")
async def register_client(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "cashier":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    new_client = models.Client(
        id=generate_id(),
        last_name=form_data.get("last_name"),
        first_name=form_data.get("first_name"),
        reg_date=datetime.now().date(),
        discount=0.0
    )
    db.add(new_client)
    
    # Создание пользователя для клиента
    new_user = models.User(
        id=generate_id(),
        username=form_data.get("username"),
        password=form_data.get("password"),  # В реальном приложении должно быть хешировано!
        role="client",
        client_id=new_client.id
    )
    db.add(new_user)
    
    db.commit()
    return RedirectResponse(url="/cashier/dashboard", status_code=303)