from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import models, initial_data
from database.session import engine, get_db
from routers import admin, tech_admin, manager, cashier, trainer, client
from services.auth import get_current_user, create_access_token, oauth2_scheme
import os

app = FastAPI()

# Подключение роутеров
app.include_router(admin.router, prefix="/admin")
app.include_router(tech_admin.router, prefix="/tech_admin")
app.include_router(manager.router, prefix="/manager")
app.include_router(cashier.router, prefix="/cashier")
app.include_router(trainer.router, prefix="/trainer")
app.include_router(client.router, prefix="/client")

# Настройка статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Создание таблиц в базе данных
models.Base.metadata.create_all(bind=engine)

# Создание триггеров, представлений и индексов
from database import create_sql_objects
create_sql_objects()

# Инициализация начальных данных
with Session(engine) as db:
    initial_data.initialize_database(db)

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")
    
    user = db.query(models.User).filter(
        models.User.username == username,
        models.User.password == password  # В реальном приложении использовать хеширование!
    ).first()
    
    if not user:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Неверные учетные данные"}
        )
    
    # Создание токена
    access_token = create_access_token(data={"sub": user.username})
    
    # Установка токена в куки
    response = RedirectResponse(url=f"/{user.role}/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)