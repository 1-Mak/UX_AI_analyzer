"""
HuggingFace Inference API helper for vision-language models (Qwen2.5-VL)
"""
import json
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
from huggingface_hub import InferenceClient

from src.config import HF_TOKEN, HF_VISION_MODEL


class HuggingFaceHelper:
    """Helper class for HuggingFace Inference API with vision models"""

    def __init__(self, token: str = HF_TOKEN, model: str = HF_VISION_MODEL):
        """
        Initialize HuggingFace helper

        Args:
            token: HuggingFace API token
            model: Model ID (default: Qwen/Qwen2.5-VL-3B-Instruct)
        """
        if not token:
            raise ValueError(
                "HF_TOKEN not set. Please add it to your .env file.\n"
                "Get your token from: https://huggingface.co/settings/tokens"
            )

        self.token = token
        self.model = model
        self.client = InferenceClient(token=token)

    def _encode_image(self, image_path: Path) -> str:
        """
        Encode image to base64 string

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def analyze_screenshot(
        self,
        image_path: Path,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.3
    ) -> str:
        """
        Analyze a screenshot with a prompt using Qwen2.5-VL

        Args:
            image_path: Path to screenshot
            prompt: Analysis prompt
            max_tokens: Maximum tokens in response
            temperature: Creativity level (0.0 = deterministic, 1.0 = creative)

        Returns:
            Model response text
        """
        # Prepare message with image
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{self._encode_image(image_path)}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        # Call HF Inference API
        response = self.client.chat_completion(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return response.choices[0].message.content

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
  ],
  "summary": {{
    "total_issues": 0,
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0,
    "overall_assessment": "Краткая общая оценка"
  }}
}}

Если проблем не найдено, верни пустой массив issues."""

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
            print(f"Failed to parse JSON from Qwen response: {e}")
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

ВАЖНО: Если не можешь найти нужный элемент, явно опиши это в поле thought."""

        messages = [{"role": "user", "content": prompt}]

        response = self.client.chat_completion(
            model=self.model,
            messages=messages,
            max_tokens=512,
            temperature=0.7
        )

        try:
            response_text = response.choices[0].message.content

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
                "raw_response": response_text if 'response_text' in locals() else str(response)
            }


def demo_usage():
    """Demo usage of HuggingFaceHelper"""
    from src.config import SCREENSHOTS_DIR, NIELSEN_HEURISTICS

    helper = HuggingFaceHelper()

    # Test: Visual Analysis
    print("\n=== Test: Visual Analysis with Qwen2.5-VL ===")
    screenshots = list(SCREENSHOTS_DIR.glob("*/baseline_screenshot_grid.png"))

    if not screenshots:
        print("No screenshots found. Run main.py first to capture baseline.")
        return

    screenshot = max(screenshots, key=lambda p: p.stat().st_mtime)
    print(f"Analyzing screenshot: {screenshot}")

    result = helper.analyze_visual_heuristics(
        screenshot,
        NIELSEN_HEURISTICS[:3]  # Test with first 3 heuristics
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    demo_usage()
