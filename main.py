# main.py (Финальная версия с lifespan)

import os
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Импортируем все необходимое из нашего проекта
from database import (
    engine, Base, get_db, initialize_database, create_sql_objects,
    crud, models, SessionLocal  # <--- ДОБАВЛЕН ИМПОРТ SessionLocal
)
from services.auth import (
    authenticate_user, create_access_token, get_current_user_from_cookie
)
from routers import (
    admin_router, tech_admin_router, manager_router, 
    cashier_router, trainer_router, client_router
)

# --- Использование Lifespan для инициализации при старте ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполняется ДО запуска приложения (аналог startup)
    print("Приложение запускается... Проверка состояния базы данных.")
    
    # Создаем все таблицы, определенные в models.py (если их еще нет)
    print("Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы.")
    
    # Создаем SQL-объекты (представления, триггеры) из файла sql_objects.sql
    print("Создание представлений и триггеров...")
    create_sql_objects()
    print("SQL-объекты созданы.")
    
    # Используем 'with' для автоматического получения и закрытия сессии
    with SessionLocal() as db:
        # Проверяем, есть ли в базе уже пользователи.
        if not db.query(models.User).first():
            print("База данных пуста. Заполняем начальными данными...")
            initialize_database(db)
            print("Начальные данные успешно добавлены.")
        else:
            print("База данных уже содержит данные. Инициализация пропущена.")
    
    print("Приложение готово к работе.")
    yield
    # Код, который выполняется ПОСЛЕ остановки приложения (аналог shutdown)
    print("Приложение останавливается...")

# --- Инициализация приложения FastAPI с указанием lifespan ---
app = FastAPI(
    lifespan=lifespan, # <--- ВОТ ТАК ПОДКЛЮЧАЕТСЯ LIFESPAN
    title="Спортивный клуб",
    description="Проект по базам данных (Сатаров В.Е., Детина С.И., Язев С.В.)"
)

# --- Подключение роутеров для разных ролей ---
app.include_router(admin_router, prefix="/admin", tags=["Admin"])
app.include_router(tech_admin_router, prefix="/tech_admin", tags=["Tech Admin"])
app.include_router(manager_router, prefix="/manager", tags=["Manager"])
app.include_router(cashier_router, prefix="/cashier", tags=["Cashier"])
app.include_router(trainer_router, prefix="/trainer", tags=["Trainer"])
app.include_router(client_router, prefix="/client", tags=["Client"])

# --- Настройка статических файлов и шаблонов ---
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def datetime_format_filter(value, format='%d.%m.%Y %H:%M'):
    if isinstance(value, datetime):
        return value.strftime(format)
    return value
templates.env.filters['datetimeformat'] = datetime_format_filter
app.state.templates = templates


# --- Основные эндпоинты (Логин, Логаут, Главная страница) ---

@app.get("/", response_class=HTMLResponse)
async def login_page(
    request: Request, 
    user: models.User = Depends(get_current_user_from_cookie)
):
    if user:
        return RedirectResponse(url=f"/{user.role}/dashboard")
    
    return templates.TemplateResponse("login.html", {"request": request, "current_user": user})

@app.post("/login", response_class=RedirectResponse)
async def login_for_access_token(
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    user = authenticate_user(db, username, password)
    if not user:
        return RedirectResponse(url="/?error=Неверное имя пользователя или пароль", status_code=303)

    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url=f"/{user.role}/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/logout", response_class=RedirectResponse)
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

# --- Точка входа для запуска сервера ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)