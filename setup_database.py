import sys
import os

# Добавляем корневую папку проекта в путь, чтобы можно было импортировать модули
# Это нужно, чтобы скрипт мог найти папки database, services и т.д.
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from database import Base, engine, SessionLocal, create_sql_objects, initialize_database, models

def setup_database():
    """
    Полностью настраивает базу данных: удаляет старые таблицы,
    создает новые и заполняет их начальными данными.
    ЭТОТ СКРИПТ НУЖНО ЗАПУСКАТЬ ОДИН РАЗ ВРУЧНУЮ.
    """
    print("ВНИМАНИЕ: Сейчас все существующие таблицы будут удалены и созданы заново.")
    confirm = input("Вы уверены? (y/n): ")
    if confirm.lower() != 'y':
        print("Отмена операции.")
        return

    print("Удаление старых таблиц...")
    # Удаляем все таблицы в обратном порядке зависимостей, чтобы избежать ошибок
    Base.metadata.drop_all(bind=engine)
    print("Старые таблицы удалены.")

    print("\nСоздание новых таблиц...")
    Base.metadata.create_all(bind=engine)
    print("Новые таблицы созданы.")
    
    print("\nСоздание представлений и триггеров...")
    try:
        create_sql_objects()
    except Exception as e:
        print(f"Не удалось создать SQL объекты: {e}")

    print("\nЗаполнение начальными данными...")
    db = SessionLocal()
    try:
        initialize_database(db)
        print("\nБаза данных успешно настроена и заполнена!")
    except Exception as e:
        print(f"Произошла ошибка при заполнении данными: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    setup_database()