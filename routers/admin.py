# routers/admin.py
# --- Полностью переписан с использованием require_role, Form(...) и flash-сообщений ---

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
from database import crud, models, get_db
from services.auth import require_role
from services.utils import generate_id
from datetime import datetime

router = APIRouter()

# Защищаем все роуты в этом файле, требуя роль 'admin'
# Админ имеет доступ ко всему, поэтому проверка на 'admin' достаточна.
ProtectedUser = Depends(require_role("admin"))

@router.get("/dashboard", response_class=RedirectResponse)
async def admin_dashboard(
    request: Request, 
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db)
):
    # Используем ваши SQL-представления для получения полных данных
    try:
        clients_view = db.execute(text("SELECT * FROM client_full_info_view")).mappings().all()
        staff_view = db.execute(text("SELECT * FROM staff_details_view")).mappings().all()
    except Exception as e:
        print(f"Ошибка при запросе к представлению, используем fallback: {e}")
        # Fallback на случай, если представления не работают (например, в SQLite)
        clients_view = crud.get_clients(db)
        staff_view = db.query(models.Staff).options(joinedload(models.Staff.position)).all()
    
    positions = db.query(models.Position).all()
    subscriptions = crud.get_subscriptions(db)
    sections = crud.get_sections(db)
    trainings = crud.get_trainings(db)
    
    context = {
        "request": request,
        "clients": clients_view,
        "staff": staff_view,
        "subscriptions": subscriptions,
        "sections": sections,
        "trainings": trainings,
        "positions": positions,
    }
    return request.app.state.templates.TemplateResponse("admin.html", context)

@router.post("/add_client")
async def add_client(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: str = Form(None),
    discount: float = Form(0.0)
):
    client_data = {
        "last_name": last_name, "first_name": first_name, 
        "middle_name": middle_name, "reg_date": datetime.now().date(), "discount": discount
    }
    crud.create_client(db, client_data)
    return RedirectResponse(url="/admin/dashboard?message=Клиент успешно добавлен", status_code=303)

@router.post("/add_staff")
async def add_staff(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: str = Form(None),
    birth_date: datetime = Form(...),
    gender: str = Form(...),
    inn: str = Form(...),
    snils: str = Form(...),
    hire_date: datetime = Form(...),
    position_id: str = Form(...)
):
    staff_data = {
        "last_name": last_name, "first_name": first_name, "middle_name": middle_name,
        "birth_date": birth_date.date(), "gender": gender, "inn": inn, "snils": snils,
        "hire_date": hire_date.date(), "position_id": position_id
    }
    crud.create_staff(db, staff_data)
    return RedirectResponse(url="/admin/dashboard?message=Сотрудник успешно добавлен", status_code=303)

@router.post("/add_subscription")
async def add_subscription(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    client_id: str = Form(...),
    start_date: datetime = Form(...),
    end_date: datetime = Form(...),
    status_name: str = Form(...),
    cost: float = Form(...)
):
    sub_data = {
        "client_id": client_id, "start_date": start_date.date(), "end_date": end_date.date(),
        "status_name": status_name, "cost": cost
    }
    crud.create_subscription(db, sub_data)
    return RedirectResponse(url="/admin/dashboard?message=Абонемент успешно добавлен", status_code=303)

@router.post("/add_section")
async def add_section(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    name: str = Form(...),
    status_name: str = Form(...)
):
    section = models.Section(id=generate_id(), name=name, status_name=status_name)
    db.add(section)
    db.commit()
    return RedirectResponse(url="/admin/dashboard?message=Секция успешно добавлена", status_code=303)

@router.post("/add_training")
async def add_training(
    user: models.User = ProtectedUser,
    db: Session = Depends(get_db),
    section_id: str = Form(...),
    trainer_id: str = Form(None),
    training_type: str = Form(...),
    start_time: datetime = Form(...),
    end_time: datetime = Form(...),
    max_participants: int = Form(...)
):
    training = models.Training(
        id=generate_id(), section_id=section_id, trainer_id=trainer_id,
        training_type=training_type, start_time=start_time, end_time=end_time,
        max_participants=max_participants
    )
    db.add(training)
    db.commit()
    return RedirectResponse(url="/admin/dashboard?message=Тренировка успешно добавлена", status_code=303)