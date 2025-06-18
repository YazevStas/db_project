from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import crud, models
from database.session import get_db
from services.auth import get_current_user
from services.utils import generate_id
from datetime import datetime
import pytz

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, 
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        return RedirectResponse(url="/", status_code=303)
    
    clients = crud.get_clients(db)
    staff = crud.get_staff(db)
    subscriptions = crud.get_subscriptions(db)
    sections = crud.get_sections(db)
    trainings = crud.get_trainings(db)
    
    return request.app.templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "clients": clients,
            "staff": staff,
            "subscriptions": subscriptions,
            "sections": sections,
            "trainings": trainings,
            "current_user": user
        }
    )

@router.post("/add_client")
async def add_client(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    new_client = models.Client(
        id=generate_id(),
        last_name=form_data.get("last_name"),
        first_name=form_data.get("first_name"),
        middle_name=form_data.get("middle_name"),
        reg_date=datetime.now(pytz.utc).date(),
        discount=float(form_data.get("discount", 0))
    )
    db.add(new_client)
    db.commit()
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@router.post("/add_staff")
async def add_staff(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    new_staff = models.Staff(
        id=generate_id(),
        last_name=form_data.get("last_name"),
        first_name=form_data.get("first_name"),
        middle_name=form_data.get("middle_name"),
        birth_date=datetime.strptime(form_data.get("birth_date"), "%Y-%m-%d").date(),
        gender=form_data.get("gender"),
        inn=form_data.get("inn"),
        snils=form_data.get("snils"),
        hire_date=datetime.strptime(form_data.get("hire_date"), "%Y-%m-%d").date(),
        position_id=form_data.get("position_id")
    )
    db.add(new_staff)
    db.commit()
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@router.post("/add_subscription")
async def add_subscription(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    new_subscription = models.Subscription(
        id=generate_id(),
        client_id=form_data.get("client_id"),
        start_date=datetime.strptime(form_data.get("start_date"), "%Y-%m-%d").date(),
        end_date=datetime.strptime(form_data.get("end_date"), "%Y-%m-%d").date(),
        status_name=form_data.get("status_name"),
        cost=float(form_data.get("cost"))
    )
    db.add(new_subscription)
    db.commit()
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@router.post("/add_section")
async def add_section(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    new_section = models.Section(
        id=generate_id(),
        name=form_data.get("name"),
        status_name=form_data.get("status_name")
    )
    db.add(new_section)
    db.commit()
    return RedirectResponse(url="/admin/dashboard", status_code=303)

@router.post("/add_training")
async def add_training(
    request: Request,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    form_data = await request.form()
    new_training = models.Training(
        id=generate_id(),
        section_id=form_data.get("section_id"),
        trainer_id=form_data.get("trainer_id"),
        training_type=form_data.get("training_type"),
        start_time=datetime.strptime(form_data.get("start_time"), "%Y-%m-%dT%H:%M"),
        end_time=datetime.strptime(form_data.get("end_time"), "%Y-%m-%dT%H:%M"),
        max_participants=int(form_data.get("max_participants", 0))
    )
    db.add(new_training)
    db.commit()
    return RedirectResponse(url="/admin/dashboard", status_code=303)