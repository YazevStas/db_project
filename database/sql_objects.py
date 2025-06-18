import os
from sqlalchemy import text
from .session import engine

def create_sql_objects():
    """Создает триггеры, представления и индексы в базе данных"""
    # Получаем путь к SQL-файлу
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file_path = os.path.join(current_dir, 'sql_objects.sql')
    
    # Читаем содержимое SQL-файла
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Выполняем SQL-скрипт
    with engine.connect() as connection:
        # Разделяем скрипт на отдельные команды
        commands = sql_script.split(';')
        for command in commands:
            # Пропускаем пустые команды
            stripped_command = command.strip()
            if stripped_command:
                try:
                    connection.execute(text(stripped_command))
                except Exception as e:
                    print(f"Ошибка при выполнении команды: {stripped_command[:50]}...")
                    print(f"Ошибка: {str(e)}")
        connection.commit()