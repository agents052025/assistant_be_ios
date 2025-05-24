#!/bin/bash

# CrashCurse Backend Launcher
# Автор: CrashCurse Team
# Опис: Скрипт для запуску AI Assistant Backend

echo "🚀 CrashCurse AI Assistant Backend"
echo "==================================="

# Перевіряємо чи активоване віртуальне середовище
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Віртуальне середовище не активоване!"
    echo "📝 Активуйте його командою: source venv/bin/activate або source .venv/bin/activate"
    exit 1
fi

# Перевіряємо чи існує .env файл
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не знайдено!"
    echo "📝 Створіть його з env_example.txt: cp env_example.txt .env"
    exit 1
fi

# Перевіряємо чи зайнятий порт 8000
if lsof -ti:8000 >/dev/null 2>&1; then
    echo "🔄 Порт 8000 зайнятий, завершуємо процеси..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Запускаємо backend
echo "🚀 Запускаємо CrashCurse Backend..."
echo "📍 URL: http://localhost:8000"
echo "📱 Production: https://mobile.labai.ws"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "⏹️  Для зупинки натисніть Ctrl+C"
echo ""

# Запуск з автоматичним перезавантаженням
uvicorn main:app --host 0.0.0.0 --port 8000 --reload 