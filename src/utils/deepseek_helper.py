"""
DeepSeek API helper for fast auxiliary text tasks
Uses OpenAI-compatible API endpoint
"""
import json
from typing import Optional, List, Dict, Any
from openai import OpenAI

from src.config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL


class DeepSeekHelper:
    """
    Helper class for DeepSeek API interactions

    Use cases:
    - Fast sentiment analysis
    - JSON parsing/extraction
    - Simple text reasoning
    - Validation of outputs

    NOT for:
    - Image analysis (use Gemini)
    - Complex reasoning (use Gemini)
    - Long context (use Gemini)
    """

    def __init__(
        self,
        api_key: Optional[str] = DEEPSEEK_API_KEY,
        model: str = DEEPSEEK_MODEL,
        base_url: str = DEEPSEEK_BASE_URL
    ):
        """
        Initialize DeepSeek helper

        Args:
            api_key: DeepSeek API key
            model: Model name (default: deepseek-chat)
            base_url: API endpoint URL
        """
        if not api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY not set. This is optional - "
                "system will fall back to Gemini if not available.\n"
                "Get your key from: https://platform.deepseek.com/api_keys"
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model

    def complete(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Simple text completion

        Args:
            prompt: User prompt
            temperature: Creativity level (0.0 = deterministic, 1.0 = creative)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Returns:
            Model response text
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

    def analyze_sentiment_fast(self, text: str) -> str:
        """
        Fast sentiment analysis

        Args:
            text: Text to analyze

        Returns:
            Sentiment label: POSITIVE, NEUTRAL, or NEGATIVE
        """
        prompt = f"""Проанализируй тональность текста и верни ТОЛЬКО одно слово: POSITIVE, NEUTRAL или NEGATIVE.

Текст: "{text}"

Ответ:"""

        response = self.complete(
            prompt=prompt,
            temperature=0.0,
            max_tokens=10
        )

        sentiment = response.strip().upper()

        # Validate and normalize
        if "POSITIVE" in sentiment:
            return "POSITIVE"
        elif "NEGATIVE" in sentiment:
            return "NEGATIVE"
        else:
            return "NEUTRAL"

    def extract_json(
        self,
        text: str,
        schema_description: str
    ) -> Dict[str, Any]:
        """
        Extract structured JSON from text

        Args:
            text: Source text
            schema_description: Description of expected JSON schema

        Returns:
            Extracted JSON as dictionary
        """
        prompt = f"""Извлеки структурированные данные из текста в формате JSON.

ОЖИДАЕМАЯ СХЕМА:
{schema_description}

ИСХОДНЫЙ ТЕКСТ:
{text}

Верни ТОЛЬКО валидный JSON, без комментариев.
"""

        response = self.complete(
            prompt=prompt,
            temperature=0.0,
            max_tokens=1500
        )

        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response

            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON from DeepSeek: {e}")
            return {"error": "Failed to parse JSON", "raw": response}

    def validate_output(
        self,
        output: str,
        criteria: str
    ) -> Dict[str, Any]:
        """
        Validate model output against criteria

        Args:
            output: Output to validate
            criteria: Validation criteria

        Returns:
            Validation result with is_valid flag and feedback
        """
        prompt = f"""Проверь, соответствует ли вывод критериям.

КРИТЕРИИ:
{criteria}

ВЫВОД:
{output}

Верни JSON:
{{
  "is_valid": true/false,
  "feedback": "Краткое объяснение"
}}
"""

        response = self.complete(
            prompt=prompt,
            temperature=0.0,
            max_tokens=300
        )

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response

            return json.loads(json_str)
        except json.JSONDecodeError:
            return {"is_valid": False, "feedback": "Не удалось распарсить ответ"}

    def batch_sentiment_analysis(
        self,
        texts: List[str]
    ) -> List[Dict[str, str]]:
        """
        Analyze sentiment for multiple texts in one call

        Args:
            texts: List of texts to analyze

        Returns:
            List of results with text and sentiment
        """
        prompt = f"""Проанализируй тональность каждого текста и верни JSON массив.

ТЕКСТЫ:
{json.dumps(texts, ensure_ascii=False, indent=2)}

Верни JSON массив в формате:
[
  {{"text": "первый текст...", "sentiment": "POSITIVE|NEUTRAL|NEGATIVE"}},
  ...
]
"""

        response = self.complete(
            prompt=prompt,
            temperature=0.0,
            max_tokens=2000
        )

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response

            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: analyze one by one
            return [
                {"text": text[:50] + "...", "sentiment": self.analyze_sentiment_fast(text)}
                for text in texts
            ]


def is_deepseek_available() -> bool:
    """Check if DeepSeek API is configured"""
    return DEEPSEEK_API_KEY is not None


def demo_usage():
    """Demo usage of DeepSeekHelper"""
    if not is_deepseek_available():
        print("⚠ DEEPSEEK_API_KEY not set. Skipping demo.")
        print("Add your key to .env to test DeepSeek integration.")
        return

    helper = DeepSeekHelper()

    # Test 1: Sentiment analysis
    print("\n=== Test 1: Sentiment Analysis ===")
    test_texts = [
        "Я не могу найти кнопку поиска. Это ужасно неудобно!",
        "Страница загружается нормально.",
        "Отличный интерфейс, все понятно!"
    ]

    for text in test_texts:
        sentiment = helper.analyze_sentiment_fast(text)
        print(f"Text: {text}")
        print(f"Sentiment: {sentiment}\n")

    # Test 2: Batch sentiment
    print("\n=== Test 2: Batch Sentiment Analysis ===")
    results = helper.batch_sentiment_analysis(test_texts)
    print(json.dumps(results, ensure_ascii=False, indent=2))

    # Test 3: JSON extraction
    print("\n=== Test 3: JSON Extraction ===")
    sample_text = """
    На сайте есть несколько проблем:
    1. Кнопка поиска слишком мелкая (размер 12px)
    2. Контраст текста низкий (2.1:1)
    3. Форма не имеет лейблов
    """

    result = helper.extract_json(
        sample_text,
        schema_description='{"issues": [{"title": str, "severity": str}]}'
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    demo_usage()
