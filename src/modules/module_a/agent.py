"""
Module A: Visual Inspector
Analyzes UI screenshots against Nielsen's heuristics using OpenAI Vision models
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import ValidationError

from src.models import VisualIssue, AuditConfig
from src.utils.openai_helper import OpenAIHelper
from src.config import OPENAI_API_KEY, OPENAI_MODEL, NIELSEN_HEURISTICS, PERSONAS
from .prompts import get_visual_analysis_prompt

logger = logging.getLogger(__name__)


class ModuleA:
    """
    Visual Inspector - analyzes screenshots for UX/UI issues

    Uses OpenAI Vision models (GPT-5-mini, GPT-5.2, etc.) to detect violations of Nielsen's 10 usability heuristics
    """

    def __init__(self, api_key: str = OPENAI_API_KEY):
        """
        Initialize Module A

        Args:
            api_key: OpenAI API key
        """
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for Module A")

        self.vision_model = OpenAIHelper(api_key=api_key)
        self.heuristics = NIELSEN_HEURISTICS

    def analyze_screenshot(
        self,
        screenshot_path: Path,
        persona_name: Optional[str] = None,
        session_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Analyze a screenshot for UX issues

        Args:
            screenshot_path: Path to screenshot (preferably with grid overlay)
            persona_name: Optional persona context (student, applicant, teacher)
            session_dir: Optional directory to save results

        Returns:
            Dictionary with:
                - issues: List[VisualIssue]
                - summary: Statistics and overall assessment
                - raw_response: Original Gemini response
        """
        logger.info(f"Starting visual analysis for: {screenshot_path}")

        # Validate screenshot exists
        if not screenshot_path.exists():
            raise FileNotFoundError(f"Screenshot not found: {screenshot_path}")

        # Generate prompt with persona context
        prompt = get_visual_analysis_prompt(persona_name)

        # Get persona info for logging
        persona_info = ""
        if persona_name and persona_name in PERSONAS:
            persona_info = f" (Persona: {PERSONAS[persona_name]['name']})"

        logger.info(f"Analyzing with {OPENAI_MODEL}{persona_info}...")

        try:
            # Call OpenAI Vision API (GPT-4o or GPT-4o-mini)
            raw_response = self.vision_model.analyze_visual_heuristics(
                image_path=screenshot_path,
                heuristics=self.heuristics,
                custom_prompt=prompt
            )

            # Parse and validate response
            parsed_result = self._parse_llm_response(raw_response)

            # Save results if session_dir provided
            if session_dir:
                self._save_results(parsed_result, session_dir)

            logger.info(
                f"Analysis complete: {parsed_result['summary']['total_issues']} issues found "
                f"(Critical: {parsed_result['summary']['critical']}, "
                f"High: {parsed_result['summary']['high']}, "
                f"Medium: {parsed_result['summary']['medium']}, "
                f"Low: {parsed_result['summary']['low']})"
            )

            return parsed_result

        except Exception as e:
            logger.error(f"Error during visual analysis: {e}", exc_info=True)
            raise

    def _parse_llm_response(self, raw_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate LLM's JSON response

        Args:
            raw_response: Raw response from OpenAI Vision API

        Returns:
            Validated parsed response with VisualIssue objects
        """
        try:
            # Extract text from response wrapper
            if isinstance(raw_response, dict) and "raw_response" in raw_response:
                response_text = raw_response["raw_response"]
            else:
                response_text = raw_response

            # Debug: print raw response
            logger.debug(f"Raw response type: {type(response_text)}")
            logger.debug(f"Raw response (first 500 chars): {str(response_text)[:500]}")

            # Extract JSON from response
            if isinstance(response_text, str):
                # Try to extract JSON from markdown code blocks if present
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                response_data = json.loads(response_text)
            elif isinstance(response_text, dict):
                response_data = response_text
            else:
                raise ValueError(f"Unexpected response type: {type(response_text)}")

            # Validate issues with Pydantic
            validated_issues = []
            for issue_data in response_data.get("issues", []):
                try:
                    issue = VisualIssue(**issue_data)
                    validated_issues.append(issue)
                except ValidationError as e:
                    logger.warning(f"Invalid issue data, skipping: {e}")
                    continue

            # Get summary (or calculate if missing)
            summary = response_data.get("summary", {})
            if not summary:
                summary = self._calculate_summary(validated_issues)

            return {
                "issues": validated_issues,
                "summary": summary,
                "raw_response": raw_response
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Raw response: {raw_response}")
            print(f"\n[DEBUG] Raw response from GPT-5-mini:")
            print(f"Type: {type(raw_response)}")
            print(f"Content: {raw_response}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")

    def _calculate_summary(self, issues: List[VisualIssue]) -> Dict[str, Any]:
        """
        Calculate summary statistics from issues

        Args:
            issues: List of validated VisualIssue objects

        Returns:
            Summary dictionary with counts and assessment
        """
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }

        for issue in issues:
            severity_counts[issue.severity.lower()] += 1

        total = len(issues)

        # Generate overall assessment
        if severity_counts["critical"] > 0:
            assessment = f"Обнаружены критические проблемы ({severity_counts['critical']}), требующие немедленного исправления."
        elif severity_counts["high"] > 2:
            assessment = f"Найдено {severity_counts['high']} серьезных проблем, снижающих юзабилити."
        elif total > 5:
            assessment = f"Выявлено {total} проблем различной степени серьезности."
        elif total > 0:
            assessment = f"Обнаружены минорные недочеты UX ({total}), не критичные для функциональности."
        else:
            assessment = "Критических проблем не обнаружено. Интерфейс соответствует основным эвристикам юзабилити."

        return {
            "total_issues": total,
            "critical": severity_counts["critical"],
            "high": severity_counts["high"],
            "medium": severity_counts["medium"],
            "low": severity_counts["low"],
            "overall_assessment": assessment
        }

    def _save_results(self, result: Dict[str, Any], session_dir: Path) -> None:
        """
        Save analysis results to JSON file

        Args:
            result: Parsed analysis result
            session_dir: Directory to save results
        """
        output_file = session_dir / "module_a_visual_analysis.json"

        # Convert VisualIssue objects to dicts for JSON serialization
        serializable_result = {
            "issues": [issue.dict() for issue in result["issues"]],
            "summary": result["summary"]
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)

        logger.info(f"Results saved to: {output_file}")

    def print_summary(self, result: Dict[str, Any]) -> None:
        """
        Print human-readable summary of analysis

        Args:
            result: Analysis result from analyze_screenshot()
        """
        summary = result["summary"]
        issues = result["issues"]

        print("\n" + "="*60)
        print("📊 MODULE A: ВИЗУАЛЬНЫЙ АНАЛИЗ - РЕЗУЛЬТАТЫ")
        print("="*60)

        print(f"\n🔍 Всего проблем найдено: {summary['total_issues']}")
        print(f"   🔴 Критических: {summary['critical']}")
        print(f"   🟠 Высокая важность: {summary['high']}")
        print(f"   🟡 Средняя важность: {summary['medium']}")
        print(f"   🟢 Низкая важность: {summary['low']}")

        print(f"\n💬 Общая оценка:")
        print(f"   {summary['overall_assessment']}")

        if issues:
            print(f"\n📋 ДЕТАЛЬНЫЙ СПИСОК ПРОБЛЕМ:")
            print("-"*60)

            # Group by severity
            severity_order = ["Critical", "High", "Medium", "Low"]
            severity_icons = {
                "Critical": "🔴",
                "High": "🟠",
                "Medium": "🟡",
                "Low": "🟢"
            }

            for severity in severity_order:
                severity_issues = [i for i in issues if i.severity == severity]
                if not severity_issues:
                    continue

                print(f"\n{severity_icons[severity]} {severity.upper()} ({len(severity_issues)}):")

                for idx, issue in enumerate(severity_issues, 1):
                    print(f"\n  {idx}. {issue.title}")
                    print(f"     📍 Локация: {issue.location}")
                    print(f"     📏 Эвристика: {issue.heuristic}")
                    print(f"     📝 Проблема: {issue.description}")
                    print(f"     💡 Рекомендация: {issue.recommendation}")

        print("\n" + "="*60)


def demo_module_a():
    """Demo usage of Module A"""
    from src.config import SCREENSHOTS_DIR, OPENAI_MODEL

    # Check for API key
    if not OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not set in .env file")
        print("   Get your key: https://platform.openai.com/api-keys")
        return

    # Find latest screenshot
    screenshots = list(SCREENSHOTS_DIR.glob("*/baseline_screenshot_grid.png"))
    if not screenshots:
        print("❌ No screenshots found. Run main.py first to capture baseline.")
        return

    latest_screenshot = max(screenshots, key=lambda p: p.stat().st_mtime)
    session_dir = latest_screenshot.parent

    print(f"📸 Analyzing screenshot: {latest_screenshot}")
    print(f"📁 Session directory: {session_dir}")
    print(f"🤖 Using model: {OPENAI_MODEL} (OpenAI)")

    # Initialize Module A
    module_a = ModuleA()

    # Run analysis
    result = module_a.analyze_screenshot(
        screenshot_path=latest_screenshot,
        persona_name="student",
        session_dir=session_dir
    )

    # Print results
    module_a.print_summary(result)

    print(f"\n💾 Full results saved to: {session_dir / 'module_a_visual_analysis.json'}")


if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    demo_module_a()
