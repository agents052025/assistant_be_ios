from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
import logging
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from datetime import datetime
import re
import requests
import asyncio
import httpx
from fastapi.exceptions import HTTPException as FastAPIHTTPException

# Try to import openai, but make it optional
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("OpenAI not installed, using fallback location extraction")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Weather API configuration
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_BASE_URL = os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org/data/2.5")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Add calendar-specific models
class CalendarEventRequest(BaseModel):
    title: str
    start_date: str  # ISO format
    end_date: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

class CalendarEventResponse(BaseModel):
    success: bool
    event_id: Optional[str] = None
    title: str
    start_date: str
    end_date: Optional[str] = None
    location: Optional[str] = None
    message: str
    action: str = "create_calendar_event"  # Signal to iOS
    timestamp: str = datetime.now().isoformat()

# Simple response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    success: bool
    message: str
    agent_id: Optional[str] = None
    conversation_id: Optional[str] = None
    timestamp: str = datetime.now().isoformat()

# Simple in-memory storage
conversations = {}
active_connections: Dict[str, WebSocket] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting CrashCurse Backend (Fixed Version)...")
    logger.info("✅ Backend initialized successfully")
    yield
    # Shutdown
    logger.info("🛑 Shutting down CrashCurse Backend...")

# Create FastAPI app
app = FastAPI(
    title="CrashCurse AI Assistant Backend - Fixed",
    description="Fixed backend for iOS CrashCurse app",
    version="1.0.1-fixed",
    lifespan=lifespan
)

# Configure CORS
ALLOWED_ORIGINS = [
    "https://mobile.labai.ws",
    "https://mobile.labai.ws:8080",
    # Add your iOS app's custom scheme or domain if needed
]

API_KEY = os.getenv("CRASHCURSE_API_KEY", "supersecretapikey")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise FastAPIHTTPException(status_code=401, detail="Invalid API Key")

# Update CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Apply API key dependency to all endpoints except root and health
from fastapi.routing import APIRoute
for route in app.routes:
    if isinstance(route, APIRoute):
        if route.path not in ["/", "/health"]:
            route.dependant.dependencies.append(Depends(verify_api_key))

@app.get("/")
async def root():
    return {
        "message": "CrashCurse AI Assistant Backend (Fixed)",
        "version": "1.0.1-fixed",
        "status": "active",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.1-fixed",
        "websocket_connections": len(active_connections),
        "mode": "fixed"
    }

# Chat endpoints
@app.post("/api/v1/chat/send")
async def send_message(request: ChatRequest):
    """Main chat endpoint with multi-agent and OpenAPI support"""
    try:
        message = request.message.strip()
        user_id = request.user_id
        
        logger.info(f"📨 Received message from {user_id}: {message[:50]}...")
        
        # Initialize response data
        agent_used = "Personal Assistant"
        api_response = None
        api_status = None
        
        # Check for API-related keywords
        message_lower = message.lower()
        api_keywords = ["api", "сервіс", "новини", "news", "курс валют", "exchange rate"]
        is_api_request = any(keyword in message_lower for keyword in api_keywords)
        
        # Check for weather requests
        weather_keywords = ["погода", "weather", "температура", "temperature"]
        is_weather_request = any(keyword in message_lower for keyword in weather_keywords)
        
        # Handle specific API requests
        if is_api_request and ("новини" in message_lower or "news" in message_lower):
            # NEWS API REQUEST
            agent_used = "News API Specialist"
            api_status = "calling_news_api"
            
            query = "Ukraine"  # Default query
            if "про" in message_lower:
                parts = message_lower.split("про")
                if len(parts) > 1:
                    query = parts[1].strip()
            
            news_result = await openapi_integration.get_news_via_api(query)
            if news_result.get("success"):
                api_response = {"news": news_result["data"]}
                api_status = "success"
                
                response_text = f"📰 **Останні новини про {query}:**\n\n"
                articles = news_result["data"].get("articles", [])[:3]
                for i, article in enumerate(articles, 1):
                    response_text += f"**{i}. {article['title']}**\n"
                    response_text += f"📝 {article.get('description', 'Опис недоступний')}\n"
                    response_text += f"🔗 {article['url']}\n\n"
            else:
                api_status = "error"
                response_text = f"❌ Не вдалося отримати новини: {news_result.get('error', 'Невідома помилка')}"
                
        elif is_weather_request and is_api_request:
            # WEATHER API REQUEST
            agent_used = "Weather API Specialist"
            api_status = "calling_weather_api"
            
            city = await extract_city_from_message(message)
            
            weather_result = await openapi_integration.get_weather_via_api(city)
            if weather_result.get("success"):
                api_response = {"weather": weather_result}
                api_status = "success"
                
                w = weather_result
                weather_icon = get_weather_icon(w["description"])
                response_text = f"""{weather_icon} **Погода в {w["location"]}** (через API)

🌡️ **{w["temperature"]}** (відчувається як {w["feels_like"]})
☁️ {w["description"]}
💧 Вологість: {w["humidity"]}
💨 Вітер: {w["wind_speed"]}

📡 *Дані отримано через OpenWeatherMap API*"""
            else:
                api_status = "fallback_to_demo"
                weather_data = generate_demo_weather(city)
                response_text = f"""🌤️ **Погода в {weather_data["location"]}**

🌡️ **{weather_data["temperature"]}** (відчувається як {weather_data["feels_like"]})
☁️ {weather_data["description"]}
💧 Вологість: {weather_data["humidity"]}
💨 Вітер: {weather_data["wind_speed"]}

💡 *Демо дані - для реальних даних налаштуйте API ключ*"""
                
        else:
            # REGULAR PROCESSING WITH AI NAVIGATION/WEATHER/ETC
            
            # Check for navigation request first (highest priority)
            navigation_data = await ai_extract_navigation_info(message)
            
            if navigation_data.get("has_destination"):
                agent_used = "Navigation Specialist"
                destination = navigation_data["destination"]
                transport_mode = navigation_data.get("transport_mode", "автомобіль")
                
                # Generate maps URLs
                apple_maps_url = f"http://maps.apple.com/?daddr={destination}&dirflg=d"
                google_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={destination}"
                
                response_text = f"""🗺️ **Навігація до {destination}**

🚗 Транспорт: {transport_mode}
📍 Пункт призначення: {destination}

**Відкрити в:**
🍎 Apple Maps: [Натисніть тут]({apple_maps_url})
🌐 Google Maps: [Відкрити]({google_maps_url})

💡 Натисніть на посилання або скажіть "відкрити навігацію" для автоматичного запуску Maps."""
                
                # Build navigation response
                response_data = {
                    "success": True,
                    "message": response_text,
                    "timestamp": datetime.now().isoformat(),
                    "navigation": True,
                    "destination": destination,
                    "transport_mode": transport_mode,
                    "apple_maps_url": apple_maps_url,
                    "maps_scheme_url": f"maps://?daddr={destination}",
                    "agent_used": agent_used
                }
                
                logger.info(f"✅ Generated response for {user_id}")
                return response_data
            
            # Check for weather request
            elif is_weather_request:
                agent_used = "Weather Specialist"
                city = await extract_city_from_message(message)
                weather_data = generate_demo_weather(city)
                
                weather_icon = get_weather_icon(weather_data["description"])
                response_text = f"""{weather_icon} **Погода в {weather_data["location"]}**

🌡️ **{weather_data["temperature"]}** (відчувається як {weather_data["feels_like"]})
☁️ {weather_data["description"]}
💧 Вологість: {weather_data["humidity"]}
💨 Вітер: {weather_data["wind_speed"]}"""
                
                response_data = {
                    "success": True,
                    "message": response_text,
                    "timestamp": datetime.now().isoformat(),
                    "weather": True,
                    "location": weather_data["location"],
                    "temperature": weather_data["temperature"],
                    "description": weather_data["description"],
                    "humidity": weather_data["humidity"],
                    "feels_like": weather_data["feels_like"],
                    "wind_speed": weather_data["wind_speed"],
                    "is_real_data": False,
                    "agent_used": agent_used
                }
                
                logger.info(f"✅ Generated response for {user_id}")
                return response_data
            
            # Regular chat response
            else:
                response_text = await generate_smart_response(message)
        
        # Build final response with agent information
        response_data = {
            "success": True,
            "message": response_text,
            "timestamp": datetime.now().isoformat(),
            "agent_used": agent_used
        }
        
        if api_response:
            response_data["api_response"] = api_response
        if api_status:
            response_data["api_status"] = api_status
            
        logger.info(f"✅ Generated response for {user_id}")
        return response_data
        
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        return {
            "success": False,
            "message": f"Вибачте, сталася помилка: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "agent_used": "Error Handler"
        }

@app.post("/chat")
async def simple_chat(request: ChatRequest):
    """Simplified chat endpoint for iOS compatibility"""
    try:
        logger.info(f"📨 Received message from {request.user_id}: {request.message[:100]}...")
        
        conversation_id = f"{request.user_id}_{datetime.now().timestamp()}"
        
        # Store conversation
        conversations[conversation_id] = {
            "user_id": request.user_id,
            "message": request.message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Check if it's a navigation request first
        if await is_navigation_request_ai(request.message):
            navigation_details = await extract_navigation_with_ai(request.message)
            
            if navigation_details["has_destination"]:
                destination = navigation_details["destination"]
                transport_type = navigation_details["transport_type"]
                transport_mode = navigation_details["transport_mode"]
                
                destination_encoded = destination.replace(' ', '+').replace('і', 'i').replace('ї', 'i')
                apple_maps_url = f"http://maps.apple.com/?daddr={destination_encoded}&dirflg={transport_type}"
                maps_scheme_url = f"maps://?daddr={destination_encoded}&dirflg={transport_type}"
                
                # Return navigation command - NOT as text but as action fields
                return {
                    "success": True,
                    "action": "open_maps",  # TOP LEVEL ACTION
                    "navigation": True,     # NAVIGATION FLAG
                    "destination": destination,
                    "transport_type": transport_type,
                    "transport_mode": transport_mode,
                    "apple_maps_url": apple_maps_url,
                    "maps_scheme_url": maps_scheme_url,
                    "maps_url": maps_scheme_url,  # Main URL field
                    "message": f"📍 Прокладаю маршрут до {destination}",  # User-friendly text
                    "conversation_id": conversation_id,
                    "agent_id": "navigation_agent",
                    "timestamp": datetime.now().isoformat()
                }
        
        # Generate smart response for non-navigation requests
        smart_response = await generate_smart_response(request.message)
        
        logger.info(f"✅ Generated response for {request.user_id}")
        
        return {
            "success": True,
            "message": smart_response,
            "agent_id": "smart_agent",
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error in simple_chat: {e}")
        return {
            "success": False,
            "message": "Вибачте, сталася помилка. Спробуйте ще раз.",
            "agent_id": "error_handler",
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/v1/calendar/create", response_model=CalendarEventResponse)
async def create_calendar_event(request: CalendarEventRequest):
    """Create a calendar event endpoint for iOS integration"""
    try:
        event_id = f"event_{int(datetime.now().timestamp())}"
        
        logger.info(f"📅 Creating calendar event: {request.title} at {request.start_date}")
        
        return CalendarEventResponse(
            success=True,
            event_id=event_id,
            title=request.title,
            start_date=request.start_date,
            end_date=request.end_date,
            location=request.location,
            message=f"Event '{request.title}' successfully created",
            action="create_calendar_event"
        )
        
    except Exception as e:
        logger.error(f"❌ Error creating calendar event: {e}")
        return CalendarEventResponse(
            success=False,
            title=request.title if hasattr(request, 'title') else "Unknown Event",
            start_date="",
            message="Failed to create calendar event"
        )

@app.post("/api/v1/navigation/open")
async def open_navigation_direct(request: ChatRequest):
    """Direct navigation endpoint for iOS testing"""
    try:
        message = request.message
        logger.info(f"🗺️ Direct navigation request: {message}")
        
        # Check if it's a navigation request
        if await is_navigation_request_ai(message):
            navigation_details = await extract_navigation_with_ai(message)
            
            if navigation_details["has_destination"]:
                destination = navigation_details["destination"]
                transport_type = navigation_details["transport_type"]
                transport_mode = navigation_details["transport_mode"]
                
                # Create direct maps URL
                destination_encoded = destination.replace(' ', '+').replace('і', 'i').replace('ї', 'i')
                apple_maps_url = f"http://maps.apple.com/?daddr={destination_encoded}&dirflg={transport_type}"
                maps_scheme_url = f"maps://?daddr={destination_encoded}&dirflg={transport_type}"
                
                return {
                    "success": True,
                    "action": "open_maps",
                    "destination": destination,
                    "transport_type": transport_type,
                    "transport_mode": transport_mode,
                    "apple_maps_url": apple_maps_url,
                    "maps_scheme_url": maps_scheme_url,
                    "message": f"Відкриваю навігацію до {destination}",
                    "ios_action": {
                        "type": "open_url",
                        "url": maps_scheme_url
                    },
                    "timestamp": datetime.now().isoformat()
                }
        
        return {
            "success": False,
            "message": "Не вдалося розпізнати навігаційний запит",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Navigation error: {e}")
        return {
            "success": False,
            "message": "Помилка обробки навігації",
            "timestamp": datetime.now().isoformat()
        }

async def generate_smart_response(message: str) -> str:
    """Generate smart responses based on user input"""
    message_lower = message.lower()
    
    # Ukrainian/English greeting detection
    if any(word in message_lower for word in ['привіт', 'hello', 'hi', 'hey', 'вітаю']):
        return "Привіт! 👋 Я ваш AI асистент CrashCurse. Готовий допомогти з плануванням, завданнями та нагадуваннями!"
    
    # Notes and Ideas - HIGH PRIORITY to avoid conflicts
    elif any(word in message_lower for word in ['нотатка', 'note', 'запиши', 'записати', 'ідея', 'idea', 'думка']):
        # Extract note content
        note_keywords = ['нотатка', 'запиши', 'записати', 'note', 'ідея', 'думка']
        note_content = message
        
        for keyword in note_keywords:
            if keyword in message_lower:
                parts = message_lower.split(keyword, 1)
                if len(parts) > 1:
                    note_content = parts[1].strip()
                    # Clean up common punctuation
                    if note_content.startswith(':'):
                        note_content = note_content[1:].strip()
                    if note_content.startswith(','):
                        note_content = note_content[1:].strip()
                break
        
        # Detect note category
        category = "загальна"
        if any(word in message_lower for word in ['робота', 'work', 'проект', 'завдання']):
            category = "робота"
        elif any(word in message_lower for word in ['особисте', 'personal', 'приватне']):
            category = "особисте"
        elif any(word in message_lower for word in ['ідея', 'idea', 'придумав']):
            category = "ідеї"
            
        if note_content and len(note_content.strip()) > 0:
            notes_instruction = f"""
📝 **НОТАТКА:**
---
NOTES_DATA: {{
    "action": "create_note",
    "content": "{note_content[:100]}",
    "category": "{category}",
    "timestamp": "{datetime.now().isoformat()}",
    "type": "note"
}}
---
"""
            
            return f"""📝 **Створюю нотатку:**

💭 **Зміст:** {note_content}
📂 **Категорія:** {category}
⏰ **Час:** {datetime.now().strftime('%H:%M')}

{notes_instruction}

💡 Нотатка збережена в iOS Notes!

🗂️ **Категорії:**
• 💼 Робота
• 👤 Особисте  
• 💡 Ідеї
• 📋 Загальні

📱 **Команди:**
• "Запиши що завтра зустріч"
• "Нотатка: купити подарунок"
• "Ідея для проекту" """
        else:
            return """📝 **Нотатки та Ідеї:**

✍️ **Швидкі нотатки:**
• Автоматичне збереження
• Категоризація
• Синхронізація з iOS Notes

💡 **Ідеї:**
• Запис креативних думок
• Організація по проектах
• Швидкий доступ

📱 **Приклади:**
• "Запиши що маю подзвонити лікарю"
• "Нотатка: рецепт бабусиного борщу"
• "Ідея: додаток для вивчення мов"

Що записати?"""
    
    # Task/Reminder management - MOVED TO TOP PRIORITY
    elif any(word in message_lower for word in ['task', 'завдання', 'todo', 'нагадування', 'remind', 'нагадай']):
        # Enhanced task detection with time parsing
        time_patterns = [
            r'о (\d{1,2}):?(\d{2})?',  # "о 18:00"
            r'(\d{1,2}):(\d{2})',      # "18:00"
            r'через (\d+) хвилин',     # "через 30 хвилин"
            r'через (\d+) годин',      # "через 2 години"
        ]
        
        time_match = None
        for pattern in time_patterns:
            time_match = re.search(pattern, message)
            if time_match:
                break
                
        has_time = bool(time_match)
        has_tomorrow = any(word in message_lower for word in ['завтра', 'tomorrow'])
        has_today = any(word in message_lower for word in ['сьогодні', 'today'])
        
        # Extract task description
        task_keywords = ['нагадай', 'завдання', 'task', 'remind', 'todo']
        task_description = message
        for keyword in task_keywords:
            if keyword in message_lower:
                parts = message_lower.split(keyword, 1)
                if len(parts) > 1:
                    task_description = parts[1].strip()
                break
        
        # If we have specific time info, create reminder
        if has_time and (has_tomorrow or has_today or 'через' in message_lower):
            if 'через' in message_lower:
                if 'хвилин' in message_lower:
                    minutes = int(time_match.group(1)) if time_match else 30
                    time_str = f"через {minutes} хвилин"
                    date_str = "сьогодні"
                elif 'годин' in message_lower:
                    hours = int(time_match.group(1)) if time_match else 1
                    time_str = f"через {hours} годин"
                    date_str = "сьогодні"
            else:
                hour = time_match.group(1)
                minute = time_match.group(2) if time_match.group(2) else "00"
                time_str = f"{hour}:{minute}"
                date_str = "завтра" if has_tomorrow else "сьогодні"
            
            reminder_instruction = f"""
📋 **НАГАДУВАННЯ ГОТОВЕ:**
---
REMINDER_DATA: {{
    "action": "create_reminder",
    "title": "{task_description[:50]}",
    "time": "{time_str}",
    "date": "{date_str}",
    "description": "{task_description}",
    "type": "reminder"
}}
---
"""
            
            return f"""⏰ **Створюю нагадування:**

📝 **Завдання:** {task_description}
🕐 **Час:** {time_str}
📅 **Дата:** {date_str}

✅ **Автоматично додаю в iOS нагадування...**

{reminder_instruction}

💡 Нагадування буде створено у вашому iPhone!"""
        else:
            return """✅ **Система управління завданнями:**

📝 **Категорії завдань:**
• 🔥 Терміново (сьогодні)
• ⭐ Важливо (цей тиждень)
• 📅 Заплановано (майбутнє)
• 🔄 Повторювані (щодня/щотижня)

🎯 **Smart-нагадування:**
• ⏰ За часом (через 1 годину)
• 📍 За локацією (коли прийду додому)
• 📅 За датою (завтра вранці)
• 🔔 Повторювані (щодня о 9:00)

💪 **Приклади:**
• "Нагадай купити молоко о 18:00"
• "Завдання: здати звіт до п'ятниці"
• "Через 30 хвилин нагадай про дзвінок"

Яке завдання додати?"""
    
    # Meeting/encounter requests
    elif any(word in message_lower for word in ['зустріч', 'meeting', 'встреча']):
        # Extract meeting details from message - improved regex for Ukrainian
        time_patterns = [
            r'о (\d{1,2}):?(\d{2})?',  # "о 14:00" or "о 14"  
            r'(\d{1,2}):(\d{2})',      # "14:00"
            r'(\d{1,2}) год',          # "14 год"
        ]
        
        time_match = None
        for pattern in time_patterns:
            time_match = re.search(pattern, message)
            if time_match:
                break
                
        has_time = bool(time_match)
        
        has_tomorrow = any(word in message_lower for word in ['завтра', 'tomorrow'])
        has_today = any(word in message_lower for word in ['сьогодні', 'today'])
        
        location = None
        if 'офіс' in message_lower or 'office' in message_lower:
            location = "офіс"
        elif 'дом' in message_lower or 'home' in message_lower:
            location = "дом"
        elif 'онлайн' in message_lower or 'online' in message_lower:
            location = "онлайн"
            
        # If we have specific time and date info, create calendar event
        if has_time and (has_tomorrow or has_today):
            hour = time_match.group(1)
            minute = time_match.group(2) if time_match.group(2) else "00"
            time_str = f"{hour}:{minute}"
            date_str = "завтра" if has_tomorrow else "сьогодні"
            
            calendar_instruction = f"""
📅 **КАЛЕНДАРНА ПОДІЯ ГОТОВА:**
---
CALENDAR_EVENT_DATA: {{
    "action": "create_calendar_event",
    "title": "Зустріч",
    "time": "{time_str}",
    "date": "{date_str}",
    "location": "{location if location else 'не вказано'}",
    "message": "Зустріч {date_str} о {time_str}"
}}
---
"""
            
            return f"""📅 **Створюю зустріч в календарі:**

🕐 **Час:** {time_str}
📅 **Дата:** {date_str}
📍 **Місце:** {location if location else 'не вказано'}

✅ **Автоматично додаю в iOS календар...**

{calendar_instruction}

💡 Подія буде створена у вашому календарі iPhone!"""
        else:
            return """📅 **Планую зустріч для вас:**

🤝 **Деталі зустрічі:**
• **Коли:** Оберіть дату та час
• **Де:** Визначте локацію (офіс/онлайн/кафе)
• **Хто:** Список учасників
• **Що:** Мета та порядок денний

📝 **Наступні кроки:**
1. Повідомте мені дату та час
2. Я створю подію в календарі
3. Додам нагадування за 15 хвилин

💡 Скажіть: "Зустріч завтра о 14:00" або подібне, і я все налаштую!"""
    
    # Calendar addition requests
    elif any(word in message_lower for word in ['додай в календар', 'add to calendar', 'календар', 'calendar']):
        return """📅 **Додаю в календар:**

✅ **Створюю подію:**
• 📍 Назва: [Буде взята з контексту]
• 🕐 Час: [Вкажіть час]
• 📍 Місце: [Опційно]
• 🔔 Нагадування: Автоматично за 15 хв

🎯 **Приклади команд:**
• "Зустріч з командою завтра о 10:00"
• "День народження Марії 15 березня"
• "Презентація проекту п'ятниця 16:30"

💬 Вкажіть деталі події, і я створю нагадування!"""
    
    # Birthday/celebration planning
    elif any(word in message_lower for word in ['birthday', 'день народження', 'свято', 'святкування']):
        return """🎉 **Планую святкування для вас:**

🎂 **План дня народження:**
• 📅 Дата: [Коли святкуємо?]
• 👥 Гості: [Скільки людей?]
• 🏠 Місце: Дім / Ресторан / Кафе
• 🍰 Торт: Замовлення заздалегідь
• 🎵 Розваги: Музика, ігри, активності
• 🎁 Подарунки: Список ідей

📋 **Чек-лист підготовки:**
✅ Запросити гостей (за тиждень)
✅ Замовити торт (за 2-3 дні)  
✅ Купити декорації
✅ Підготувати меню

🎈 Розкажіть про побажання - допоможу створити ідеальне свято!"""
    
    # Planning tasks with more specificity
    elif any(word in message_lower for word in ['план', 'plan it', 'планувати', 'організувати', 'organize']):
        return """📋 **Створюю персональний план:**

🎯 **Методологія планування:**
1. **Аналіз:** Що потрібно зробити?
2. **Пріоритизація:** Що найважливіше?
3. **Часові рамки:** Коли має бути готово?
4. **Ресурси:** Що потрібно для виконання?
5. **Контроль:** Як відстежуємо прогрес?

🗂️ **Типи планів:**
• 📊 Робочі проекти
• 🏠 Домашні справи  
• 🎓 Навчання та розвиток
• 💪 Фітнес та здоров'я
• 🌟 Особисті цілі

💡 **Приклад:** "Хочу вивчити іспанську за 3 місяці" → отримаєте детальний план!"""
    
    # Weather queries - NEW FUNCTIONALITY
    elif any(word in message_lower for word in ['weather', 'погода', 'temperature', 'температура', 'дощ', 'rain', 'сонце', 'sunny']):
        # Enhanced location extraction from message
        location = await extract_location_with_ai(message)
        
        # Get real weather data
        try:
            weather_data = get_weather_data_sync(location)
        except Exception as e:
            logger.error(f"Error getting weather data: {e}")
            weather_data = {
                "success": False,
                "temperature": "18°C",
                "description": "Помилка отримання даних",
                "mock_data": True
            }
            
        if weather_data["success"]:
            weather_instruction = f"""
🌤️ **ПОГОДНА ІНФОРМАЦІЯ:**
---
WEATHER_DATA: {{
    "action": "get_weather",
    "location": "{weather_data['location']}",
    "temperature": "{weather_data['temperature']}",
    "description": "{weather_data['description']}",
    "humidity": "{weather_data.get('humidity', 'N/A')}%",
    "feels_like": "{weather_data.get('feels_like', 'N/A')}",
    "wind_speed": "{weather_data.get('wind_speed', 'N/A')} м/с",
    "request_type": "current",
    "real_data": true
}}
---
"""
            
            return f"""🌤️ **Актуальна погода в {weather_data['location']}:**\n\n🌡️ **Температура:** {weather_data['temperature']} (відчувається як {weather_data.get('feels_like', 'N/A')})\n☁️ **Опис:** {weather_data['description']}\n💧 **Вологість:** {weather_data.get('humidity', 'N/A')}%\n💨 **Вітер:** {weather_data.get('wind_speed', 'N/A')} м/с\n"""
        else:
            # Fallback to mock data
            weather_instruction = f"""
🌤️ **ПОГОДНА ІНФОРМАЦІЯ:**
---
WEATHER_DATA: {{
    "action": "get_weather",
    "location": "{location}",
    "temperature": "{weather_data['temperature']}",
    "description": "{weather_data['description']}",
    "request_type": "current",
    "real_data": false,
    "error": "{weather_data.get('message', 'API недоступне')}"
}}
---
"""
            
            return f"""🌤️ **Погода в {location} (демо-режим):**\n\n🌡️ **Температура:** {weather_data['temperature']}\n☁️ **Опис:** {weather_data['description']}\n"""
    
    # Contacts and Communication - NEW FUNCTIONALITY
    elif any(word in message_lower for word in ['подзвони', 'call', 'дзвінок', 'sms', 'смс', 'повідомлення', 'message', 'контакт', 'contact']):
        # Extract contact name if mentioned
        contact_keywords = ['подзвони', 'дзвінок', 'повідомлення', 'надішли']
        contact_name = None
        action_type = "call"
        
        if 'sms' in message_lower or 'смс' in message_lower or 'повідомлення' in message_lower:
            action_type = "sms"
            
        # Try to extract contact name
        for keyword in contact_keywords:
            if keyword in message_lower:
                parts = message_lower.split(keyword, 1)
                if len(parts) > 1:
                    potential_name = parts[1].strip().split()[0] if parts[1].strip() else None
                    if potential_name and len(potential_name) > 2:
                        contact_name = potential_name.capitalize()
                break
                
        if not contact_name:
            # Try common names
            names = ['мама', 'тато', 'мамі', 'татові', 'іван', 'марія', 'олексій', 'анна']
            for name in names:
                if name in message_lower:
                    contact_name = name.capitalize()
                    break
        
        if contact_name:
            contact_instruction = f"""
📱 **КОНТАКТНА ДІЯ:**
---
CONTACT_DATA: {{
    "action": "{action_type}",
    "contact_name": "{contact_name}",
    "message": "{message}",
    "type": "communication"
}}
---
"""
            
            action_text = "Дзвоню" if action_type == "call" else "Надсилаю повідомлення"
            return f"""📱 **{action_text} {contact_name}:**

👤 **Контакт:** {contact_name}
📞 **Дія:** {action_text}
🔄 **Виконую...**

{contact_instruction}

💡 Дія буде виконана через iOS!"""
        else:
            return """📱 **Контакти та Комунікація:**

📞 **Доступні дії:**
• Дзвінки: "Подзвони мамі"
• SMS: "Надішли SMS Іванові"
• Повідомлення: "Повідомлення татові що спізнююся"

👥 **Контакти:**
• Використовуйте імена з вашої адресної книги
• Підтримка: мама, тато, родина, друзі

💬 **Приклади:**
• "Подзвони Марії"
• "SMS мамі що все добре"
• "Повідомити Олексію про зустріч"

Вкажіть ім'я контакту!"""
    
    # Finance and Shopping - NEW FUNCTIONALITY  
    elif any(word in message_lower for word in ['витрата', 'витрати', 'expense', 'купити', 'buy', 'shopping', 'покупки', 'список', 'list', 'гроші', 'money', 'грн', 'uah', 'долар', 'dollar']):
        # Detect if it's expense tracking or shopping list
        if any(word in message_lower for word in ['витрата', 'витрати', 'expense', 'грн', 'долар', 'гроші']):
            # Extract amount and description
            amount_match = re.search(r'(\d+(?:\.\d{2})?)\s*(?:грн|uah|долар|dollar|\$)', message_lower)
            amount = amount_match.group(1) if amount_match else None
            
            # Extract expense description
            expense_desc = message.lower()
            for word in ['витрата', 'витрати', 'expense']:
                if word in expense_desc:
                    expense_desc = expense_desc.split(word, 1)[1].strip() if word in expense_desc else expense_desc
                    break
            
            if amount:
                finance_instruction = f"""
💰 **ФІНАНСОВА ОПЕРАЦІЯ:**
---
FINANCE_DATA: {{
    "action": "add_expense",
    "amount": "{amount}",
    "description": "{expense_desc}",
    "currency": "UAH",
    "type": "expense"
}}
---
"""
                
                return f"""💰 **Додаю витрату:**

💵 **Сума:** {amount} грн
📝 **Опис:** {expense_desc}
📅 **Дата:** сьогодні

{finance_instruction}

💡 Витрата збережена в вашому фінансовому треку!"""
            else:
                return """💰 **Фінансовий Трекер:**

💵 **Додавання витрат:**
• "Витрата 150 грн на каву"
• "Expense 25 USD for lunch"
• "Сплатив 500 грн за комунальні"

📊 **Категорії:**
• 🍽️ Їжа та напої
• 🚗 Транспорт  
• 🏠 Дім та побут
• 💼 Робота
• 🎯 Розваги

💡 Вкажіть суму та опис витрати!"""
                
        else:
            # Shopping list functionality
            # Extract items from message
            items = []
            shopping_keywords = ['купити', 'список', 'shopping', 'покупки']
            item_text = message.lower()
            
            for keyword in shopping_keywords:
                if keyword in item_text:
                    item_text = item_text.split(keyword, 1)[1].strip() if keyword in item_text else item_text
                    break
                    
            # Parse items (comma separated or "and" separated)
            if 'та' in item_text or 'і' in item_text or ',' in item_text:
                separators = [',', ' та ', ' і ', ' and ']
                for sep in separators:
                    if sep in item_text:
                        items = [item.strip() for item in item_text.split(sep) if item.strip()]
                        break
            else:
                items = [item_text.strip()] if item_text.strip() else []
                
            if items:
                shopping_instruction = f"""
🛒 **СПИСОК ПОКУПОК:**
---
SHOPPING_DATA: {{
    "action": "add_to_shopping_list",
    "items": {items},
    "message": "Додано в список покупок",
    "type": "shopping"
}}
---
"""
                
                items_text = "\n".join([f"• {item}" for item in items])
                return f"""🛒 **Додаю в список покупок:**

📝 **Товари:**
{items_text}

{shopping_instruction}

💡 Список збережено в iOS Reminders!"""
            else:
                return """🛒 **Список Покупок:**

📝 **Додавання товарів:**
• "Купити молоко та хліб"
• "Список: яблука, банани, сир"
• "Покупки на завтра: м'ясо і овочі"

🛍️ **Категорії:**
• 🥛 Молочні продукти
• 🍞 Хліб та випічка
• 🥕 Овочі та фрукти
• 🥩 М'ясо та риба
• 🧴 Побутова хімія

💡 Перерахуйте товари через кому!"""
    
    # Transport and Navigation - AI-POWERED
    elif await is_navigation_request_ai(message):
        # Use AI to extract navigation details
        navigation_details = await extract_navigation_with_ai(message)
        
        if navigation_details["has_destination"]:
            # Create Apple Maps URL for direct navigation
            destination = navigation_details["destination"]
            transport_type = navigation_details["transport_type"]
            transport_mode = navigation_details["transport_mode"]
            
            # Enhanced Apple Maps URL with better iOS compatibility
            destination_encoded = destination.replace(' ', '+').replace('і', 'i').replace('ї', 'i')
            
            # Multiple URL formats for better compatibility
            apple_maps_url = f"http://maps.apple.com/?daddr={destination_encoded}&dirflg={transport_type}"
            maps_scheme_url = f"maps://?daddr={destination_encoded}&dirflg={transport_type}"
            google_maps_fallback = f"https://www.google.com/maps/dir/?api=1&destination={destination_encoded}&travelmode={transport_type}"
            
            # Return structured response for iOS to handle
            return f"""📍 Прокладаю маршрут до {destination}

🚗 Транспорт: {transport_mode}
📱 Відкриваю Apple Maps...

{{
    "action": "open_maps",
    "destination": "{destination}",
    "transport_type": "{transport_type}",
    "apple_maps_url": "{apple_maps_url}",
    "maps_scheme_url": "{maps_scheme_url}",
    "google_maps_fallback": "{google_maps_fallback}",
    "success": true,
    "message": "Маршрут до {destination} готовий!"
}}"""
        else:
            return """🚗 **Транспорт та Навігація:**

🗺️ **Маршрути:**
• Автомобільні маршрути з пробками
• Громадський транспорт
• Пішохідні маршрути

🚌 **Громадський транспорт:**
• Розклад автобусів/маршруток
• Станції метро
• Час прибуття

📱 **Команди:**
• "Маршрут до [місце]"
• "Пробки на [вулиця]"
• "Як доїхати до [адреса]"

Вкажіть пункт призначення!"""
    
    # News and Information - NEW FUNCTIONALITY
    elif any(word in message_lower for word in ['новини', 'news', 'що нового', 'events', 'події', 'інформація']):
        # Detect news category
        category = "загальні"
        if any(word in message_lower for word in ['спорт', 'sport', 'футбол', 'баскетбол']):
            category = "спорт"
        elif any(word in message_lower for word in ['технології', 'tech', 'it', 'айті']):
            category = "технології"
        elif any(word in message_lower for word in ['політика', 'politics', 'вибори']):
            category = "політика"
        elif any(word in message_lower for word in ['бізнес', 'business', 'економіка']):
            category = "бізнес"
            
        news_instruction = f"""
📰 **НОВИНИ:**
---
NEWS_DATA: {{
    "action": "get_news",
    "category": "{category}",
    "location": "Ukraine",
    "language": "uk",
    "type": "news"
}}
---
"""
        
        return f"""📰 **Останні новини ({category}):**

🔄 **Оновлюю стрічку новин...**
📍 **Регіон:** Україна
🗞️ **Категорія:** {category}

{news_instruction}

💡 Новини будуть відображені в додатку!

📱 **Категорії:**
• 🌍 Загальні новини
• ⚽ Спорт
• 💻 Технології  
• 📅 Політика
• 💼 Бізнес

🎯 **Приклади:**
• "Спортивні новини"
• "Що нового в технологіях?"
• "Останні події" """
    
    # Health and Fitness - NEW FUNCTIONALITY
    elif any(word in message_lower for word in ['здоров\'я', 'health', 'фітнес', 'fitness', 'тренування', 'workout', 'ліки', 'medicine', 'вода', 'water']):
        # Detect health action type
        action_type = "general"
        activity_data = {}
        
        if any(word in message_lower for word in ['тренування', 'workout', 'фітнес', 'біг', 'running']):
            action_type = "workout"
            # Extract workout type
            if 'біг' in message_lower or 'running' in message_lower:
                activity_data['workout_type'] = 'біг'
            elif 'спортзал' in message_lower or 'gym' in message_lower:
                activity_data['workout_type'] = 'спортзал'
            else:
                activity_data['workout_type'] = 'загальне'
                
        elif any(word in message_lower for word in ['ліки', 'medicine', 'таблетки', 'pills']):
            action_type = "medication"
            # Extract medication info
            med_match = re.search(r'(ліки|таблетки|medicine)\s+([а-яa-z]+)', message_lower)
            if med_match:
                activity_data['medication'] = med_match.group(2)
                
        elif any(word in message_lower for word in ['вода', 'water', 'пити', 'drink']):
            action_type = "hydration"
            # Extract water amount
            water_match = re.search(r'(\d+)\s*(мл|ml|л|l)', message_lower)
            if water_match:
                activity_data['amount'] = water_match.group(1)
                activity_data['unit'] = water_match.group(2)
        
        health_instruction = f"""
💊 **ЗДОРОВ'Я:**
---
HEALTH_DATA: {{
    "action": "{action_type}",
    "data": {activity_data},
    "timestamp": "{datetime.now().isoformat()}",
    "type": "health"
}}
---
"""
        
        if action_type == "workout":
            return f"""💪 **Фітнес трекер:**

🏃‍♂️ **Тренування:** {activity_data.get('workout_type', 'загальне')}
⏰ **Час початку:** {datetime.now().strftime('%H:%M')}
📊 **Статус:** Активне

{health_instruction}

💡 Тренування записано в Apple Health!

🎯 **Типи активності:**
• 🏃‍♂️ Біг
• 🏋️‍♂️ Спортзал
• 🚴‍♂️ Велосипед
• 🧘‍♂️ Йога """
            
        elif action_type == "medication":
            medication = activity_data.get('medication', 'ліки')
            return f"""💊 **Нагадування про ліки:**

💊 **Препарат:** {medication}
⏰ **Час прийому:** {datetime.now().strftime('%H:%M')}
✅ **Статус:** Прийнято

{health_instruction}

💡 Запис додано в Health app!

📋 **Функції:**
• Нагадування про прийом
• Трекінг дозування
• Історія прийому """
            
        elif action_type == "hydration":
            amount = activity_data.get('amount', '250')
            unit = activity_data.get('unit', 'мл')
            return f"""💧 **Трекер води:**

💧 **Випито:** {amount} {unit}
📊 **Прогрес:** Оновлено
🎯 **Ціль:** 2000 мл/день

{health_instruction}

💡 Дані збережені в Apple Health!

📈 **Статистика:**
• Денна норма
• Недільний звіт
• Нагадування пити """
        else:
            return """💊 **Здоров'я та Фітнес:**

💪 **Фітнес:**
• Трекінг тренувань
• Кардіо активність  
• Силові вправи
• Калорії

💊 **Ліки:**
• Нагадування про прийом
• Розклад ліків
• Контроль дозування

💧 **Вода:**
• Щоденна норма
• Нагадування пити
• Статистика споживання

📱 **Приклади:**
• "Почав тренування біг"
• "Прийняв ліки аспірин"
• "Випив 500 мл води"

Що відзначити?"""
    
    # Generic responses with better context understanding
    else:
        # Try to detect specific intents
        if any(word in message_lower for word in ['завтра', 'tomorrow', 'сьогодні', 'today']):
            return f"""📅 **Планую на основі часу: "{message}"**

🕐 **Розумію часовий контекст:**
• Завтра = наступний день
• Сьогодні = поточний день  
• Цей тиждень = найближчі 7 днів

💡 **Уточніть деталі:**
• Конкретний час (о 14:00)
• Тип активності (зустріч/завдання/нагадування)
• Локація (якщо потрібно)

🎯 Приклад: "Зустріч завтра о 10:00 в офісі"

Що саме плануємо?"""
        
        elif any(word in message_lower for word in ['час', 'time', 'коли', 'when']):
            return f"""⏰ **Працюю з часом: "{message}"**

🕐 **Формати часу:**
• 24-годинний: 14:00, 09:30
• 12-годинний: 2 PM, 9:30 AM
• Словесний: пополудні, вранці, ввечері

📅 **Дати:**
• Відносні: завтра, післязавтра
• Конкретні: 15 березня, 23.12.2025
• Дні тижня: понеділок, п'ятниця

💭 Додайте більше деталей до вашого запиту!"""
        
        else:
            return f"""💭 **Аналізую запит:** "{message}"

🎯 **Можу допомогти з:**
• 📅 Календарем та плануванням
• ✅ Завданнями та нагадуваннями  
• 🗂️ Організацією проектів
• 💡 Ідеями та порадами

🔍 **Для кращого розуміння додайте:**
• Конкретний час або дату
• Тип активності
• Додаткові деталі

💬 **Приклади:**
• "Нагадай про зустріч завтра"
• "План підготовки до екзамену"
• "Організувати день народження"

Уточніть, будь ласка, що саме потрібно?"""

async def extract_location_with_ai(message: str) -> str:
    """Use OpenAI to intelligently extract city name from natural language"""
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        logger.warning("OpenAI not available, using fallback location extraction")
        return extract_location_fallback(message)
    
    try:
        system_prompt = """Ти - експерт з географії та розпізнавання міст. 
Твоє завдання - витягти назву міста з речення та повернути її у стандартному форматі.

Правила:
1. Для українських міст: повертай у називному відмінку (Київ, Львів, Харків, Одеса)
2. Для англійських міст: повертай англійською (London, New York, Paris)
3. Якщо місто не вказано - поверни "Київ" 
4. Відповідай ЛИШЕ назвою міста, без пояснень
5. Розпізнавай різні відмінки та мови

Приклади:
"Погода у Львові" → "Львів"
"Weather in London" → "London" 
"Харкові сьогодні дощ?" → "Харків"
"What about Paris?" → "Paris"
"Температура" → "Київ"
"в Одесі" → "Одеса"
"New York weather" → "New York" """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=20,
            temperature=0.1
        )
        
        city = response.choices[0].message.content.strip()
        logger.info(f"🤖 AI extracted city: '{city}' from message: '{message}'")
        return city
        
    except Exception as e:
        logger.error(f"❌ OpenAI location extraction failed: {e}")
        return extract_location_fallback(message)

def extract_location_fallback(message: str) -> str:
    """Fallback location extraction for when AI is not available"""
    message_lower = message.lower()
    
    # Simple fallback - check for major Ukrainian cities
    city_mentions = {
        'львів': 'Львів', 'lviv': 'Львів', 'львові': 'Львів',
        'харків': 'Харків', 'kharkiv': 'Харків', 'харкові': 'Харків', 
        'одеса': 'Одеса', 'odesa': 'Одеса', 'одесі': 'Одеса',
        'дніпро': 'Дніпро', 'dnipro': 'Дніпро', 'дніпрі': 'Дніпро'
    }
    
    for key, city in city_mentions.items():
        if key in message_lower:
            return city
            
    return "Київ"  # Default

def get_weather_data_sync(location: str) -> Dict[str, Any]:
    """Get weather data - enhanced mock system with realistic data until API activates"""
    if not OPENWEATHER_API_KEY:
        return generate_realistic_weather_mock(location, "API key not configured")
    
    # Simplified city coordinates mapping - AI handles the recognition
    city_coordinates = {
        # Ukrainian cities
        "київ": {"lat": 50.4501, "lon": 30.5234, "name": "Київ"},
        "львів": {"lat": 49.8397, "lon": 24.0297, "name": "Львів"},
        "харків": {"lat": 49.9935, "lon": 36.2304, "name": "Харків"},
        "одеса": {"lat": 46.4825, "lon": 30.7233, "name": "Одеса"},
        "дніпро": {"lat": 48.4647, "lon": 35.0462, "name": "Дніпро"},
        "запоріжжя": {"lat": 47.8388, "lon": 35.1396, "name": "Запоріжжя"},
        
        # International cities (lowercase for matching)
        "london": {"lat": 51.5074, "lon": -0.1278, "name": "London"},
        "new york": {"lat": 40.7128, "lon": -74.0060, "name": "New York"},
        "paris": {"lat": 48.8566, "lon": 2.3522, "name": "Paris"},
        "berlin": {"lat": 52.5200, "lon": 13.4050, "name": "Berlin"},
        "madrid": {"lat": 40.4168, "lon": -3.7038, "name": "Madrid"},
        "rome": {"lat": 41.9028, "lon": 12.4964, "name": "Rome"},
        "tokyo": {"lat": 35.6762, "lon": 139.6503, "name": "Tokyo"},
        "sydney": {"lat": -33.8688, "lon": 151.2093, "name": "Sydney"}
    }
    
    # Get coordinates for the city (AI already normalized the name)
    location_lower = location.lower().strip()
    coords = city_coordinates.get(location_lower)
    
    if not coords:
        # Default to Kyiv if city not found
        coords = city_coordinates["київ"]
        city_name = f"{location} (fallback: Київ)"
        logger.warning(f"⚠️ City '{location}' not found in coordinates, using Kyiv")
    else:
        city_name = coords["name"]
        logger.info(f"📍 Found coordinates for {location} -> {city_name}")
    
    # Try One Call API 3.0 first
    try:
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "uk",
            "exclude": "minutely,alerts"
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        current = data["current"]
        
        return {
            "success": True,
            "location": city_name,
            "temperature": f"{round(current['temp'])}°C",
            "description": current["weather"][0]["description"].capitalize(),
            "humidity": current["humidity"],
            "pressure": current["pressure"],
            "wind_speed": current.get("wind_speed", 0),
            "feels_like": f"{round(current['feels_like'])}°C",
            "visibility": current.get("visibility", "N/A"),
            "uv_index": current.get("uvi", "N/A"),
            "mock_data": False,
            "api_version": "3.0 One Call"
        }
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"One Call API 3.0 failed: {e}, trying fallback API 2.5...")
        
        # Fallback to standard API 2.5
        try:
            url = f"{OPENWEATHER_BASE_URL}/weather"
            params = {
                "q": city_name,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric",
                "lang": "uk"
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "location": data["name"],
                "temperature": f"{round(data['main']['temp'])}°C",
                "description": data["weather"][0]["description"].capitalize(),
                "humidity": data["main"]["humidity"],
                "pressure": data["main"]["pressure"],
                "wind_speed": data.get("wind", {}).get("speed", 0),
                "feels_like": f"{round(data['main']['feels_like'])}°C",
                "mock_data": False,
                "api_version": "2.5 Standard"
            }
            
        except requests.exceptions.RequestException as e2:
            logger.error(f"Both APIs failed - 3.0: {e}, 2.5: {e2}")
            return generate_realistic_weather_mock(city_name, f"APIs unavailable: {str(e2)}")

def generate_realistic_weather_mock(location: str, error_msg: str) -> Dict[str, Any]:
    """Generate realistic weather data based on location and current time"""
    import random
    from datetime import datetime
    
    current_hour = datetime.now().hour
    current_month = datetime.now().month
    
    # Seasonal temperature adjustments for Ukraine
    if "київ" in location.lower() or "kyiv" in location.lower():
        base_temp = {
            12: -2, 1: -5, 2: -3,  # Winter
            3: 5, 4: 12, 5: 18,    # Spring  
            6: 22, 7: 25, 8: 24,   # Summer
            9: 18, 10: 11, 11: 3   # Autumn
        }.get(current_month, 10)
    else:
        base_temp = 15  # Default
    
    # Daily temperature variation
    if 6 <= current_hour <= 18:  # Day
        temp_adjustment = random.randint(2, 8)
    else:  # Night
        temp_adjustment = random.randint(-5, 2)
        
    temp = base_temp + temp_adjustment
    feels_like = temp + random.randint(-3, 3)
    
    # Weather conditions based on season
    winter_conditions = ["сніг", "хмарно", "туман", "ясно"]
    summer_conditions = ["сонячно", "хмарно", "дощ", "грозове небо"]
    spring_autumn = ["хмарно", "дощ", "ясно", "туман"]
    
    if current_month in [12, 1, 2]:
        conditions = winter_conditions
    elif current_month in [6, 7, 8]:
        conditions = summer_conditions
    else:
        conditions = spring_autumn
        
    description = random.choice(conditions)
    
    return {
        "success": True,
        "location": location,
        "temperature": f"{temp}°C",
        "description": description.capitalize(),
        "humidity": random.randint(40, 85),
        "pressure": random.randint(995, 1025),
        "wind_speed": round(random.uniform(0.5, 8.0), 1),
        "feels_like": f"{feels_like}°C",
        "visibility": "10 км",
        "uv_index": random.randint(0, 8),
        "mock_data": True,
        "api_version": "Enhanced Mock",
        "note": "Realistic demo data until API activates"
    }

async def is_navigation_request_ai(message: str) -> bool:
    """Use AI to detect if message is a navigation/transport request"""
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        # Fallback to simple keyword detection
        message_lower = message.lower()
        navigation_keywords = ['маршрут', 'дорога', 'доїхати', 'проїхати', 'їхати', 'дійти', 'транспорт', 'пробки', 'traffic', 'route', 'навігація', 'проїзд']
        return any(word in message_lower for word in navigation_keywords)
    
    try:
        system_prompt = """Ти - експерт з розпізнавання навігаційних та транспортних запитів.
Твоє завдання - визначити, чи є повідомлення запитом про навігацію, маршрути або транспорт.

Навігаційні запити включають:
- Прохання прокласти маршрут ("як доїхати", "маршрут до", "дійти до")  
- Запити про транспорт ("громадський транспорт", "автобус", "метро")
- Питання про пробки ("пробки на", "traffic")
- Пішохідні маршрути ("як дійти", "пішки")

Відповідай ТІЛЬКИ "YES" або "NO" без пояснень."""

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip().upper()
        return result == "YES"
        
    except Exception as e:
        logger.error(f"❌ AI navigation detection failed: {e}")
        # Fallback to keyword detection
        message_lower = message.lower()
        navigation_keywords = ['маршрут', 'дорога', 'доїхати', 'проїхати', 'їхати', 'дійти', 'транспорт', 'пробки', 'traffic', 'route', 'навігація', 'проїзд']
        return any(word in message_lower for word in navigation_keywords)

async def extract_navigation_with_ai(message: str) -> dict:
    """Use AI to extract navigation details from message"""
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        return extract_navigation_fallback(message)
    
    try:
        system_prompt = """Ти - експерт з витягування навігаційної інформації з тексту.
З повідомлення витягни:
1. Пункт призначення (у називному відмінку)
2. Тип транспорту

Правила для пункту призначення:
- Переведи у називний відмінок: "до офісу" → "Офіс", "в центр" → "Центр"
- Якщо не вказано конкретне місце - поверни null

Правила для транспорту:
- car (автомобіль) - за замовчуванням
- transit (громадський) - якщо згадується автобус, метро, маршрутка  
- walking (пішки) - якщо згадується дійти, пішки, пешком

Відповідай ТІЛЬКИ у форматі JSON:
{
  "destination": "Офіс" або null,
  "transport_type": "car|transit|walking",
  "transport_mode": "автомобіль|громадський транспорт|пішки",
  "has_destination": true/false
}"""

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=100,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        navigation_data = json.loads(result)
        
        logger.info(f"🤖 AI extracted navigation: {navigation_data} from '{message}'")
        return navigation_data
        
    except Exception as e:
        logger.error(f"❌ AI navigation extraction failed: {e}")
        return extract_navigation_fallback(message)

def extract_navigation_fallback(message: str) -> dict:
    """Fallback navigation extraction when AI is not available"""
    message_lower = message.lower()
    
    # Simple destination extraction patterns
    destination_patterns = [
        r'до\s+([а-яі'']+)',
        r'в\s+([а-яі'']+)',  
        r'на\s+([а-яі'']+)',
    ]
    
    destination = None
    for pattern in destination_patterns:
        match = re.search(pattern, message_lower)
        if match:
            potential_dest = match.group(1).strip()
            if len(potential_dest) > 2:
                destination = potential_dest.capitalize()
                break
    
    # Transport type detection
    transport_type = "car"
    transport_mode = "автомобіль"
    
    if any(word in message_lower for word in ['автобус', 'метро', 'маршрутка', 'громадський']):
        transport_type = "transit"
        transport_mode = "громадський транспорт"
    elif any(word in message_lower for word in ['дійти', 'пішки', 'пешком']):
        transport_type = "walking"
        transport_mode = "пішки"
    
    return {
        "destination": destination,
        "transport_type": transport_type,
        "transport_mode": transport_mode,
        "has_destination": destination is not None
    }

# Add OpenAPI tools and multi-agent support
import httpx
from typing import Optional, Dict, Any

# OpenAPI Integration class
class OpenAPIIntegration:
    def __init__(self):
        self.session = httpx.AsyncClient(timeout=30.0)
    
    async def call_external_api(self, url: str, method: str = "GET", headers: Dict[str, str] = None, data: Dict[str, Any] = None):
        """Call external API"""
        try:
            if method.upper() == "GET":
                response = await self.session.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                response = await self.session.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = await self.session.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = await self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return {
                "status_code": response.status_code,
                "success": response.status_code < 400,
                "data": response.json() if response.text else None,
                "text": response.text
            }
        except Exception as e:
            return {
                "status_code": 500,
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def get_weather_via_api(self, city: str) -> Dict[str, Any]:
        """Get weather via OpenWeatherMap API"""
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "API key not found",
                "demo_data": True
            }
        
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",
            "lang": "ua"
        }
        
        result = await self.call_external_api(url, "GET", data=params)
        if result["success"] and result["data"]:
            weather = result["data"]
            return {
                "success": True,
                "location": weather.get("name", city),
                "temperature": f"{weather['main']['temp']:.1f}°C",
                "description": weather["weather"][0]["description"],
                "humidity": f"{weather['main']['humidity']}%",
                "feels_like": f"{weather['main']['feels_like']:.1f}°C",
                "wind_speed": f"{weather['wind']['speed']} м/с",
                "real_data": True
            }
        
        return result
    
    async def get_news_via_api(self, query: str = "Ukraine") -> Dict[str, Any]:
        """Get news via NewsAPI"""
        api_key = os.getenv("NEWS_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "News API key not found",
                "demo_data": True
            }
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": api_key,
            "sortBy": "publishedAt",
            "pageSize": 5,
            "language": "en"
        }
        
        result = await self.call_external_api(url, "GET", data=params)
        return result

# Initialize OpenAPI integration
openapi_integration = OpenAPIIntegration()

# Add to existing imports after the other imports

# Add OpenAPI endpoints after the existing endpoints

@app.post("/api/v1/openapi/call")
async def call_openapi_endpoint(request: Request):
    """Call external API endpoint"""
    try:
        body = await request.json()
        url = body.get("url")
        method = body.get("method", "GET")
        headers = body.get("headers", {})
        data = body.get("data", {})
        
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        result = await openapi_integration.call_external_api(url, method, headers, data)
        
        return {
            "success": result["success"],
            "status_code": result["status_code"],
            "data": result.get("data"),
            "error": result.get("error"),
            "agent_used": "API Integration Specialist",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in OpenAPI call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/openapi/weather/{city}")
async def get_weather_openapi(city: str):
    """Get weather via OpenAPI"""
    try:
        result = await openapi_integration.get_weather_via_api(city)
        
        if result.get("success"):
            return {
                "success": True,
                "weather_data": result,
                "agent_used": "Weather API Specialist",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Fallback to demo data
            demo_weather = generate_demo_weather(city)
            return {
                "success": True,
                "weather_data": demo_weather,
                "agent_used": "Weather Demo Mode",
                "note": "Using demo data - API key not configured",
                "timestamp": datetime.now().isoformat()
            }
    
    except Exception as e:
        logger.error(f"Error getting weather via OpenAPI: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/openapi/news")
async def get_news_openapi(query: str = "Ukraine"):
    """Get news via OpenAPI"""
    try:
        result = await openapi_integration.get_news_via_api(query)
        
        if result.get("success"):
            return {
                "success": True,
                "news_data": result,
                "agent_used": "News API Specialist",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to fetch news"),
                "agent_used": "News API Specialist",
                "note": "News API key not configured",
                "timestamp": datetime.now().isoformat()
            }
    
    except Exception as e:
        logger.error(f"Error getting news via OpenAPI: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/agents")
async def get_available_agents():
    """Get list of available agents"""
    return {
        "agents": [
            {
                "name": "Personal Assistant",
                "role": "General conversation and task management",
                "capabilities": ["navigation", "weather", "calendar", "reminders"]
            },
            {
                "name": "Navigation Specialist", 
                "role": "AI-powered navigation and routing",
                "capabilities": ["directions", "maps", "transport_modes"]
            },
            {
                "name": "Weather Specialist",
                "role": "Weather information and forecasts", 
                "capabilities": ["current_weather", "forecasts", "alerts"]
            },
            {
                "name": "API Integration Specialist",
                "role": "External API calls and data integration",
                "capabilities": ["openapi", "external_services", "data_fetching"]
            },
            {
                "name": "Calendar Manager",
                "role": "Event and meeting management",
                "capabilities": ["events", "scheduling", "reminders"]
            }
        ],
        "timestamp": datetime.now().isoformat()
    }

# Add missing functions before the existing generate_smart_response function

async def extract_city_from_message(message: str) -> str:
    """Extract city name from message using AI"""
    return await extract_location_with_ai(message)

def get_weather_icon(description: str) -> str:
    """Get weather emoji icon based on description"""
    description_lower = description.lower()
    
    if any(word in description_lower for word in ['сонце', 'ясно', 'sunny', 'clear']):
        return "☀️"
    elif any(word in description_lower for word in ['хмарно', 'cloudy', 'overcast']):
        return "☁️"
    elif any(word in description_lower for word in ['дощ', 'rain', 'дрібний']):
        return "🌧️"
    elif any(word in description_lower for word in ['сніг', 'snow', 'снігопад']):
        return "❄️"
    elif any(word in description_lower for word in ['туман', 'fog', 'mist']):
        return "🌫️"
    elif any(word in description_lower for word in ['гроза', 'thunder', 'storm']):
        return "⛈️"
    else:
        return "🌤️"

def generate_demo_weather(city: str) -> dict:
    """Generate demo weather data"""
    import random
    from datetime import datetime
    
    current_month = datetime.now().month
    
    # Seasonal temperature for Ukrainian cities
    if city.lower() in ['київ', 'kyiv', 'kiev']:
        base_temp = {
            12: -2, 1: -5, 2: -3,  # Winter
            3: 5, 4: 12, 5: 18,    # Spring  
            6: 22, 7: 25, 8: 24,   # Summer
            9: 18, 10: 11, 11: 3   # Autumn
        }.get(current_month, 10)
    else:
        base_temp = 15
    
    temp = base_temp + random.randint(-3, 6)
    feels_like = temp + random.randint(-2, 3)
    
    conditions = ["ясно", "хмарно", "дощ", "сонячно"]
    description = random.choice(conditions)
    
    return {
        "location": city,
        "temperature": f"{temp}°C",
        "description": description,
        "humidity": f"{random.randint(40, 85)}%",
        "feels_like": f"{feels_like}°C",
        "wind_speed": f"{random.uniform(0.5, 8.0):.1f} м/с"
    }

async def ai_extract_navigation_info(message: str) -> dict:
    """Extract navigation info using AI - wrapper for existing function"""
    return await extract_navigation_with_ai(message)

if __name__ == "__main__":
    logger.info("🚀 Starting CrashCurse Backend - Fixed Version")
    
    uvicorn.run(
        app,  # Використовуємо app напряму замість строки
        host="0.0.0.0",
        port=8000,
        reload=False,  # ВІДКЛЮЧАЄМО reload щоб уникнути перезапусків
        log_level="info"
    ) 