import os
from sqlalchemy import text
from .session import engine

def create_sql_objects():
    """Создает триггеры, представления и другие SQL-объекты, выполняя скрипт целиком."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file_path = os.path.join(current_dir, 'sql_objects.sql')

    if not os.path.exists(sql_file_path):
        print(f"ВНИМАНИЕ: SQL-скрипт не найден по пути: {sql_file_path}")
        return

    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    try:
        with engine.connect() as connection:
            connection.execute(text(sql_script))
            connection.commit()
        print("SQL-скрипт успешно выполнен.")
    except Exception as e:
        print("="*50)
        print("!!! ПРОИЗОШЛА ОШИБКА ПРИ ВЫПОЛНЕНИИ SQL-СКРИПТА !!!")
        print(f"Файл: {sql_file_path}")
        print(f"Ошибка: {e}")
        print("="*50)