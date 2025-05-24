# 🚀 CrashCurse AI Backend

Потужна багатоагентна AI система на базі FastAPI та OpenAI GPT для обробки запитів від мобільних додатків.

## ✨ Особливості

- **🤖 Багатоагентна AI система**: Спеціалізовані агенти для різних завдань
- **⚡ FastAPI Backend**: Швидкий та сучасний API
- **🔒 API Key аутентифікація**: Захищені endpoint'и
- **🌐 CORS підтримка**: Налаштування для мобільних додатків
- **📊 RESTful API**: Стандартизовані HTTP endpoints
- **🔄 Auto-reload**: Автоматичне перезавантаження в режимі розробки
- **📝 API документація**: Автоматична Swagger UI документація

## 🏗️ Архітектура

### 🤖 AI Агенти

**1. Координатор (Coordinator)**
- Маршрутизація запитів між агентами
- Синтез фінальних відповідей
- Контроль якості

**2. Погодний агент (Weather)**
- Отримання актуальної погоди за містами
- Обробка запитів про погодні умови
- Надання рекомендацій

**3. Календарний агент (Calendar)**
- Створення подій та нагадувань
- Планування зустрічей
- Управління завданнями

**4. Навігаційний агент (Navigation)**
- Обробка запитів маршрутизації
- Генерація посилань на карти
- Розрахунок часу в дорозі

### 📁 Структура проекту

```
crashcurse-backend/
├── main.py                    # 🚀 Основний FastAPI додаток
├── run.sh                     # 🔧 Скрипт запуску
├── app/                       # 📂 Основні модулі
│   ├── agents/               # 🤖 AI агенти
│   ├── api/routes/           # 🛤️ API маршрути
│   ├── core/                 # ⚙️ Конфігурація
│   ├── models/               # 📊 Моделі даних
│   └── services/             # 🔧 Бізнес-логіка
├── backup/                   # 📦 Архівні файли
├── requirements.txt          # 📋 Python залежності
├── env_example.txt           # 🔐 Приклад змінних середовища
└── README.md                 # 📖 Документація
```

## 🚀 Швидкий старт

### 1. Клонування репозиторію

```bash
git clone <backend-repository-url>
cd crashcurse-backend
```

### 2. Створення віртуального середовища

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# або
venv\\Scripts\\activate    # Windows
```

### 3. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 4. Налаштування змінних середовища

```bash
cp env_example.txt .env
# Відредагуйте .env файл, додавши ваші API ключі
```

**Мінімальні необхідні змінні:**
```bash
OPENAI_API_KEY=your_openai_api_key_here
CRASHCURSE_API_KEY=supersecretapikey
```

### 5. Запуск backend

```bash
# За допомогою скрипта (рекомендовано)
./run.sh

# Або ручний запуск
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 🌐 API Endpoints

### Основні endpoints

```bash
GET  /                        # Інформація про backend
GET  /health                  # Перевірка стану системи
GET  /docs                    # Swagger UI документація
```

### AI Chat API

```bash
POST /api/v1/chat/send        # Надсилання повідомлення до AI
GET  /api/v1/chat/history     # Отримання історії чату
```

**Приклад запиту:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat/send" \\
  -H "Content-Type: application/json" \\
  -H "X-API-KEY: supersecretapikey" \\
  -d '{
    "message": "Яка погода в Києві?",
    "user_id": "user123"
  }'
```

### Календар API

```bash
POST /api/v1/calendar/events     # Створення події
POST /api/v1/calendar/reminders # Створення нагадування
```

## 🔐 Безпека

### API Key аутентифікація

Всі захищені endpoint'и вимагають заголовок:
```
X-API-KEY: supersecretapikey
```

### CORS налаштування

У production режимі CORS налаштований для конкретних доменів:
```python
ALLOWED_ORIGINS = [
    "https://mobile.labai.ws",
    "https://yourdomain.com"
]
```

## 🛠️ Розробка

### Локальна розробка

```bash
# Активувати venv
source venv/bin/activate

# Запустити в режимі розробки
./run.sh
```

Backend буде доступний на:
- **API**: http://localhost:8000
- **Документація**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

### Додавання нових агентів

1. Створіть новий файл в `app/agents/`
2. Імплементуйте логіку агента
3. Додайте маршрутизацію в `main.py`
4. Оновіть документацію

## 🧪 Тестування

### Тестування API

```bash
# Перевірка здоров'я
curl http://localhost:8000/health

# Тест чату
curl -X POST http://localhost:8000/api/v1/chat/send \\
  -H "Content-Type: application/json" \\
  -H "X-API-KEY: supersecretapikey" \\
  -d '{"message": "Привіт!", "user_id": "test"}'
```

### Моніторинг логів

```bash
# Дивитися логи в реальному часі (якщо run.sh запущений)
tail -f logs/backend.log

# Або переглядати output uvicorn
./run.sh
```

## 📊 Production Deployment

### Nginx конфігурація

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Production запуск

```bash
# Встановити production залежності
pip install gunicorn

# Запустити з Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🐞 Troubleshooting

### Порт зайнятий
```bash
# Знайти процес
lsof -ti:8000

# Завершити процес
kill -9 $(lsof -ti:8000)
```

### API Key помилки
- Перевірте `.env` файл
- Переконайтеся що `CRASHCURSE_API_KEY` встановлений
- Перезапустіть backend після зміни `.env`

### Помилки залежностей
```bash
# Перевстановити залежності
pip install --upgrade -r requirements.txt
```

## 📦 Docker (опціонально)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contribution

1. Fork репозиторій
2. Створіть feature branch (`git checkout -b feature/amazing-feature`)
3. Commit зміни (`git commit -m 'Add amazing feature'`)
4. Push до branch (`git push origin feature/amazing-feature`)
5. Створіть Pull Request

## 📝 Ліцензія

MIT License - деталі в файлі LICENSE

## 🆘 Підтримка

- **Документація API**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Health Check**: http://localhost:8000/health

---

**🚗💨 Розроблено командою CrashCurse** 