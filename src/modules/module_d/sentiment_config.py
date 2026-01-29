"""
Configuration constants for Module D - Sentiment Analyzer
"""
from typing import Dict, List

# Weights for calculating sentiment score (-1 to +1)
SENTIMENT_WEIGHTS: Dict[str, int] = {
    "POSITIVE": 1,
    "NEUTRAL": 0,
    "NEGATIVE": -1
}

# Thresholds for trend detection
TREND_THRESHOLDS: Dict[str, float] = {
    "improving": 0.2,    # Difference > 0.2 = improving
    "declining": -0.2,   # Difference < -0.2 = declining
    "stable": 0.0        # Otherwise = stable
}

# Emotion categories for detailed analysis (Russian keywords)
EMOTION_CATEGORIES: Dict[str, List[str]] = {
    "frustration": [
        "не могу", "невозможно", "ужасно", "сложно", "раздражает",
        "бесит", "не работает", "ошибка", "проблема", "не получается"
    ],
    "confusion": [
        "непонятно", "где", "как найти", "не вижу", "потерялся",
        "запутался", "куда", "не понимаю", "странно", "неясно"
    ],
    "satisfaction": [
        "отлично", "нашёл", "удобно", "легко", "понятно",
        "хорошо", "быстро", "классно", "супер", "работает"
    ],
    "neutral": [
        "вижу", "наблюдаю", "перехожу", "кликаю", "ввожу",
        "страница", "открывается", "загружается", "есть", "содержит"
    ]
}

# Expected sentiment based on action status
STATUS_SENTIMENT_EXPECTATION: Dict[str, List[str]] = {
    "success": ["POSITIVE", "NEUTRAL"],
    "failure": ["NEGATIVE", "NEUTRAL"],
    "blocked": ["NEGATIVE"]
}

# Insight templates (Russian)
INSIGHT_TEMPLATES: Dict[str, str] = {
    "trend_improving": "📈 Эмоциональный тренд: улучшение к концу сессии",
    "trend_stable": "➡️ Эмоциональный тренд: стабильный на протяжении сессии",
    "trend_declining": "📉 Эмоциональный тренд: ухудшение к концу сессии",
    "high_negative": "😤 {percent}% шагов сопровождались негативными эмоциями",
    "low_negative": "😊 Только {percent}% шагов вызвали негативные эмоции",
    "pain_points": "🔴 Основные болевые точки: {points}",
    "no_pain_points": "✅ Серьёзных болевых точек не выявлено",
    "task_completed": "✅ Задача выполнена успешно",
    "task_not_completed": "⚠️ Задача не была выполнена - высокая корреляция с негативом",
    "high_failure_correlation": "📊 {percent}% неудачных действий сопровождались негативными эмоциями",
    "recommendation_navigation": "💡 Рекомендация: улучшить навигацию и структуру сайта",
    "recommendation_search": "💡 Рекомендация: добавить или улучшить функцию поиска",
    "recommendation_labels": "💡 Рекомендация: использовать более понятные названия разделов"
}

# Thresholds for generating insights
INSIGHT_THRESHOLDS: Dict[str, float] = {
    "high_negative_rate": 0.25,      # > 25% negative = high
    "high_failure_correlation": 0.6  # > 60% failures with negative = high
}
