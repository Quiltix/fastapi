# Сервис учета учебных курсов (FastAPI)

Реализовано:
- Курсы (CRUD)
- Расписание (занятия)
- Прогресс (отметка пройденных занятий)
- Аутентификация (JWT)
- PostgreSQL + async

## Запуск
1. Установить все зависимости `pip install -r requirements.txt`
2. Создать БД `course_db` в PostgreSQL
3. Настроить `.env`
4. Создать таблицы `python create_tables.py`
5. Запустить сервер на порту 8080 `uvicorn app.main:app --reload --port 8080`
6. Открыть http://127.0.0.1:8080/docs