"""
Google Gemini API helper for multimodal analysis (text + images)
"""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import google.generativeai as genai
from PIL import Image

from src.config import GEMINI_API_KEY, GEMINI_MODEL


class GeminiHelper:
    """Helper class for Google Gemini API interactions"""

    def __init__(self, model_name: str = GEMINI_MODEL, api_key: str = GEMINI_API_KEY):
        """
        Initialize Gemini helper

        Args:
            model_name: Gemini model name (e.g., 'gemini-1.5-pro', 'gemini-2.0-flash-exp')
            api_key: Google API key
        """
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Please add it to your .env file.\n"
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )

        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)

    def analyze_screenshot(
        self,
        image_path: Path,
        prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Analyze a screenshot with a prompt

        Args:
            image_path: Path to screenshot
            prompt: Analysis prompt
            temperature: Creativity level (0.0 = deterministic, 1.0 = creative)

        Returns:
            Model response text
        """
        # Load image
        img = Image.open(image_path)

        # Generate response
        response = self.model.generate_content(
            [prompt, img],
            generation_config=genai.GenerationConfig(
                temperature=temperature,
            )
        )

        return response.text

    def analyze_visual_heuristics(
        self,
        image_path: Path,
        heuristics: List[str],
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze screenshot against Nielsen's heuristics

        Args:
            image_path: Path to screenshot with grid overlay
            heuristics: List of heuristics to check
            custom_prompt: Optional custom prompt (overrides default)

        Returns:
            Dictionary with issues found
        """
        # Use custom prompt if provided, otherwise use default
        if custom_prompt:
            prompt = custom_prompt
        else:
            heuristics_list = "\n".join(f"{i+1}. {h}" for i, h in enumerate(heuristics))

            prompt = f"""Ты эксперт по юзабилити и UX-дизайну. Проанализируй этот скриншот интерфейса на соответствие эвристикам Нильсена.

ЭВРИСТИКИ ДЛЯ ПРОВЕРКИ:
{heuristics_list}

ВАЖНО:
- На скриншоте есть координатная сетка (буквы по горизонтали, цифры по вертикали)
- Указывай точное местоположение проблемы через эти координаты (например, "зона C4")
- Игнорируй эстетику, фокусируйся только на функциональных проблемах
- Оценивай контраст текста, размеры кликабельных элементов, информационную иерархию

ФОРМАТ ОТВЕТА (JSON):
{{
  "issues": [
    {{
      "title": "Краткое название проблемы",
      "severity": "Low|Medium|High|Critical",
      "heuristic": "Какая эвристика нарушена",
      "location": "Координаты (например, C4)",
      "description": "Подробное описание проблемы",
      "recommendation": "Как исправить"
    }}
  ]
}}

Если проблем не найдено, верни пустой массив issues.
"""

        response_text = self.analyze_screenshot(image_path, prompt, temperature=0.3)

        # Try to extract JSON from response
        try:
            # Sometimes models wrap JSON in markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text

            result = json.loads(json_str)
            return result
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from Gemini response: {e}")
            print(f"Raw response: {response_text[:500]}")
            return {"issues": [], "raw_response": response_text}

    def analyze_behavior_step(
        self,
        simplified_dom: str,
        goal: str,
        persona_prompt: str,
        previous_steps: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze current page state and decide next action (ReAct pattern)

        Args:
            simplified_dom: Simplified HTML with interactive elements
            goal: User's goal
            persona_prompt: Persona system prompt
            previous_steps: List of previous actions taken

        Returns:
            Dictionary with thought and action
        """
        previous_context = ""
        if previous_steps:
            previous_context = "\n\nПредыдущие действия:\n" + "\n".join(
                f"{i+1}. {step}" for i, step in enumerate(previous_steps)
            )

        prompt = f"""{persona_prompt}

ТВОЯ ЦЕЛЬ: {goal}

ТЕКУЩЕЕ СОСТОЯНИЕ СТРАНИЦЫ (упрощенный DOM):
{simplified_dom[:3000]}
{previous_context}

ДОСТУПНЫЕ ДЕЙСТВИЯ:
- click <id> - кликнуть по элементу с id
- type <id> <text> - ввести текст в поле
- scroll_down - прокрутить вниз
- scroll_up - прокрутить вверх
- done - цель достигнута

ФОРМАТ ОТВЕТА (JSON):
{{
  "thought": "Что ты видишь и что думаешь о текущей ситуации",
  "action": "Какое действие выполнишь (например: click 5, type 3 'расписание', scroll_down, done)"
}}

ВАЖНО: Если не можешь найти нужный элемент, явно опиши это в поле thought.
"""

        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(temperature=0.7)
        )

        try:
            response_text = response.text

            # Extract JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text

            result = json.loads(json_str)
            return result
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Failed to parse behavior response: {e}")
            return {
                "thought": "Не могу распарсить ответ модели",
                "action": "scroll_down",
                "raw_response": response.text if hasattr(response, 'text') else str(response)
            }

    def analyze_text_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of a text (POSITIVE, NEUTRAL, NEGATIVE)

        Args:
            text: Text to analyze

        Returns:
            Sentiment label
        """
        prompt = f"""Проанализируй тональность этого текста и верни ТОЛЬКО одно слово: POSITIVE, NEUTRAL или NEGATIVE.

Текст: "{text}"

Ответ (одно слово):"""

        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.0,
                max_output_tokens=10
            )
        )

        sentiment = response.text.strip().upper()

        # Validate response
        if sentiment not in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
            # Try to extract from longer response
            if "POSITIVE" in sentiment:
                return "POSITIVE"
            elif "NEGATIVE" in sentiment:
                return "NEGATIVE"
            else:
                return "NEUTRAL"

        return sentiment

    def synthesize_report(
        self,
        visual_issues: List[Dict],
        behavior_log: List[Dict],
        accessibility_issues: List[Dict],
        persona: str
    ) -> Dict[str, Any]:
        """
        Synthesize final report from all module outputs

        Args:
            visual_issues: Issues from Module A
            behavior_log: Steps from Module B
            accessibility_issues: Issues from Module C
            persona: Persona name

        Returns:
            Synthesized report with cross-module insights
        """
        prompt = f"""Ты аналитик UX. Тебе нужно проанализировать результаты автоматического аудита интерфейса и создать итоговый отчет.

КОНТЕКСТ:
Персона: {persona}

ВИЗУАЛЬНЫЕ ПРОБЛЕМЫ (Module A):
{json.dumps(visual_issues, ensure_ascii=False, indent=2)[:2000]}

ПОВЕДЕНЧЕСКИЙ ЛОГ (Module B):
{json.dumps(behavior_log, ensure_ascii=False, indent=2)[:2000]}

ПРОБЛЕМЫ ДОСТУПНОСТИ (Module C):
{json.dumps(accessibility_issues, ensure_ascii=False, indent=2)[:1000]}

ЗАДАЧА:
1. Найди кросс-модульные проблемы (когда визуальная проблема коррелирует с негативным опытом в поведенческом логе)
2. Оцени общий UX-балл от 0 до 100
3. Составь список приоритизированных рекомендаций

ФОРМАТ ОТВЕТА (JSON):
{{
  "overall_score": 65,
  "critical_issues": [
    {{
      "title": "Название проблемы",
      "severity": "Critical",
      "evidence": {{
        "visual": "Что нашел Module A",
        "behavior": "Что показал Module B",
        "code": "Что нашел Module C"
      }},
      "recommendation": "Как исправить"
    }}
  ],
  "recommendations": [
    "Рекомендация 1 (самая приоритетная)",
    "Рекомендация 2",
    "Рекомендация 3"
  ],
  "summary": "Краткий итог аудита (2-3 предложения)"
}}
"""

        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(temperature=0.5)
        )

        try:
            response_text = response.text

            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text

            result = json.loads(json_str)
            return result
        except json.JSONDecodeError as e:
            print(f"Failed to parse synthesis response: {e}")
            return {
                "overall_score": 50,
                "critical_issues": [],
                "recommendations": ["Не удалось синтезировать отчет"],
                "summary": "Ошибка при генерации итогового отчета"
            }


def demo_usage():
    """Demo usage of GeminiHelper"""
    from src.config import SCREENSHOTS_DIR, NIELSEN_HEURISTICS

    helper = GeminiHelper()

    # Test 1: Simple text generation
    print("\n=== Test 1: Visual Analysis ===")
    screenshot = SCREENSHOTS_DIR / "demo_screenshot_grid.png"

    if screenshot.exists():
        result = helper.analyze_visual_heuristics(
            screenshot,
            NIELSEN_HEURISTICS[:3]  # Test with first 3 heuristics
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Screenshot not found: {screenshot}")
        print("Run playwright_helper demo first to create a screenshot")

    # Test 2: Sentiment analysis
    print("\n=== Test 2: Sentiment Analysis ===")
    test_texts = [
        "Я не могу найти кнопку поиска. Это очень неудобно!",
        "Страница загружается нормально.",
        "Отличный интерфейс, все понятно и быстро работает!"
    ]

    for text in test_texts:
        sentiment = helper.analyze_text_sentiment(text)
        print(f"Text: {text[:50]}...")
        print(f"Sentiment: {sentiment}\n")


if __name__ == "__main__":
    demo_usage()
