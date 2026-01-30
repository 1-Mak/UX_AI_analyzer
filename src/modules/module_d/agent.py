"""
Module D - Sentiment Analyzer Agent
Analyzes emotional patterns in behavioral logs to identify UX pain points
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from .analyzer import SentimentAnalyzer
from .aggregator import SentimentAggregator
from src.utils.deepseek_helper import is_deepseek_available


class ModuleD:
    """
    Main class for Module D - Sentiment Analysis

    Analyzes behavioral logs from Module B to extract:
    - Sentiment per step
    - Emotional trend
    - Pain points
    - Actionable insights
    """

    def __init__(
        self,
        session_dir: Path,
        persona_key: Optional[str] = None,
        use_reasoner: bool = False
    ):
        """
        Initialize Module D

        Args:
            session_dir: Directory for saving results
            persona_key: Persona context (student, applicant, teacher)
            use_reasoner: Use DeepSeek Reasoner for deeper analysis (slower but more accurate)
        """
        self.session_dir = Path(session_dir)
        self.persona_key = persona_key
        self.use_reasoner = use_reasoner

        # Check DeepSeek availability
        if not is_deepseek_available():
            raise ValueError(
                "Module D requires DeepSeek API. "
                "Set DEEPSEEK_API_KEY in .env file."
            )

        self.analyzer = SentimentAnalyzer(use_batch=True, use_reasoner=use_reasoner)
        self.aggregator = SentimentAggregator(persona_key=persona_key)

    def _load_behavioral_log(self, log_path: Path) -> Dict[str, Any]:
        """
        Load and validate behavioral log from Module B

        Args:
            log_path: Path to behavioral log JSON

        Returns:
            Parsed behavioral log data with 'steps' key
        """
        if not log_path.exists():
            raise FileNotFoundError(f"Behavioral log not found: {log_path}")

        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both formats: array of steps or object with "steps" key
        if isinstance(data, list):
            # Array format - wrap in object
            return {"steps": data, "_format": "array"}
        elif isinstance(data, dict) and "steps" in data:
            # Object format with steps
            return data
        elif isinstance(data, dict):
            # Single step object - wrap in array
            return {"steps": [data], "_format": "single"}
        else:
            raise ValueError("Invalid behavioral log format")

        return data

    def _extract_task_status(self, log_data: Dict[str, Any]) -> str:
        """
        Extract final task status from behavioral log

        Args:
            log_data: Behavioral log data

        Returns:
            Task status: completed, blocked, or in_progress
        """
        steps = log_data.get("steps", [])
        if not steps:
            return "unknown"

        # Check last step for task_complete action
        last_step = steps[-1]
        action_taken = last_step.get("action_taken", "")

        try:
            if isinstance(action_taken, str):
                action_data = json.loads(action_taken)
            else:
                action_data = action_taken

            if action_data.get("action_type") == "task_complete":
                return "completed"
        except (json.JSONDecodeError, TypeError):
            pass

        # Check summary if available
        summary = log_data.get("summary", {})
        if summary.get("task_status"):
            return summary["task_status"]

        return "in_progress"

    async def analyze_behavioral_log(
        self,
        log_path: Path
    ) -> Dict[str, Any]:
        """
        Main analysis method - analyzes behavioral log

        Args:
            log_path: Path to behavioral log JSON

        Returns:
            Complete analysis result
        """
        # Load log
        log_data = self._load_behavioral_log(log_path)
        steps = log_data.get("steps", [])

        if not steps:
            return {
                "error": "No steps found in behavioral log",
                "timestamp": datetime.now().isoformat()
            }

        print(f"  -> Analyzing {len(steps)} behavior steps...")

        # Add URL to steps if available from log
        for step in steps:
            if "url" not in step:
                step["url"] = ""

        # Analyze steps
        step_analysis = self.analyzer.analyze_steps_batch(steps)

        # Get task status
        task_status = self._extract_task_status(log_data)

        # Aggregate results
        aggregation = self.aggregator.aggregate(
            step_analysis,
            task_status=task_status
        )

        # Build final result
        result = {
            "timestamp": datetime.now().isoformat(),
            "source_file": str(log_path.name),
            "total_steps": len(steps),
            "task_status": task_status,
            "persona": self.persona_key,
            "step_analysis": step_analysis,
            "summary": aggregation["summary"],
            "pain_points": aggregation["pain_points"],
            "correlation": aggregation["correlation"],
            "insights": aggregation["insights"]
        }

        # Save results
        self._save_results(result)

        # Optionally enrich original log
        self._enrich_behavioral_log(log_path, step_analysis)

        return result

    def _enrich_behavioral_log(
        self,
        log_path: Path,
        step_analysis: List[Dict[str, Any]]
    ) -> None:
        """
        Update original behavioral log with analyzed sentiments

        Args:
            log_path: Path to behavioral log
            step_analysis: Analysis results per step
        """
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                log_data = json.load(f)

            # Create mapping step_id -> analyzed_sentiment
            sentiment_map = {
                s["step_id"]: s["analyzed_sentiment"]
                for s in step_analysis
            }

            # Handle both array and object formats
            if isinstance(log_data, list):
                steps = log_data
            else:
                steps = log_data.get("steps", [])

            # Update steps
            for step in steps:
                step_id = step.get("step_id")
                if step_id in sentiment_map:
                    step["sentiment_analyzed"] = sentiment_map[step_id]

            # Save enriched log (preserve original format)
            enriched_path = log_path.parent / "module_b_behavioral_log_enriched.json"
            with open(enriched_path, "w", encoding="utf-8") as f:
                if isinstance(log_data, list):
                    json.dump(log_data, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(log_data, f, ensure_ascii=False, indent=2)

            print(f"  -> Enriched log saved: {enriched_path.name}")

        except Exception as e:
            print(f"  Warning: Could not enrich log: {e}")

    def _save_results(self, result: Dict[str, Any]) -> Path:
        """
        Save analysis results to JSON file

        Args:
            result: Analysis results

        Returns:
            Path to saved file
        """
        output_path = self.session_dir / "module_d_sentiment_analysis.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"  -> Results saved: {output_path.name}")
        return output_path

    def print_summary(self, result: Dict[str, Any]) -> None:
        """
        Print human-readable summary to console

        Args:
            result: Analysis results
        """
        summary = result.get("summary", {})
        pain_points = result.get("pain_points", [])
        insights = result.get("insights", [])

        print("\n  ────────────────────────────────────")
        print("  MODULE D: SENTIMENT ANALYSIS SUMMARY")
        print("  ────────────────────────────────────")

        # Score and trend
        score = summary.get("session_score", 0)
        trend = summary.get("trend", "stable")
        trend_icon = {"improving": "[+]", "stable": "[=]", "declining": "[-]"}.get(trend, "")

        print(f"    Session Score: {score:.2f} (-1 to +1)")
        print(f"    Emotional Trend: {trend_icon} {trend}")

        # Distribution
        dist = summary.get("distribution", {})
        print(f"\n    Distribution:")
        print(f"      POSITIVE: {dist.get('POSITIVE', 0)}")
        print(f"      NEUTRAL: {dist.get('NEUTRAL', 0)}")
        print(f"      NEGATIVE: {dist.get('NEGATIVE', 0)}")

        # Pain points
        if pain_points:
            print(f"\n    Pain Points ({len(pain_points)}):")
            for pp in pain_points[:3]:  # Show top 3
                print(f"      Step {pp['step_id']}: {pp['emotion']}")
                issue = pp.get('issue', '')[:50]
                if issue:
                    print(f"        \"{issue}...\"")

        # Insights
        if insights:
            print(f"\n    Insights:")
            for insight in insights[:5]:  # Show top 5
                print(f"      {insight}")

        print()


async def demo_module_d(use_reasoner: bool = False):
    """Demo function to test Module D

    Args:
        use_reasoner: Use DeepSeek Reasoner for deeper analysis
    """
    from pathlib import Path

    # Find a behavioral log to analyze
    screenshots_dir = Path("screenshots")

    if not screenshots_dir.exists():
        print("No screenshots directory found")
        return

    # Find latest session with behavioral log
    behavioral_logs = list(screenshots_dir.glob("*/module_b_behavioral_log.json"))

    if not behavioral_logs:
        print("No behavioral logs found")
        return

    latest_log = max(behavioral_logs, key=lambda p: p.stat().st_mtime)
    session_dir = latest_log.parent

    mode = "DeepSeek Reasoner (deep)" if use_reasoner else "DeepSeek Chat (fast)"
    print(f"Testing Module D with: {latest_log}")
    print(f"Analysis mode: {mode}")

    # Run analysis
    module_d = ModuleD(
        session_dir=session_dir,
        persona_key="student",
        use_reasoner=use_reasoner
    )

    result = await module_d.analyze_behavioral_log(latest_log)
    module_d.print_summary(result)


if __name__ == "__main__":
    import asyncio

    if is_deepseek_available():
        asyncio.run(demo_module_d())
    else:
        print("DeepSeek API not configured. Set DEEPSEEK_API_KEY in .env")
