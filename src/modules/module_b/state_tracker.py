"""
State Tracker for Module B - Behavioral Simulator
Tracks simulation state and detects stuck conditions
"""
import json
import logging
from typing import List, Dict, Any, Optional, Union
from src.models import BehaviorStep

logger = logging.getLogger(__name__)


class StateTracker:
    """
    Tracks behavioral simulation state and detects anomalies

    Features:
    - Maintains history of BehaviorStep objects
    - Detects stuck conditions (repeated actions, no URL changes)
    - Counts recent failures
    - Provides progress summaries
    """

    def __init__(self):
        """Initialize StateTracker"""
        self.history: List[BehaviorStep] = []
        self.url_history: List[str] = []
        self.action_history: List[str] = []

    def add_step(self, step: BehaviorStep) -> None:
        """
        Add a step to history

        Args:
            step: BehaviorStep object to add
        """
        self.history.append(step)
        self.url_history.append(step.url)

        # Extract action type from action_taken (may be JSON string)
        action_type = self._extract_action_type(step.action_taken)
        self.action_history.append(action_type)

        logger.debug(f"Added step {step.step_id}: {action_type} at {step.url}")

    def _extract_action_type(self, action_taken: str) -> str:
        """
        Extract action type from action_taken field

        Args:
            action_taken: Action description (may be JSON string or plain text)

        Returns:
            Action type string
        """
        try:
            # Try to parse as JSON
            action_data = json.loads(action_taken)
            return action_data.get("action_type", "unknown")
        except (json.JSONDecodeError, TypeError):
            # Plain text - extract first word or whole string
            if isinstance(action_taken, str):
                return action_taken.split()[0].lower() if action_taken else "unknown"
            return "unknown"

    def is_stuck(self) -> bool:
        """
        Detect if agent is stuck

        Conditions for being stuck:
        1. Same action repeated 3+ times in a row
        2. URL unchanged for 4+ steps with meaningful actions (not just scrolling)

        Returns:
            True if stuck condition detected
        """
        if len(self.history) < 3:
            return False

        # Check 1: Same action repeated 3+ times
        last_3_actions = self.action_history[-3:]
        if len(set(last_3_actions)) == 1:
            # All 3 actions are the same
            action = last_3_actions[0]
            # Scrolling repeatedly is acceptable behavior
            if action not in ["scroll_down", "scroll_up", "wait"]:
                logger.warning(f"Stuck detected: same action '{action}' repeated 3 times")
                return True

        # Check 2: URL unchanged for 4+ steps with non-scroll actions
        if len(self.history) >= 4:
            last_4_urls = self.url_history[-4:]
            if len(set(last_4_urls)) == 1:
                # URL hasn't changed in 4 steps
                last_4_actions = self.action_history[-4:]
                non_scroll_actions = [a for a in last_4_actions if a not in ["scroll_down", "scroll_up", "wait"]]

                # If there were meaningful actions but URL didn't change
                if len(non_scroll_actions) >= 2:
                    logger.warning(f"Stuck detected: URL unchanged for 4 steps with actions: {last_4_actions}")
                    return True

        return False

    def count_recent_failures(self, window: int = 3) -> int:
        """
        Count failures in recent steps

        Args:
            window: Number of recent steps to check

        Returns:
            Count of failed steps
        """
        if not self.history:
            return 0

        recent_steps = self.history[-window:] if len(self.history) >= window else self.history
        failure_count = sum(1 for step in recent_steps if step.status == "failure")

        return failure_count

    def get_progress_summary(self) -> str:
        """
        Generate a human-readable progress summary

        Returns:
            Summary string
        """
        if not self.history:
            return "Симуляция не начата."

        total_steps = len(self.history)
        success_count = sum(1 for step in self.history if step.status == "success")
        failure_count = sum(1 for step in self.history if step.status == "failure")

        # Get unique URLs visited
        unique_urls = len(set(self.url_history))

        # Get last action
        last_step = self.history[-1]
        last_action = self._extract_action_type(last_step.action_taken)

        summary = f"""Прогресс симуляции:
- Всего шагов: {total_steps}
- Успешных: {success_count}
- Неудачных: {failure_count}
- Уникальных URL: {unique_urls}
- Последнее действие: {last_action}
- Текущий URL: {last_step.url}"""

        return summary

    def get_step_history_for_llm(self, max_steps: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent step history formatted for LLM context

        Args:
            max_steps: Maximum number of steps to return

        Returns:
            List of step dictionaries
        """
        recent = self.history[-max_steps:] if len(self.history) > max_steps else self.history

        return [
            {
                "step_id": step.step_id,
                "action_taken": step.action_taken,
                "status": step.status,
                "url": step.url
            }
            for step in recent
        ]

    def get_emotional_trend(self) -> str:
        """
        Analyze emotional state trend over recent steps

        Returns:
            Trend description: 'improving', 'stable', 'declining'
        """
        if len(self.history) < 3:
            return "stable"

        recent_emotions = [
            step.sentiment for step in self.history[-5:]
            if step.sentiment is not None
        ]

        if not recent_emotions:
            return "stable"

        # Score emotions
        emotion_scores = {
            "POSITIVE": 1,
            "NEUTRAL": 0,
            "NEGATIVE": -1
        }

        scores = [emotion_scores.get(e, 0) for e in recent_emotions]

        if len(scores) >= 2:
            # Compare first half to second half
            mid = len(scores) // 2
            first_half_avg = sum(scores[:mid]) / mid if mid > 0 else 0
            second_half_avg = sum(scores[mid:]) / (len(scores) - mid)

            diff = second_half_avg - first_half_avg

            if diff > 0.3:
                return "improving"
            elif diff < -0.3:
                return "declining"

        return "stable"

    def get_last_url(self) -> Optional[str]:
        """
        Get the URL from the last step

        Returns:
            Last URL or None if no steps
        """
        if self.url_history:
            return self.url_history[-1]
        return None

    def reset(self) -> None:
        """Reset all tracking data"""
        self.history.clear()
        self.url_history.clear()
        self.action_history.clear()
        logger.info("StateTracker reset")


def demo_state_tracker():
    """Demo usage of StateTracker"""
    tracker = StateTracker()

    # Simulate some steps
    steps = [
        BehaviorStep(
            step_id=1,
            screenshot="step_01.png",
            dom_snapshot="<html>...</html>",
            agent_thought="Looking at homepage",
            action_taken='{"action_type": "click", "target": "5"}',
            status="success",
            url="https://example.com",
            sentiment="NEUTRAL"
        ),
        BehaviorStep(
            step_id=2,
            screenshot="step_02.png",
            dom_snapshot="<html>...</html>",
            agent_thought="Navigating to target page",
            action_taken='{"action_type": "click", "target": "10"}',
            status="success",
            url="https://example.com/page/",
            sentiment="POSITIVE"
        ),
        BehaviorStep(
            step_id=3,
            screenshot="step_03.png",
            dom_snapshot="<html>...</html>",
            agent_thought="Looking for information",
            action_taken='{"action_type": "scroll_down"}',
            status="success",
            url="https://example.com/page/",
            sentiment="NEUTRAL"
        ),
    ]

    for step in steps:
        tracker.add_step(step)

    print("Progress Summary:")
    print(tracker.get_progress_summary())
    print()

    print(f"Is stuck: {tracker.is_stuck()}")
    print(f"Recent failures: {tracker.count_recent_failures()}")
    print(f"Emotional trend: {tracker.get_emotional_trend()}")
    print()

    print("History for LLM:")
    for item in tracker.get_step_history_for_llm():
        print(f"  {item}")


if __name__ == "__main__":
    demo_state_tracker()
