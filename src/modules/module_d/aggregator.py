"""
Sentiment aggregation and insight generation for Module D
"""
from typing import List, Dict, Any, Optional
from collections import Counter

from .sentiment_config import (
    SENTIMENT_WEIGHTS,
    TREND_THRESHOLDS,
    INSIGHT_TEMPLATES,
    INSIGHT_THRESHOLDS
)


class SentimentAggregator:
    """
    Aggregates sentiment analysis results and generates insights
    """

    def __init__(self, persona_key: Optional[str] = None):
        """
        Initialize aggregator

        Args:
            persona_key: Persona context for tailored insights
        """
        self.persona_key = persona_key

    def calculate_session_score(self, sentiments: List[str]) -> float:
        """
        Calculate average sentiment score for the session

        Args:
            sentiments: List of sentiment labels

        Returns:
            Score from -1.0 (all negative) to +1.0 (all positive)
        """
        if not sentiments:
            return 0.0

        total_weight = sum(
            SENTIMENT_WEIGHTS.get(s, 0) for s in sentiments
        )

        return round(total_weight / len(sentiments), 2)

    def calculate_trend(self, sentiments: List[str]) -> str:
        """
        Calculate emotional trend by comparing first and second half

        Args:
            sentiments: List of sentiment labels in order

        Returns:
            Trend: "improving", "stable", or "declining"
        """
        if len(sentiments) < 2:
            return "stable"

        mid = len(sentiments) // 2
        first_half = sentiments[:mid]
        second_half = sentiments[mid:]

        first_score = self.calculate_session_score(first_half)
        second_score = self.calculate_session_score(second_half)

        diff = second_score - first_score

        if diff > TREND_THRESHOLDS["improving"]:
            return "improving"
        elif diff < TREND_THRESHOLDS["declining"]:
            return "declining"
        else:
            return "stable"

    def calculate_distribution(self, sentiments: List[str]) -> Dict[str, int]:
        """
        Calculate sentiment distribution

        Args:
            sentiments: List of sentiment labels

        Returns:
            Count of each sentiment type
        """
        counter = Counter(sentiments)
        return {
            "POSITIVE": counter.get("POSITIVE", 0),
            "NEUTRAL": counter.get("NEUTRAL", 0),
            "NEGATIVE": counter.get("NEGATIVE", 0)
        }

    def find_pain_points(self, step_analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find steps with negative sentiment (pain points)

        Args:
            step_analysis: List of analyzed steps

        Returns:
            List of pain points with details
        """
        pain_points = []

        for step in step_analysis:
            if step.get("analyzed_sentiment") == "NEGATIVE":
                # Determine emotion type from keywords
                keywords = step.get("keywords", {})
                emotion = "negative"

                if "frustration" in keywords:
                    emotion = "frustration"
                elif "confusion" in keywords:
                    emotion = "confusion"

                pain_points.append({
                    "step_id": step.get("step_id"),
                    "url": step.get("url", ""),
                    "issue": step.get("text_analyzed", ""),
                    "emotion": emotion,
                    "keywords": keywords
                })

        return pain_points

    def correlate_with_failures(
        self,
        step_analysis: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Correlate sentiment with action status

        Args:
            step_analysis: List of analyzed steps

        Returns:
            Correlation statistics
        """
        failures = [s for s in step_analysis if s.get("status") == "failure"]
        successes = [s for s in step_analysis if s.get("status") == "success"]

        # Calculate negative rate for failures
        failure_negative = sum(
            1 for s in failures
            if s.get("analyzed_sentiment") == "NEGATIVE"
        )
        failure_negative_rate = (
            failure_negative / len(failures) if failures else 0
        )

        # Calculate negative rate for successes
        success_negative = sum(
            1 for s in successes
            if s.get("analyzed_sentiment") == "NEGATIVE"
        )
        success_negative_rate = (
            success_negative / len(successes) if successes else 0
        )

        return {
            "total_failures": len(failures),
            "total_successes": len(successes),
            "failure_negative_rate": round(failure_negative_rate, 2),
            "success_negative_rate": round(success_negative_rate, 2),
            "correlation_difference": round(
                failure_negative_rate - success_negative_rate, 2
            )
        }

    def generate_insights(
        self,
        summary: Dict[str, Any],
        pain_points: List[Dict[str, Any]],
        correlation: Dict[str, Any],
        task_completed: bool = False
    ) -> List[str]:
        """
        Generate human-readable insights in Russian

        Args:
            summary: Session summary with scores and distribution
            pain_points: List of identified pain points
            correlation: Failure-sentiment correlation data
            task_completed: Whether the task was completed

        Returns:
            List of insight strings
        """
        insights = []

        # 1. Trend insight
        trend = summary.get("trend", "stable")
        if trend == "improving":
            insights.append(INSIGHT_TEMPLATES["trend_improving"])
        elif trend == "declining":
            insights.append(INSIGHT_TEMPLATES["trend_declining"])
        else:
            insights.append(INSIGHT_TEMPLATES["trend_stable"])

        # 2. Negative rate insight
        distribution = summary.get("distribution", {})
        total = sum(distribution.values())
        negative_count = distribution.get("NEGATIVE", 0)
        negative_rate = negative_count / total if total > 0 else 0

        if negative_rate > INSIGHT_THRESHOLDS["high_negative_rate"]:
            insights.append(
                INSIGHT_TEMPLATES["high_negative"].format(
                    percent=int(negative_rate * 100)
                )
            )
        else:
            insights.append(
                INSIGHT_TEMPLATES["low_negative"].format(
                    percent=int(negative_rate * 100)
                )
            )

        # 3. Pain points insight
        if pain_points:
            # Group by step_id
            step_ids = [str(p["step_id"]) for p in pain_points[:3]]
            points_str = f"шаги {', '.join(step_ids)}"
            insights.append(
                INSIGHT_TEMPLATES["pain_points"].format(points=points_str)
            )
        else:
            insights.append(INSIGHT_TEMPLATES["no_pain_points"])

        # 4. Task completion insight
        if task_completed:
            insights.append(INSIGHT_TEMPLATES["task_completed"])
        else:
            if negative_rate > 0.2:
                insights.append(INSIGHT_TEMPLATES["task_not_completed"])

        # 5. Failure correlation insight
        failure_neg_rate = correlation.get("failure_negative_rate", 0)
        if (
            correlation.get("total_failures", 0) > 0 and
            failure_neg_rate > INSIGHT_THRESHOLDS["high_failure_correlation"]
        ):
            insights.append(
                INSIGHT_TEMPLATES["high_failure_correlation"].format(
                    percent=int(failure_neg_rate * 100)
                )
            )

        # 6. Recommendation based on pain points
        if pain_points:
            # Analyze keywords to suggest recommendations
            all_keywords = {}
            for p in pain_points:
                for emotion, kws in p.get("keywords", {}).items():
                    if emotion not in all_keywords:
                        all_keywords[emotion] = []
                    all_keywords[emotion].extend(kws)

            if "confusion" in all_keywords:
                insights.append(INSIGHT_TEMPLATES["recommendation_navigation"])
            elif "frustration" in all_keywords:
                # Check for search-related frustration
                frustration_kws = " ".join(all_keywords.get("frustration", []))
                if "найти" in frustration_kws or "поиск" in frustration_kws:
                    insights.append(INSIGHT_TEMPLATES["recommendation_search"])
                else:
                    insights.append(INSIGHT_TEMPLATES["recommendation_labels"])

        return insights

    def aggregate(
        self,
        step_analysis: List[Dict[str, Any]],
        task_status: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Perform full aggregation of sentiment analysis

        Args:
            step_analysis: List of analyzed steps
            task_status: Final task status

        Returns:
            Complete aggregation result
        """
        # Extract sentiments
        sentiments = [
            s.get("analyzed_sentiment", "NEUTRAL")
            for s in step_analysis
        ]

        # Calculate metrics
        session_score = self.calculate_session_score(sentiments)
        trend = self.calculate_trend(sentiments)
        distribution = self.calculate_distribution(sentiments)

        # Find pain points
        pain_points = self.find_pain_points(step_analysis)

        # Correlate with failures
        correlation = self.correlate_with_failures(step_analysis)

        # Build summary
        total = len(sentiments)
        summary = {
            "session_score": session_score,
            "trend": trend,
            "distribution": distribution,
            "positive_rate": round(distribution["POSITIVE"] / total, 2) if total else 0,
            "negative_rate": round(distribution["NEGATIVE"] / total, 2) if total else 0,
            "failure_negative_correlation": correlation["failure_negative_rate"]
        }

        # Generate insights
        task_completed = task_status == "completed"
        insights = self.generate_insights(
            summary, pain_points, correlation, task_completed
        )

        return {
            "summary": summary,
            "pain_points": pain_points,
            "correlation": correlation,
            "insights": insights
        }


if __name__ == "__main__":
    # Quick test
    aggregator = SentimentAggregator(persona_key="student")

    test_analysis = [
        {"step_id": 1, "analyzed_sentiment": "NEUTRAL", "status": "success", "keywords": {}},
        {"step_id": 2, "analyzed_sentiment": "NEGATIVE", "status": "success", "keywords": {"confusion": ["где"]}},
        {"step_id": 3, "analyzed_sentiment": "NEUTRAL", "status": "success", "keywords": {}},
        {"step_id": 4, "analyzed_sentiment": "NEGATIVE", "status": "failure", "keywords": {"frustration": ["не могу"]}},
        {"step_id": 5, "analyzed_sentiment": "POSITIVE", "status": "success", "keywords": {"satisfaction": ["нашёл"]}}
    ]

    result = aggregator.aggregate(test_analysis, task_status="completed")

    print("Session Score:", result["summary"]["session_score"])
    print("Trend:", result["summary"]["trend"])
    print("Distribution:", result["summary"]["distribution"])
    print("Pain Points:", len(result["pain_points"]))
    print("\nInsights:")
    for insight in result["insights"]:
        print(f"  {insight}")
