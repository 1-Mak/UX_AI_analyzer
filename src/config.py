"""
Centralized configuration for UX AI Audit System
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
REPORTS_DIR = DATA_DIR / "reports"
LOGS_DIR = ROOT_DIR / "logs"

# Create directories if they don't exist
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ===== LLM Configuration =====
# Architecture: OpenAI GPT-5 (primary for vision) + DeepSeek (auxiliary for text)
# - OpenAI gpt-5-mini: Most cost-effective vision model ($0.25/1M input, $2/1M output)
# - OpenAI gpt-5.2: Enhanced vision with 50% fewer errors ($1.75/1M input, $14/1M output)
# - OpenAI gpt-5.2-pro: Most powerful but expensive ($21/1M input, $168/1M output)
# - DeepSeek: Fast text tasks (sentiment analysis, JSON parsing, simple reasoning)

# OpenAI Configuration (Primary for Vision)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")

# Google Gemini Configuration (Fallback - optional)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

# DeepSeek Configuration (Auxiliary LLM - optional)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# Application Settings
MAX_STEPS = int(os.getenv("MAX_STEPS", "15"))
SCREENSHOT_TIMEOUT = int(os.getenv("SCREENSHOT_TIMEOUT", "30000"))
DEFAULT_VIEWPORT_WIDTH = int(os.getenv("DEFAULT_VIEWPORT_WIDTH", "1920"))
DEFAULT_VIEWPORT_HEIGHT = int(os.getenv("DEFAULT_VIEWPORT_HEIGHT", "1080"))

# Grid Overlay Settings (Module A)
GRID_SIZE = int(os.getenv("GRID_SIZE", "100"))
GRID_COLOR = os.getenv("GRID_COLOR", "rgba(255,0,0,0.3)")

# Navigation Settings
NAVIGATION_TIMEOUT = int(os.getenv("NAVIGATION_TIMEOUT", "30000"))
PAGE_LOAD_WAIT = int(os.getenv("PAGE_LOAD_WAIT", "2000"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "audit.log"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ux_audit")

# Nielsen's 10 Heuristics (Module A)
NIELSEN_HEURISTICS = [
    "Visibility of system status",
    "Match between system and the real world",
    "User control and freedom",
    "Consistency and standards",
    "Error prevention",
    "Recognition rather than recall",
    "Flexibility and efficiency of use",
    "Aesthetic and minimalist design",
    "Help users recognize, diagnose, and recover from errors",
    "Help and documentation"
]

# Personas (Module B) - Educational Context
PERSONAS = {
    "student": {
        "name": "Студент",
        "name_en": "Student",
        "age": 20,
        "tech_level": "высокий",
        "characteristics": [
            "Активный пользователь мобильных устройств",
            "Многозадачность и быстрое переключение между разделами",
            "Ограниченное время между парами",
            "Привычка к современным UI паттернам (свайпы, жесты)"
        ],
        "goals": [
            "Быстро найти расписание занятий",
            "Скачать учебные материалы",
            "Сдать домашнее задание онлайн",
            "Проверить оценки и зачетку",
            "Найти контакты преподавателя"
        ],
        "pain_points": [
            "Долгая загрузка на мобильном интернете",
            "Непонятная навигация в личном кабинете",
            "Мелкий текст на мобильных",
            "Отсутствие push-уведомлений"
        ],
        "devices": ["mobile", "tablet", "desktop"],
        "time_pressure": "высокое",
        "system_prompt": "Ты студент, 20 лет. Ты опытный пользователь интернета, активно используешь смартфон. У тебя мало времени между парами, поэтому тебе нужно быстро найти нужную информацию. Ты ожидаешь, что интерфейс будет интуитивным и современным, как в популярных приложениях."
    },
    "applicant": {
        "name": "Абитуриент",
        "name_en": "Applicant",
        "age": 17,
        "tech_level": "средний",
        "characteristics": [
            "Первый раз на сайте университета",
            "Стресс от выбора будущей профессии",
            "Часто заходит вместе с родителями",
            "Сравнивает несколько университетов"
        ],
        "goals": [
            "Узнать проходные баллы на программу",
            "Посмотреть список вступительных экзаменов",
            "Найти информацию о стоимости обучения",
            "Понять процесс подачи документов",
            "Найти дни открытых дверей"
        ],
        "pain_points": [
            "Слишком много непонятных терминов",
            "Информация раскидана по разным разделам",
            "Нет четкой инструкции 'как поступить'",
            "Устаревшие данные (прошлогодние проходные баллы)"
        ],
        "devices": ["mobile", "desktop"],
        "time_pressure": "среднее",
        "system_prompt": "Ты абитуриент, 17 лет, выбираешь учебное заведение. Ты впервые на этом сайте и немного волнуешься. Тебе нужна понятная информация о поступлении без сложных терминов. Ты будешь сравнивать эту информацию с другими вариантами."
    },
    "teacher": {
        "name": "Преподаватель",
        "name_en": "Teacher",
        "age": 45,
        "tech_level": "средний",
        "characteristics": [
            "Использует компьютер в основном для работы",
            "Ценит стабильность и привычные паттерны",
            "Много административной работы",
            "Может работать с планшета в аудитории"
        ],
        "goals": [
            "Загрузить оценки студентов",
            "Опубликовать учебные материалы",
            "Посмотреть список студентов в группе",
            "Забронировать аудиторию",
            "Согласовать расписание консультаций"
        ],
        "pain_points": [
            "Слишком много кликов для простых действий",
            "Непонятная система загрузки файлов",
            "Нет возможности массовых операций",
            "Интерфейс не адаптирован под планшет"
        ],
        "devices": ["desktop", "tablet"],
        "time_pressure": "низкое",
        "system_prompt": "Ты преподаватель, 45 лет. Ты используешь сайт регулярно для работы со студентами и публикации материалов. Ты ценишь эффективность и не любишь, когда интерфейс меняется без причины. Ты хочешь выполнять задачи быстро и без лишних кликов."
    }
}

# Sentiment Labels (Module D)
SENTIMENT_LABELS = {
    "POSITIVE": 1,
    "NEUTRAL": 0,
    "NEGATIVE": -1
}

# Validate critical configuration
def validate_config():
    """Validate that critical configuration values are set"""
    errors = []
    warnings = []

    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is not set (required for primary LLM)")

    if not GEMINI_API_KEY:
        warnings.append("GEMINI_API_KEY is not set (optional fallback)")

    if not DEEPSEEK_API_KEY:
        warnings.append("DEEPSEEK_API_KEY is not set (optional auxiliary LLM)")

    if warnings:
        print(f"⚠ Warnings: {', '.join(warnings)}")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")

if __name__ == "__main__":
    validate_config()
    print("✓ Configuration validated successfully")
