from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db, models
from services.auth import authenticate_user, create_access_token, get_current_user_from_cookie
from routers import admin_router, tech_admin_router, manager_router, cashier_router, trainer_router, client_router

app = FastAPI(title="Спортивный клуб")

app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(tech_admin_router, prefix="/tech_admin", tags=["Tech Admin"])
app.include_router(manager_router, prefix="/manager", tags=["Manager"])
app.include_router(cashier_router, prefix="/cashier", tags=["Cashier"])
app.include_router(trainer_router, prefix="/trainer", tags=["Trainer"])
app.include_router(client_router, prefix="/client", tags=["Client"])

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def datetime_format_filter(value, format='%d.%m.%Y %H:%M'):
    if isinstance(value, datetime): return value.strftime(format)
    return value
templates.env.filters['datetimeformat'] = datetime_format_filter
app.state.templates = templates


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request, user: models.User = Depends(get_current_user_from_cookie)):
    if user:
        return RedirectResponse(url=f"/{user.role}/dashboard")
    return templates.TemplateResponse("login.html", {"request": request, "current_user": None})

@app.post("/login", response_class=RedirectResponse)
async def login_for_access_token(db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(db, username, password)
    if not user:
        return RedirectResponse(url="/?error=Неверное имя пользователя или пароль", status_code=303)
    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url=f"/{user.role}/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/logout", response_class=RedirectResponse)
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response