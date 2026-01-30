"""
Sentiment analysis logic for Module D
Uses DeepSeek API for fast and accurate sentiment detection
"""
import json
import re
from typing import List, Dict, Any, Optional

from src.utils.deepseek_helper import DeepSeekHelper, is_deepseek_available
from src.models import BehaviorStep
from .sentiment_config import EMOTION_CATEGORIES


class SentimentAnalyzer:
    """
    Analyzes sentiment of behavioral step texts using DeepSeek API

    Supports two modes:
    - Fast mode (deepseek-chat): Quick sentiment classification
    - Deep mode (deepseek-reasoner): Chain-of-thought analysis with reasoning
    """

    def __init__(self, use_batch: bool = True, use_reasoner: bool = False):
        """
        Initialize sentiment analyzer

        Args:
            use_batch: Use batch API for efficiency (recommended)
            use_reasoner: Use deepseek-reasoner for deeper analysis (slower but more accurate)
        """
        if not is_deepseek_available():
            raise ValueError(
                "DeepSeek API not configured. Module D requires DEEPSEEK_API_KEY.\n"
                "Get your key from: https://platform.deepseek.com/api_keys"
            )

        self.deepseek = DeepSeekHelper()
        self.use_batch = use_batch
        self.use_reasoner = use_reasoner

    def extract_analysis_text(self, step: Dict[str, Any]) -> str:
        """
        Extract text for sentiment analysis from a behavior step

        Args:
            step: Behavior step dictionary

        Returns:
            Combined text for analysis
        """
        texts = []

        # Primary: agent_thought (main reasoning)
        if step.get("agent_thought"):
            texts.append(step["agent_thought"])

        # Secondary: reasoning from action_taken JSON
        action_taken = step.get("action_taken", "")
        if action_taken:
            try:
                if isinstance(action_taken, str):
                    action_data = json.loads(action_taken)
                else:
                    action_data = action_taken

                if isinstance(action_data, dict) and action_data.get("reasoning"):
                    texts.append(action_data["reasoning"])
            except (json.JSONDecodeError, TypeError):
                pass

        return " ".join(texts) if texts else ""

    def detect_emotion_keywords(self, text: str) -> Dict[str, List[str]]:
        """
        Detect emotion keywords in text

        Args:
            text: Text to analyze

        Returns:
            Dictionary of detected keywords by emotion category
        """
        text_lower = text.lower()
        detected = {}

        for emotion, keywords in EMOTION_CATEGORIES.items():
            found = [kw for kw in keywords if kw in text_lower]
            if found:
                detected[emotion] = found

        return detected

    def analyze_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment of a single step

        Args:
            step: Behavior step dictionary

        Returns:
            Analysis result with sentiment, keywords, etc.
        """
        text = self.extract_analysis_text(step)

        if not text:
            return {
                "step_id": step.get("step_id"),
                "text_analyzed": "",
                "sentiment": "NEUTRAL",
                "keywords": {},
                "status": step.get("status", "unknown")
            }

        # Get sentiment - use reasoner if enabled for deeper analysis
        if self.use_reasoner:
            result = self.deepseek.analyze_sentiment_with_reasoning(text)
            sentiment = result.get("sentiment", "NEUTRAL")
            extra_data = {
                "confidence": result.get("confidence"),
                "emotion_type": result.get("emotion_type"),
                "reasoning": result.get("reasoning", "")[:500]  # Truncate reasoning
            }
        else:
            sentiment = self.deepseek.analyze_sentiment_fast(text)
            extra_data = {}

        # Detect emotion keywords
        keywords = self.detect_emotion_keywords(text)

        result = {
            "step_id": step.get("step_id"),
            "text_analyzed": text[:200] + "..." if len(text) > 200 else text,
            "original_sentiment": step.get("sentiment"),
            "analyzed_sentiment": sentiment,
            "keywords": keywords,
            "status": step.get("status", "unknown")
        }

        # Add extra data from reasoner if available
        if extra_data:
            result.update(extra_data)

        return result

    def analyze_steps_batch(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze sentiment for multiple steps efficiently using batch API

        Args:
            steps: List of behavior step dictionaries

        Returns:
            List of analysis results
        """
        # If using reasoner, analyze one by one (reasoner doesn't support batch)
        if self.use_reasoner:
            print("    (Using DeepSeek Reasoner - analyzing with chain-of-thought...)")
            return [self.analyze_step(step) for step in steps]

        # Extract texts for analysis
        texts_to_analyze = []
        step_mapping = []  # Track which step each text belongs to

        for step in steps:
            text = self.extract_analysis_text(step)
            if text:
                texts_to_analyze.append(text)
                step_mapping.append(step)
            else:
                step_mapping.append(None)  # Mark steps with no text

        # Batch sentiment analysis
        if texts_to_analyze and self.use_batch:
            try:
                batch_results = self.deepseek.batch_sentiment_analysis(texts_to_analyze)

                # Map results back to steps
                text_idx = 0
                results = []

                for i, step in enumerate(steps):
                    if step_mapping[i] is not None:
                        # Get sentiment from batch result
                        if text_idx < len(batch_results):
                            sentiment = batch_results[text_idx].get("sentiment", "NEUTRAL")
                        else:
                            sentiment = "NEUTRAL"

                        text = self.extract_analysis_text(step)
                        keywords = self.detect_emotion_keywords(text)

                        results.append({
                            "step_id": step.get("step_id"),
                            "text_analyzed": text[:200] + "..." if len(text) > 200 else text,
                            "original_sentiment": step.get("sentiment"),
                            "analyzed_sentiment": sentiment,
                            "keywords": keywords,
                            "status": step.get("status", "unknown")
                        })

                        text_idx += 1
                    else:
                        # No text to analyze
                        results.append({
                            "step_id": step.get("step_id"),
                            "text_analyzed": "",
                            "original_sentiment": step.get("sentiment"),
                            "analyzed_sentiment": "NEUTRAL",
                            "keywords": {},
                            "status": step.get("status", "unknown")
                        })

                return results

            except Exception as e:
                print(f"  Warning: Batch analysis failed, falling back to individual: {e}")

        # Fallback: analyze one by one
        return [self.analyze_step(step) for step in steps]

    def quick_sentiment_check(self, text: str) -> str:
        """
        Quick sentiment check without full analysis

        Args:
            text: Text to check

        Returns:
            Sentiment label
        """
        return self.deepseek.analyze_sentiment_fast(text)


if __name__ == "__main__":
    # Quick test
    if is_deepseek_available():
        analyzer = SentimentAnalyzer()

        test_steps = [
            {"step_id": 1, "agent_thought": "На главной странице вижу меню", "status": "success"},
            {"step_id": 2, "agent_thought": "Не могу найти кнопку поиска", "status": "success"},
            {"step_id": 3, "agent_thought": "Отлично, нашёл нужный раздел!", "status": "success"}
        ]

        print("Testing SentimentAnalyzer...")
        results = analyzer.analyze_steps_batch(test_steps)

        for r in results:
            print(f"Step {r['step_id']}: {r['analyzed_sentiment']} - {r['keywords']}")
    else:
        print("DeepSeek API not configured, skipping test")
