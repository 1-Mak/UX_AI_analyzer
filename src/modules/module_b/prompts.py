"""
Prompt templates for Module B - Behavioral Simulator
"""
from typing import List, Optional, Dict, Any
from src.config import PERSONAS


# =============================================================================
# SYSTEM PROMPT TEMPLATE
# =============================================================================

BEHAVIORAL_AGENT_SYSTEM = """Ты {persona_name}, {persona_age} лет.

{persona_system_prompt}

КОНТЕКСТ ПРОЕКТА: Ты используешь веб-сайт.

ТВОЯ ТЕКУЩАЯ ЗАДАЧА: {task}

Ты видишь скриншот текущего состояния страницы и упрощённый DOM с интерактивными элементами.
Твоя цель - выполнить задачу, действуя как реальный пользователь с твоей персоной.

{action_space}

{response_format}

{history_context}
"""


# =============================================================================
# ACTION SPACE DESCRIPTION
# =============================================================================

ACTION_SPACE_DESCRIPTION = """
🎯 ДОСТУПНЫЕ ДЕЙСТВИЯ:

1. **click** - Кликнуть на элемент
   - target: ID элемента из DOM (число или строка)
   - Пример: {"action_type": "click", "target": "5", "reasoning": "Клик на нужную ссылку"}

2. **type** - Ввести текст в поле ввода
   - target: ID поля ввода
   - value: текст для ввода
   - Пример: {"action_type": "type", "target": "search-input", "value": "поисковый запрос", "reasoning": "Ввожу поисковый запрос"}

3. **scroll_down** - Прокрутить страницу вниз
   - Без параметров
   - Пример: {"action_type": "scroll_down", "reasoning": "Ищу контент ниже на странице"}

4. **scroll_up** - Прокрутить страницу вверх
   - Без параметров
   - Пример: {"action_type": "scroll_up", "reasoning": "Возвращаюсь к верхней части страницы"}

5. **wait** - Подождать загрузки контента
   - Без параметров
   - Пример: {"action_type": "wait", "reasoning": "Жду загрузки страницы"}

6. **navigate** - Перейти на конкретный URL
   - value: полный URL
   - Пример: {"action_type": "navigate", "value": "https://example.com/page/", "reasoning": "Перехожу на нужную страницу"}

7. **back** - Вернуться на предыдущую страницу
   - Без параметров
   - Пример: {"action_type": "back", "reasoning": "Возвращаюсь назад, зашёл не туда"}

8. **task_complete** - Сообщить о завершении задачи
   - Используй когда задача ВЫПОЛНЕНА
   - Пример: {"action_type": "task_complete", "reasoning": "Нашёл нужную информацию"}

⚠️ ВАЖНО:
- Используй ID элементов из DOM (data-audit-id или id)
- НЕ придумывай ID, используй только те, что видишь в DOM
- Если элемент не найден - попробуй прокрутить страницу или найти альтернативу
"""


# =============================================================================
# RESPONSE FORMAT
# =============================================================================

RESPONSE_FORMAT_TEMPLATE = """
📤 ФОРМАТ ОТВЕТА (ТОЛЬКО валидный JSON, без комментариев):

{
  "current_state_analysis": "Краткое описание того, что ты видишь на странице (1-2 предложения)",
  "progress_towards_task": "Насколько близко ты к выполнению задачи (1 предложение)",
  "next_action": {
    "action_type": "click|type|scroll_down|scroll_up|wait|navigate|back|task_complete",
    "target": "ID элемента (только для click и type)",
    "value": "текст или URL (только для type и navigate)",
    "reasoning": "Почему ты выбрал это действие (1 предложение)"
  },
  "task_status": "in_progress|completed|blocked",
  "emotional_state": "POSITIVE|NEUTRAL|NEGATIVE"
}

📋 ПОЯСНЕНИЯ К ПОЛЯМ:
- task_status:
  - "in_progress" - задача ещё не выполнена, продолжаю работу
  - "completed" - задача ВЫПОЛНЕНА (нашёл нужную информацию/страницу)
  - "blocked" - не могу продолжить (ошибка, недоступный элемент, тупик)
- emotional_state - твоё эмоциональное состояние как пользователя:
  - POSITIVE - всё понятно, легко ориентируюсь
  - NEUTRAL - нормально, но есть небольшие затруднения
  - NEGATIVE - раздражён, запутался, не понимаю интерфейс
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_step_history(history: List[Dict[str, Any]], max_steps: int = 5) -> str:
    """
    Format recent step history for LLM context

    Args:
        history: List of BehaviorStep dicts or objects
        max_steps: Maximum number of steps to include

    Returns:
        Formatted string with recent actions
    """
    if not history:
        return "Это твой первый шаг. Начни с изучения страницы."

    recent = history[-max_steps:] if len(history) > max_steps else history

    lines = ["📜 ПОСЛЕДНИЕ ДЕЙСТВИЯ:"]
    for step in recent:
        # Handle both dict and object
        if hasattr(step, 'step_id'):
            step_id = step.step_id
            action = step.action_taken
            status = step.status
            url = step.url
        else:
            step_id = step.get('step_id', '?')
            action = step.get('action_taken', '?')
            status = step.get('status', '?')
            url = step.get('url', '?')

        status_icon = "✓" if status == "success" else "✗"
        lines.append(f"  {step_id}. {status_icon} {action} (URL: {url})")

    lines.append(f"\nВсего выполнено шагов: {len(history)}")

    return "\n".join(lines)


def get_persona_context(persona_key: str) -> Dict[str, Any]:
    """
    Get persona details from config

    Args:
        persona_key: Key like 'student', 'applicant', 'teacher'

    Returns:
        Persona dictionary or empty dict if not found
    """
    return PERSONAS.get(persona_key, {})


def get_behavioral_prompt(
    persona_key: str,
    task: str,
    step_history: Optional[List[Dict[str, Any]]] = None,
    current_dom: Optional[str] = None,
    current_url: Optional[str] = None
) -> str:
    """
    Generate complete prompt for behavioral simulation

    Args:
        persona_key: Persona key (student, applicant, teacher)
        task: Task description
        step_history: List of previous BehaviorStep objects/dicts
        current_dom: Simplified DOM of current page
        current_url: Current page URL

    Returns:
        Complete formatted prompt for LLM
    """
    # Get persona details
    persona = get_persona_context(persona_key)

    if not persona:
        raise ValueError(f"Unknown persona: {persona_key}")

    persona_name = persona.get('name', 'Пользователь')
    persona_age = persona.get('age', 25)
    persona_system_prompt = persona.get('system_prompt', '')

    # Format history context
    history_context = ""
    if step_history:
        history_context = format_step_history(step_history)
    else:
        history_context = "Это твой первый шаг. Начни с изучения страницы."

    # Add current state context
    state_context = ""
    if current_url:
        state_context += f"\n🌐 ТЕКУЩИЙ URL: {current_url}\n"

    if current_dom:
        # Truncate DOM if too long
        dom_preview = current_dom[:3000] if len(current_dom) > 3000 else current_dom
        state_context += f"\n📄 УПРОЩЁННЫЙ DOM (интерактивные элементы):\n{dom_preview}\n"

    # Build final prompt
    prompt = BEHAVIORAL_AGENT_SYSTEM.format(
        persona_name=persona_name,
        persona_age=persona_age,
        persona_system_prompt=persona_system_prompt,
        task=task,
        action_space=ACTION_SPACE_DESCRIPTION,
        response_format=RESPONSE_FORMAT_TEMPLATE,
        history_context=history_context
    )

    # Add current state
    prompt += state_context

    # Add instruction
    prompt += "\n\n🎯 Проанализируй скриншот и DOM, затем верни JSON с твоим следующим действием."

    return prompt


def get_retry_prompt(original_response: str, error_message: str) -> str:
    """
    Generate retry prompt when LLM returns invalid JSON

    Args:
        original_response: The invalid response from LLM
        error_message: Error message explaining what went wrong

    Returns:
        Retry prompt asking for valid JSON
    """
    return f"""Твой предыдущий ответ содержал ошибку: {error_message}

Твой ответ был:
{original_response[:500]}...

Пожалуйста, верни ТОЛЬКО валидный JSON в следующем формате:
{{
  "current_state_analysis": "...",
  "progress_towards_task": "...",
  "next_action": {{
    "action_type": "click|type|scroll_down|scroll_up|wait|navigate|back|task_complete",
    "target": "ID элемента (если нужен)",
    "value": "значение (если нужно)",
    "reasoning": "..."
  }},
  "task_status": "in_progress|completed|blocked",
  "emotional_state": "POSITIVE|NEUTRAL|NEGATIVE"
}}

ВАЖНО: Верни ТОЛЬКО JSON, без дополнительного текста или markdown.
"""


# =============================================================================
# DEFAULT FALLBACK ACTION
# =============================================================================

DEFAULT_FALLBACK_ACTION = {
    "current_state_analysis": "Не удалось проанализировать страницу",
    "progress_towards_task": "Продолжаю исследование",
    "next_action": {
        "action_type": "scroll_down",
        "target": None,
        "value": None,
        "reasoning": "Прокручиваю страницу для поиска нужных элементов"
    },
    "task_status": "in_progress",
    "emotional_state": "NEUTRAL"
}


if __name__ == "__main__":
    # Test prompt generation
    print("Testing prompt generation...\n")

    test_prompt = get_behavioral_prompt(
        persona_key="student",
        task="Найти нужную информацию",
        step_history=[
            {"step_id": 1, "action_taken": "click on 'Меню'", "status": "success", "url": "https://example.com"}
        ],
        current_dom="<a id=\"1\" text=\"Главная\"/>\n<a id=\"2\" text=\"Каталог\"/>",
        current_url="https://example.com/page/"
    )

    print("Generated prompt (first 2000 chars):")
    print(test_prompt[:2000])
    print("\n" + "="*60)

    print("\n✓ Prompt generation test passed")
