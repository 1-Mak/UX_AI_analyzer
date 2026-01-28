"""
WCAG Configuration for Module C - Accessibility Scanner
Defines WCAG levels, impact mappings, and rule categories
"""
from typing import Dict, List

# WCAG Levels mapping to axe-core tags
WCAG_LEVELS: Dict[str, List[str]] = {
    "A": ["wcag2a", "wcag21a"],
    "AA": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
    "AAA": ["wcag2a", "wcag2aa", "wcag2aaa", "wcag21a", "wcag21aa", "wcag21aaa"]
}

# Impact levels in order of severity (highest to lowest)
IMPACT_LEVELS: List[str] = ["critical", "serious", "moderate", "minor"]

# Impact level weights for scoring
IMPACT_WEIGHTS: Dict[str, int] = {
    "critical": 10,
    "serious": 5,
    "moderate": 2,
    "minor": 1
}

# Persona-specific accessibility focus areas
# These help prioritize issues based on persona characteristics
PERSONA_ACCESSIBILITY_FOCUS: Dict[str, Dict[str, List[str]]] = {
    "student": {
        "priority_rules": [
            "color-contrast",      # May use screens in various lighting
            "link-name",           # Quick navigation needed
            "heading-order",       # Scanning content
            "bypass"               # Skip repetitive content
        ],
        "description": "Students need fast navigation and clear visual hierarchy"
    },
    "applicant": {
        "priority_rules": [
            "label",               # Form filling is critical
            "form-field-multiple-labels",
            "autocomplete-valid",
            "color-contrast",
            "link-name"
        ],
        "description": "Applicants heavily use forms and need clear instructions"
    },
    "teacher": {
        "priority_rules": [
            "color-contrast",      # Often use projectors
            "image-alt",           # Accessibility for all students
            "document-title",
            "heading-order",
            "table-duplicate-name"
        ],
        "description": "Teachers need accessible content for diverse student audiences"
    },
    "elderly": {
        "priority_rules": [
            "color-contrast",      # Vision issues
            "target-size",         # Motor control
            "link-name",           # Clear labels
            "label",
            "focus-visible"
        ],
        "description": "Elderly users need high contrast and large click targets"
    }
}

# Rule categories for grouping issues in reports
RULE_CATEGORIES: Dict[str, Dict[str, any]] = {
    "images": {
        "rules": ["image-alt", "image-redundant-alt", "input-image-alt", "svg-img-alt"],
        "name_ru": "Изображения",
        "name_en": "Images"
    },
    "forms": {
        "rules": ["label", "select-name", "form-field-multiple-labels", "autocomplete-valid"],
        "name_ru": "Формы",
        "name_en": "Forms"
    },
    "keyboard": {
        "rules": ["keyboard", "tabindex", "focus-visible", "focus-order-semantics"],
        "name_ru": "Клавиатурная навигация",
        "name_en": "Keyboard Navigation"
    },
    "color": {
        "rules": ["color-contrast", "color-contrast-enhanced", "link-in-text-block"],
        "name_ru": "Контраст и цвета",
        "name_en": "Color and Contrast"
    },
    "structure": {
        "rules": ["heading-order", "bypass", "document-title", "landmark-one-main"],
        "name_ru": "Структура страницы",
        "name_en": "Page Structure"
    },
    "links": {
        "rules": ["link-name", "link-in-text-block", "identical-links-same-purpose"],
        "name_ru": "Ссылки",
        "name_en": "Links"
    },
    "tables": {
        "rules": ["td-headers-attr", "table-duplicate-name", "table-fake-caption"],
        "name_ru": "Таблицы",
        "name_en": "Tables"
    },
    "aria": {
        "rules": ["aria-allowed-attr", "aria-required-attr", "aria-valid-attr-value"],
        "name_ru": "ARIA атрибуты",
        "name_en": "ARIA Attributes"
    }
}

# Common rule descriptions in Russian for better UX in reports
RULE_DESCRIPTIONS_RU: Dict[str, str] = {
    "image-alt": "Изображения должны иметь альтернативный текст (alt)",
    "color-contrast": "Недостаточный контраст между текстом и фоном",
    "link-name": "Ссылки должны иметь понятный текст или описание",
    "label": "Поля форм должны иметь связанные метки (label)",
    "heading-order": "Заголовки должны идти в логическом порядке (H1, H2, H3...)",
    "bypass": "Должен быть способ пропустить повторяющийся контент",
    "document-title": "Страница должна иметь заголовок (title)",
    "html-has-lang": "HTML должен иметь атрибут lang",
    "keyboard": "Все интерактивные элементы должны быть доступны с клавиатуры",
    "focus-visible": "Фокус должен быть визуально различим",
    "aria-required-attr": "ARIA элементы должны иметь обязательные атрибуты",
    "aria-valid-attr-value": "ARIA атрибуты должны иметь допустимые значения"
}


def get_wcag_tags(level: str) -> List[str]:
    """
    Get axe-core tags for a WCAG level

    Args:
        level: WCAG level ("A", "AA", or "AAA")

    Returns:
        List of axe-core tag strings

    Raises:
        ValueError: If level is not valid
    """
    level = level.upper()
    if level not in WCAG_LEVELS:
        raise ValueError(f"Invalid WCAG level: {level}. Must be one of: {list(WCAG_LEVELS.keys())}")
    return WCAG_LEVELS[level]


def get_impact_weight(impact: str) -> int:
    """
    Get numeric weight for an impact level

    Args:
        impact: Impact level string

    Returns:
        Numeric weight (higher = more severe)
    """
    return IMPACT_WEIGHTS.get(impact.lower(), 0)


def get_rule_category(rule_id: str) -> str:
    """
    Get category for a rule ID

    Args:
        rule_id: axe-core rule ID

    Returns:
        Category name or "other" if not found
    """
    for category, data in RULE_CATEGORIES.items():
        if rule_id in data["rules"]:
            return category
    return "other"


def get_rule_description_ru(rule_id: str, fallback: str = "") -> str:
    """
    Get Russian description for a rule

    Args:
        rule_id: axe-core rule ID
        fallback: Fallback description if not found

    Returns:
        Russian description or fallback
    """
    return RULE_DESCRIPTIONS_RU.get(rule_id, fallback)


def get_persona_priority_rules(persona_key: str) -> List[str]:
    """
    Get priority accessibility rules for a persona

    Args:
        persona_key: Persona key (student, applicant, teacher, elderly)

    Returns:
        List of priority rule IDs
    """
    focus = PERSONA_ACCESSIBILITY_FOCUS.get(persona_key, {})
    return focus.get("priority_rules", [])
