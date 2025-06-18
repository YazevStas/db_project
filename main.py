# main.py

import os
from datetime import datetime
from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_303_SEE_OTHER

from database import get_db, models
from routers import admin, tech_admin, manager, cashier, trainer, client
from services.auth import authenticate_user, create_access_token, get_current_user_from_cookie

# --- Инициализация приложения FastAPI ---
app = FastAPI(
    title="Спортивный клуб",
    description="Проект по базам данных (Сатаров В.Е., Детина С.И., Язев С.В.)"
)

# --- Middleware для добавления пользователя в контекст каждого запроса ---
# Это позволяет нам не передавать current_user в каждый шаблон вручную.
# Шаблоны смогут получить доступ к нему через `request.state.current_user`.
class AddUserToTemplateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Используем нашу функцию для безопасного получения пользователя из cookie
        user = await get_current_user_from_cookie(request, next(get_db()))
        request.state.current_user = user
        response = await call_next(request)
        return response

app.add_middleware(AddUserToTemplateMiddleware)

# --- Подключение роутеров для разных ролей ---
# Теги используются для группировки эндпоинтов в документации /docs
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(tech_admin.router, prefix="/tech_admin", tags=["Tech Admin"])
app.include_router(manager.router, prefix="/manager", tags=["Manager"])
app.include_router(cashier.router, prefix="/cashier", tags=["Cashier"])
app.include_router(trainer.router, prefix="/trainer", tags=["Trainer"])
app.include_router(client.router, prefix="/client", tags=["Client"])

# --- Настройка статических файлов (CSS, JS, изображения) ---
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Настройка шаблонизатора Jinja2 ---
templates = Jinja2Templates(directory="templates")

# Добавляем кастомный фильтр 'datetimeformat', который используется в шаблонах
def datetime_format(value, format='%d.%m.%Y %H:%M'):
    if not isinstance(value, datetime):
        return value
    return value.strftime(format)
templates.env.filters['datetimeformat'] = datetime_format

# Помещаем шаблоны в "состояние" приложения, чтобы роутеры могли получить к ним доступ
app.state.templates = templates

# --- Основные эндпоинты (Логин, Логаут, Главная страница) ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    # Если пользователь уже залогинен, перенаправляем его на дашборд
    if request.state.current_user:
        role = request.state.current_user.role
        return RedirectResponse(url=f"/{role}/dashboard", status_code=HTTP_303_SEE_OTHER)
    
    # Иначе показываем страницу входа
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=RedirectResponse)
async def login_for_access_token(
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    # Аутентификация пользователя с проверкой хеша пароля
    user = authenticate_user(db, username, password)
    
    if not user:
        # Если аутентификация не удалась, возвращаем на страницу входа с ошибкой
        error_message = "Неверное имя пользователя или пароль"
        return RedirectResponse(url=f"/?error={error_message}", status_code=HTTP_303_SEE_OTHER)

    # Создание токена доступа
    access_token = create_access_token(data={"sub": user.username})
    
    # Перенаправление на дашборд соответствующей роли
    response = RedirectResponse(url=f"/{user.role}/dashboard", status_code=HTTP_303_SEE_OTHER)
    
    # Установка токена в безопасный HTTPOnly cookie
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/logout", response_class=RedirectResponse)
async def logout():
    # Перенаправляем на главную страницу и удаляем cookie
    response = RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

# --- Обработчик ошибок 404 ---
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    # Показываем кастомную страницу 404, если она есть
    if os.path.exists("templates/404.html"):
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return HTMLResponse(content="<h1>404 Not Found</h1>", status_code=404)

# --- Логика, выполняемая при запуске приложения ---
@app.on_event("startup")
def on_startup():
    from database.session import engine, SessionLocal
    from database import create_sql_objects, initial_data
    
    print("Приложение запускается... Проверка состояния базы данных.")
    
    # Создаем все таблицы, определенные в models.py (если их еще нет)
    models.Base.metadata.create_all(bind=engine)
    
    # Создаем SQL-объекты (представления, триггеры) из файла sql_objects.sql
    # Для PostgreSQL это безопасно.
    print("Создание представлений и триггеров...")
    create_sql_objects()
    
    db = SessionLocal()
    try:
        # Проверяем, есть ли в базе уже пользователи.
        # Если нет, значит, база пуста и ее нужно заполнить начальными данными.
        if not db.query(models.User).first():
            print("База данных пуста. Заполняем начальными данными...")
            initial_data.initialize_database(db)
            print("Начальные данные успешно добавлены.")
        else:
            print("База данных уже содержит данные. Инициализация пропущена.")
    finally:
        db.close()

# --- Точка входа для запуска сервера через `python main.py` ---
if __name__ == "__main__":
    import uvicorn
    # Рекомендуется запускать через терминал: uvicorn main:app --reload
    # Такой запуск полезен для простой отладки
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)