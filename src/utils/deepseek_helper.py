"""
DeepSeek API helper for fast auxiliary text tasks
Uses OpenAI-compatible API endpoint

Supports:
- deepseek-chat: Fast responses for simple tasks
- deepseek-reasoner: Chain-of-thought reasoning for complex analysis
"""
import json
from typing import Optional, List, Dict, Any, Tuple
from openai import OpenAI

from src.config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL


# Model constants
DEEPSEEK_CHAT = "deepseek-chat"
DEEPSEEK_REASONER = "deepseek-reasoner"


class DeepSeekHelper:
    """
    Helper class for DeepSeek API interactions

    Use cases:
    - Fast sentiment analysis (deepseek-chat)
    - Deep reasoning and analysis (deepseek-reasoner)
    - JSON parsing/extraction
    - Validation of outputs

    Models:
    - deepseek-chat: Fast, cost-effective for simple tasks
    - deepseek-reasoner: Chain-of-thought reasoning for complex analysis
    """

    def __init__(
        self,
        api_key: Optional[str] = DEEPSEEK_API_KEY,
        model: str = DEEPSEEK_MODEL,
        base_url: str = DEEPSEEK_BASE_URL,
        use_reasoner: bool = False
    ):
        """
        Initialize DeepSeek helper

        Args:
            api_key: DeepSeek API key
            model: Model name (default from config, usually deepseek-chat)
            base_url: API endpoint URL
            use_reasoner: If True, use deepseek-reasoner for complex tasks
        """
        if not api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY not set. This is optional - "
                "system will fall back to other LLMs if not available.\n"
                "Get your key from: https://platform.deepseek.com/api_keys"
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.reasoner_model = DEEPSEEK_REASONER
        self.use_reasoner = use_reasoner

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

    def reason(
        self,
        prompt: str,
        max_tokens: int = 4000
    ) -> Dict[str, str]:
        """
        Use DeepSeek Reasoner for chain-of-thought reasoning

        The reasoner model thinks step-by-step before giving a final answer.
        Returns both the reasoning process and the final answer.

        Args:
            prompt: User prompt (problem to solve)
            max_tokens: Maximum tokens for response

        Returns:
            Dict with 'reasoning' (chain of thought) and 'answer' (final response)
        """
        messages = [{"role": "user", "content": prompt}]

        response = self.client.chat.completions.create(
            model=self.reasoner_model,
            messages=messages,
            max_tokens=max_tokens
        )

        message = response.choices[0].message

        # DeepSeek Reasoner returns reasoning_content with chain-of-thought
        reasoning = getattr(message, 'reasoning_content', '') or ''
        answer = message.content or ''

        return {
            "reasoning": reasoning,
            "answer": answer,
            "model": self.reasoner_model
        }

    def analyze_with_reasoning(
        self,
        text: str,
        task: str
    ) -> Dict[str, Any]:
        """
        Analyze text using chain-of-thought reasoning

        Args:
            text: Text to analyze
            task: Analysis task description

        Returns:
            Dict with reasoning process, answer, and extracted insights
        """
        prompt = f"""Analyze the following text carefully, thinking step by step.

TASK: {task}

TEXT TO ANALYZE:
{text}

Provide your analysis with a clear final answer."""

        result = self.reason(prompt)

        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "task": task,
            "reasoning": result["reasoning"],
            "answer": result["answer"],
            "model": result["model"]
        }

    def analyze_sentiment_with_reasoning(self, text: str) -> Dict[str, Any]:
        """
        Sentiment analysis with chain-of-thought reasoning

        Uses DeepSeek Reasoner for deeper understanding of sentiment,
        including nuances, sarcasm, and context.

        Args:
            text: Text to analyze

        Returns:
            Dict with sentiment, confidence, reasoning, and key phrases
        """
        prompt = f"""Analyze the sentiment of the following text from a UX perspective.

TEXT: "{text}"

Consider:
1. Overall emotional tone (positive, neutral, negative)
2. Key phrases indicating emotion
3. Any frustration, confusion, or satisfaction signals
4. Context and nuances

Respond in JSON format:
{{
    "sentiment": "POSITIVE" or "NEUTRAL" or "NEGATIVE",
    "confidence": 0.0-1.0,
    "emotion_type": "satisfaction/frustration/confusion/neutral/etc",
    "key_phrases": ["phrase1", "phrase2"],
    "explanation": "Brief explanation"
}}"""

        result = self.reason(prompt)

        # Parse the answer as JSON
        try:
            answer = result["answer"]
            if "```json" in answer:
                json_str = answer.split("```json")[1].split("```")[0].strip()
            elif "```" in answer:
                json_str = answer.split("```")[1].split("```")[0].strip()
            else:
                # Try to find JSON in the text
                import re
                json_match = re.search(r'\{[^{}]*\}', answer, re.DOTALL)
                json_str = json_match.group() if json_match else answer

            parsed = json.loads(json_str)
            parsed["reasoning"] = result["reasoning"]
            return parsed

        except (json.JSONDecodeError, AttributeError):
            # Fallback: extract sentiment from text
            answer_upper = result["answer"].upper()
            if "POSITIVE" in answer_upper:
                sentiment = "POSITIVE"
            elif "NEGATIVE" in answer_upper:
                sentiment = "NEGATIVE"
            else:
                sentiment = "NEUTRAL"

            return {
                "sentiment": sentiment,
                "confidence": 0.7,
                "emotion_type": "unknown",
                "key_phrases": [],
                "explanation": result["answer"][:200],
                "reasoning": result["reasoning"]
            }

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


    def analyze_ux_session_deep(
        self,
        session_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Deep analysis of UX session using reasoning

        Analyzes the entire user session to identify patterns,
        pain points, and provide actionable recommendations.

        Args:
            session_steps: List of behavior steps with agent_thought, action, status

        Returns:
            Comprehensive UX analysis with insights
        """
        # Format steps for analysis
        steps_text = []
        for step in session_steps:
            step_desc = f"Step {step.get('step_id', '?')}: "
            step_desc += f"Thought: {step.get('agent_thought', 'N/A')[:150]}"
            step_desc += f" | Status: {step.get('status', 'unknown')}"
            steps_text.append(step_desc)

        prompt = f"""You are a UX expert analyzing a user session on a website.

USER SESSION ({len(session_steps)} steps):
{chr(10).join(steps_text)}

Analyze this session and provide:
1. Overall user experience assessment
2. Identified pain points (frustration moments)
3. Positive moments (successful interactions)
4. Pattern analysis (what worked, what didn't)
5. Specific recommendations for improvement

Respond in JSON:
{{
    "overall_score": 1-10,
    "summary": "Brief session summary",
    "pain_points": [
        {{"step": N, "issue": "description", "severity": "high/medium/low"}}
    ],
    "positive_moments": [
        {{"step": N, "what_worked": "description"}}
    ],
    "patterns": {{
        "navigation": "assessment",
        "findability": "assessment",
        "task_completion": "assessment"
    }},
    "recommendations": [
        {{"priority": "high/medium/low", "suggestion": "specific recommendation"}}
    ],
    "emotional_journey": "description of emotional arc"
}}"""

        result = self.reason(prompt, max_tokens=6000)

        try:
            answer = result["answer"]
            if "```json" in answer:
                json_str = answer.split("```json")[1].split("```")[0].strip()
            elif "```" in answer:
                json_str = answer.split("```")[1].split("```")[0].strip()
            else:
                import re
                json_match = re.search(r'\{[\s\S]*\}', answer)
                json_str = json_match.group() if json_match else answer

            parsed = json.loads(json_str)
            parsed["reasoning_process"] = result["reasoning"]
            return parsed

        except (json.JSONDecodeError, AttributeError) as e:
            return {
                "error": f"Failed to parse: {e}",
                "raw_answer": result["answer"],
                "reasoning_process": result["reasoning"]
            }


def is_deepseek_available() -> bool:
    """Check if DeepSeek API is configured"""
    return DEEPSEEK_API_KEY is not None


def demo_usage():
    """Demo usage of DeepSeekHelper"""
    if not is_deepseek_available():
        print("DeepSeek API not configured. Set DEEPSEEK_API_KEY in .env")
        return

    helper = DeepSeekHelper()

    print("\n" + "="*60)
    print("DeepSeek Helper Demo")
    print("="*60)

    # Test 1: Fast sentiment
    print("\n=== Test 1: Fast Sentiment (deepseek-chat) ===")
    test_texts = [
        "Я не могу найти кнопку поиска. Это ужасно неудобно!",
        "Страница загружается нормально.",
        "Отличный интерфейс, все понятно!"
    ]

    for text in test_texts:
        sentiment = helper.analyze_sentiment_fast(text)
        print(f"  [{sentiment}] {text[:50]}...")

    # Test 2: Reasoning sentiment
    print("\n=== Test 2: Deep Sentiment (deepseek-reasoner) ===")
    complex_text = "Вроде бы нашел нужный раздел, но почему-то расписание не загружается. Может это баг?"

    print(f"  Text: {complex_text}")
    result = helper.analyze_sentiment_with_reasoning(complex_text)
    print(f"  Sentiment: {result.get('sentiment')}")
    print(f"  Confidence: {result.get('confidence')}")
    print(f"  Emotion: {result.get('emotion_type')}")
    print(f"  Key phrases: {result.get('key_phrases')}")
    if result.get('reasoning'):
        print(f"  Reasoning (first 200 chars): {result['reasoning'][:200]}...")

    # Test 3: General reasoning
    print("\n=== Test 3: Chain-of-Thought Reasoning ===")
    problem = "Why might a user have difficulty finding the schedule on a university website?"

    result = helper.reason(problem, max_tokens=2000)
    print(f"  Question: {problem}")
    print(f"  Reasoning (first 300 chars): {result['reasoning'][:300]}...")
    print(f"  Answer (first 200 chars): {result['answer'][:200]}...")

    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60)


if __name__ == "__main__":
    demo_usage()
