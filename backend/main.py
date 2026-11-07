import time
import sqlite3
import requests
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Настройка CORS для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Раздача статики
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
def read_index():
    return FileResponse("../frontend/index.html")

# Конфигурация OAuth
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/auth/yandex/callback"

# Инициализация кэша
schedule_cache = {}

@app.get("/auth/yandex")
def auth_yandex():
    yandex_auth_url = (
        f"https://oauth.yandex.ru/authorize?"
        f"response_type=code&"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(yandex_auth_url)

@app.get("/auth/yandex/callback")
def auth_yandex_callback(code: str):
    # Обмен кода авторизации на access token
    token_url = "https://oauth.yandex.ru/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    
    response = requests.post(token_url, data=data)
    token_data = response.json()

    if "access_token" not in token_data:
        return {"error": "Не удалось получить токен", "details": token_data}

    access_token = token_data["access_token"]

    # Запрос данных пользователя
    user_info_url = "https://login.yandex.ru/info?format=json"
    headers = {"Authorization": f"OAuth {access_token}"}
    user_response = requests.get(user_info_url, headers=headers)
    user_data = user_response.json()

    yandex_id = str(user_data.get("id"))
    first_name = user_data.get("first_name", "Имя")
    last_name = user_data.get("last_name", "Фамилия")
    
    # Передача данных на фронтенд через параметры URL
    return RedirectResponse(f"http://localhost:8000/?user_id={yandex_id}&first_name={first_name}&last_name={last_name}")


def get_db():
    conn = sqlite3.connect('schedule.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get('/api/schedule/{user_id}')
def get_schedule(
    user_id: str, 
    first_name: str = Query("Новый"), 
    last_name: str = Query("Студент")
):
    # Проверка кэша (TTL 5 минут)
    if user_id in schedule_cache:
        cached_time, cached_data = schedule_cache[user_id]
        if time.time() - cached_time < 300:
            print(f"[CACHE] Данные для {user_id} взяты из кэша")
            return cached_data
            
    
    conn = get_db()
    cur = conn.cursor()
    
    # Поиск пользователя в БД
    cur.execute('SELECT id FROM users WHERE external_id = ?', (user_id,))
    user_row = cur.fetchone()
    
    if user_row:
        db_user_id = user_row['id']
    else:
        # Регистрация нового пользователя при первом входе
        cur.execute(
            'INSERT INTO users (external_id, first_name, last_name) VALUES (?, ?, ?)',
            (user_id, first_name, last_name)
        )
        conn.commit()
        db_user_id = cur.lastrowid
        
        # Копирование тестового расписания для нового пользователя (НУЖНО ТОЛЬКО ДЛЯ ТЕСТОВ)
        cur.execute('''
            INSERT INTO schedule (user_id, day_of_week, start_time, end_time, subject, room, teacher)
            SELECT ?, day_of_week, start_time, end_time, subject, room, teacher 
            FROM schedule WHERE user_id = 2
        ''', (db_user_id,))
        conn.commit()
    
    # Получение расписания
    cur.execute(
        'SELECT day_of_week, start_time, end_time, subject, room, teacher FROM schedule WHERE user_id = ?',
        (db_user_id,)
    )
    rows = cur.fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    
    # Сохранение в кэш
    schedule_cache[user_id] = (time.time(), result)
    print(f"[DB] Данные для {user_id} взяты из базы данных")
    
    return result