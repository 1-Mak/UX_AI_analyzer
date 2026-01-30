"""
Module E Configuration - Report Synthesis Settings
"""

# Report sections configuration
REPORT_SECTIONS = {
    "executive_summary": {
        "title": "Executive Summary",
        "title_ru": "Краткое резюме",
        "order": 1,
        "required": True
    },
    "visual_analysis": {
        "title": "Visual Analysis (Module A)",
        "title_ru": "Визуальный анализ (Модуль A)",
        "order": 2,
        "required": False,
        "source": "module_a_results"
    },
    "behavioral_analysis": {
        "title": "Behavioral Analysis (Module B)",
        "title_ru": "Поведенческий анализ (Модуль B)",
        "order": 3,
        "required": False,
        "source": "module_b_results"
    },
    "accessibility_audit": {
        "title": "Accessibility Audit (Module C)",
        "title_ru": "Аудит доступности (Модуль C)",
        "order": 4,
        "required": False,
        "source": "module_c_results"
    },
    "sentiment_analysis": {
        "title": "Sentiment Analysis (Module D)",
        "title_ru": "Анализ эмоций (Модуль D)",
        "order": 5,
        "required": False,
        "source": "module_d_results"
    },
    "recommendations": {
        "title": "Recommendations",
        "title_ru": "Рекомендации",
        "order": 6,
        "required": True
    }
}

# Severity levels for prioritization
SEVERITY_ORDER = ["critical", "high", "serious", "medium", "moderate", "low", "minor"]

# Score thresholds for overall rating
RATING_THRESHOLDS = {
    "excellent": {"min_score": 0.8, "label": "Excellent", "label_ru": "Отлично", "color": "#22c55e"},
    "good": {"min_score": 0.6, "label": "Good", "label_ru": "Хорошо", "color": "#84cc16"},
    "fair": {"min_score": 0.4, "label": "Fair", "label_ru": "Удовлетворительно", "color": "#eab308"},
    "poor": {"min_score": 0.2, "label": "Poor", "label_ru": "Плохо", "color": "#f97316"},
    "critical": {"min_score": 0.0, "label": "Critical", "label_ru": "Критично", "color": "#ef4444"}
}

# Weight factors for overall score calculation
SCORE_WEIGHTS = {
    "visual": 0.25,        # Module A weight
    "behavioral": 0.25,    # Module B weight
    "accessibility": 0.30, # Module C weight (higher - compliance matters)
    "sentiment": 0.20      # Module D weight
}

# Issue type icons (ASCII-safe for Windows console)
ISSUE_ICONS = {
    "critical": "[!!!]",
    "high": "[!!]",
    "serious": "[!]",
    "medium": "[~]",
    "moderate": "[~]",
    "low": "[.]",
    "minor": "[.]"
}

# Module status icons
MODULE_STATUS = {
    "success": "[OK]",
    "partial": "[~]",
    "skipped": "[--]",
    "error": "[X]"
}

# Persona descriptions for report context
PERSONA_CONTEXT = {
    "student": {
        "name": "Student",
        "name_ru": "Студент",
        "description": "Active user looking for information quickly",
        "description_ru": "Активный пользователь, ищет информацию быстро"
    },
    "applicant": {
        "name": "Applicant",
        "name_ru": "Абитуриент",
        "description": "First-time visitor exploring options",
        "description_ru": "Новичок на сайте, изучает условия и требования"
    },
    "teacher": {
        "name": "Teacher",
        "name_ru": "Преподаватель",
        "description": "Experienced user managing content",
        "description_ru": "Опытный пользователь, работает с контентом"
    }
}

# HTML template settings
HTML_SETTINGS = {
    "theme": "light",
    "primary_color": "#3b82f6",
    "font_family": "system-ui, -apple-system, sans-serif",
    "max_width": "1200px"
}
