# CrashCurse AI Асистент

Потужна багатоагентна AI система з backend на FastAPI та CrewAI, розроблена для iOS додатку CrashCurse.

## 🚀 Особливості

- **Багатоагентна AI система**: Працює з CrewAI та спеціалізованими агентами
- **Простий режим розробки**: Для тестування та розробки (поточний активний)
- **RESTful API**: Повний набір API endpoints для інтеграції з iOS додатком
- **WebSocket підтримка**: Реальний час комунікації
- **Інтеграція з базою даних**: SQLAlchemy з підтримкою SQLite/PostgreSQL
- **Координація агентів**: Інтелектуальна маршрутизація завдань та синтез відповідей
- **HTTPS/SSL підтримка**: Безпечне з'єднання з Let's Encrypt
- **API Key аутентифікація**: Захищені endpoint'и

## 🏗️ Архітектура системи

### 📁 Структура проекту
```
CrashCurseApp/
├── main.py                  # ✅ Основний backend файл (FastAPI + AI агенти)
├── run.sh                   # 🚀 Скрипт для запуску backend
├── backup/                  # 📦 Архів старих файлів та скриптів
│   ├── main_*.py           # Старі версії main файлів
│   └── start_*.sh          # Старі скрипти запуску
├── app/                     # 📂 Backend модулі
│   ├── agents/             # 🤖 AI агенти (CrewAI)
│   ├── api/routes/         # 🛤️ API маршрути
│   ├── core/               # ⚙️ Основні налаштування
│   ├── models/             # 📊 Моделі даних
│   └── services/           # 🔧 Сервіси
├── CrashCurseApp/          # 📱 iOS додаток (Swift/SwiftUI)
├── requirements.txt        # 📋 Python залежності
├── .env                    # 🔐 Змінні середовища
└── README.md              # 📖 Документація
```

### 🤖 AI Агенти

**1. Координуючий агент (Coordinator)**
- Маршрутизація запитів між агентами
- Синтез фінальних відповідей
- Контроль якості

**2. Погодний агент (Weather)**
- Отримання актуальної погоди
- Прогнози для подорожей
- Рекомендації одягу

**3. Календарний агент (Calendar)**
- Створення подій
- Управління нагадуваннями
- Планування зустрічей

**4. Навігаційний агент (Navigation)**
- Побудова маршрутів
- Розрахунок часу в дорозі
- Рекомендації транспорту

### 🌐 API Endpoints

```bash
# Основні
GET  /                      # Інформація про backend
GET  /health               # Перевірка стану системи

# Чат з AI
POST /api/v1/chat/send     # Надсилання повідомлення
GET  /api/v1/chat/history  # Історія розмов

# Календар
POST /api/v1/calendar/events    # Створення події
POST /api/v1/calendar/reminders # Створення нагадування

# Документація
GET  /docs                 # Swagger UI документація
```

### 🔐 Безпека

- **API Key аутентифікація**: Захист всіх endpoint'ів
- **CORS налаштування**: Обмеження доступу тільки для дозволених доменів
- **HTTPS/SSL**: Шифрування з Let's Encrypt сертифікатами

### 📱 iOS Інтеграція

**Backend URL**: `https://mobile.labai.ws`
**Nginx**: Проксі з порту 443 на локальний порт 8000
**NetworkService.swift**: Автоматичне додавання API ключів до запитів

## 🚀 Швидкий старт

### 1. Встановлення залежностей

```bash
# Клонування репозиторію
git clone <repository>
cd CrashCurseApp

# Створення віртуального середовища
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# або
source venv/Scripts/activate  # Windows

# Встановлення залежностей
pip install -r requirements.txt
```

### 2. Налаштування змінних середовища

```bash
# Створіть .env файл
cp env_example.txt .env

# Додайте необхідні API ключі
OPENAI_API_KEY=your_openai_api_key
CRASHCURSE_API_KEY=supersecretapikey
```

### 3. Запуск backend

```bash
# Простий запуск за допомогою скрипта
./run.sh

# Або ручний запуск
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend буде доступний на:
- **Локально**: http://localhost:8000
- **Production**: https://mobile.labai.ws
- **API документація**: http://localhost:8000/docs

## 🛠️ Розробка

### Локальна розробка

```bash
# Активувати venv
source venv/bin/activate

# Запустити в режимі розробки
./run.sh
```

### Production розгортання

```bash
# 1. Налаштувати Nginx (приклад конфігурації)
server {
    listen 443 ssl;
    server_name mobile.labai.ws;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# 2. Запустити backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📊 Моніторинг

### Перевірка стану
```bash
curl https://mobile.labai.ws/health
```

### Логи
```bash
# Backend логи в реальному часі
tail -f logs/backend.log
```

## 🔧 Налаштування iOS додатка

### NetworkService.swift
```swift
private let backendURL = "https://mobile.labai.ws"
private let apiKey = "supersecretapikey"
```

### Info.plist (для HTTP з'єднань в розробці)
```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
```

## 🤝 Співпраця

1. Fork репозиторій
2. Створіть feature branch
3. Зробіть зміни
4. Відправте pull request

## 📝 Ліцензія

MIT License - деталі в файлі LICENSE

## 🆘 Підтримка

Для питань та підтримки:
- Створіть issue в GitHub
- Зв'яжіться з командою розробки

---

**Розроблено командою CrashCurse** 🚗💨 