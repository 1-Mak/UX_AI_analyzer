"""
Module B: Behavioral Simulator
Simulates user behavior through a website using ReAct loop architecture
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from src.models import BehaviorStep
from src.config import OPENAI_API_KEY, OPENAI_MODEL, PERSONAS
from src.utils.openai_helper import OpenAIHelper
from src.utils.playwright_helper import PlaywrightHelper
from .prompts import get_behavioral_prompt, get_retry_prompt, DEFAULT_FALLBACK_ACTION
from .action_executor import ActionExecutor
from .state_tracker import StateTracker

logger = logging.getLogger(__name__)


class ModuleB:
    """
    Behavioral Simulator - simulates persona-driven user behavior

    Uses ReAct (Reasoning + Acting) loop with OpenAI GPT-5-mini vision
    to navigate through a website and complete given tasks.
    """

    def __init__(
        self,
        session_dir: Path,
        persona_key: str,
        task: str,
        max_steps: int = 15,
        api_key: str = None
    ):
        """
        Initialize Module B

        Args:
            session_dir: Directory to save screenshots and logs
            persona_key: Persona key (student, applicant, teacher)
            task: Task description to complete
            max_steps: Maximum simulation steps (default 15)
            api_key: OpenAI API key (defaults to OPENAI_API_KEY from config)
        """
        self.session_dir = Path(session_dir)
        self.persona_key = persona_key
        self.task = task
        self.max_steps = max_steps

        # Validate persona
        if persona_key not in PERSONAS:
            raise ValueError(f"Unknown persona: {persona_key}. Valid: {list(PERSONAS.keys())}")

        self.persona = PERSONAS[persona_key]

        # Initialize LLM
        api_key = api_key or OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for Module B")

        self.llm = OpenAIHelper(api_key=api_key)

        # Initialize state tracker
        self.state_tracker = StateTracker()

        # Action executor will be set during simulation
        self.action_executor: Optional[ActionExecutor] = None

        logger.info(f"ModuleB initialized: persona={persona_key}, task='{task[:50]}...', max_steps={max_steps}")

    async def simulate_behavior(self, starting_url: str) -> Dict[str, Any]:
        """
        Main entry point - run behavioral simulation

        Args:
            starting_url: URL to start the simulation from

        Returns:
            Dictionary with:
                - total_steps: Number of steps taken
                - task_status: Final status (task_completed, max_steps, stuck, failed)
                - termination_reason: Why simulation stopped
                - behavioral_log: List of BehaviorStep dicts
        """
        logger.info(f"Starting behavioral simulation from {starting_url}")

        async with PlaywrightHelper(headless=False) as helper:
            # Initialize action executor
            self.action_executor = ActionExecutor(helper)

            # Navigate to starting URL
            print(f"     Навигация на {starting_url}...")
            success = await helper.navigate(starting_url)
            if not success:
                logger.error(f"Failed to navigate to {starting_url}")
                return {
                    "total_steps": 0,
                    "task_status": "failed",
                    "termination_reason": "navigation_failed",
                    "behavioral_log": []
                }

            # Wait for initial page load
            await asyncio.sleep(2)

            step_id = 0
            termination_reason = None
            task_status = "in_progress"

            # ReAct Loop
            while step_id < self.max_steps:
                step_id += 1
                print(f"     Шаг {step_id}/{self.max_steps}...", end=" ")

                # OBSERVE - Get current page state
                state = await self._observe_state(helper, step_id)

                # REASON - Ask LLM for next action
                llm_decision = await self._reason_next_action(state)

                # ACT - Execute the decided action
                action_result = await self._execute_action(llm_decision.get("next_action", {}))

                # RECORD - Create and store step record
                step = self._create_step_record(
                    step_id=step_id,
                    state=state,
                    llm_decision=llm_decision,
                    action_result=action_result
                )
                self.state_tracker.add_step(step)

                # Log step result
                action_type = llm_decision.get("next_action", {}).get("action_type", "unknown")
                status_icon = "✓" if action_result.get("status") == "success" else "✗"
                print(f"{status_icon} {action_type}")

                # CHECK TERMINATION
                should_stop, reason = self._should_terminate(llm_decision, action_result)
                if should_stop:
                    termination_reason = reason
                    task_status = llm_decision.get("task_status", "unknown")
                    break

                # Human-like delay between actions
                await asyncio.sleep(1.5)

            # If we hit max steps without terminating
            if termination_reason is None:
                termination_reason = "max_steps_reached"
                task_status = "max_steps"

            # Save behavioral log
            self._save_behavioral_log()

            result = {
                "total_steps": step_id,
                "task_status": task_status,
                "termination_reason": termination_reason,
                "behavioral_log": [step.dict() for step in self.state_tracker.history]
            }

            logger.info(f"Simulation complete: {step_id} steps, status={task_status}, reason={termination_reason}")

            return result

    async def _observe_state(self, helper: PlaywrightHelper, step_id: int) -> Dict[str, Any]:
        """
        Capture current page state

        Args:
            helper: PlaywrightHelper instance
            step_id: Current step number

        Returns:
            State dictionary with screenshot_path, dom_snapshot, url, title
        """
        # Take screenshot
        screenshot_filename = f"step_{step_id:02d}_screenshot.png"
        screenshot_path = await helper.take_screenshot(
            filename=screenshot_filename,
            path=self.session_dir,
            full_page=False  # Only viewport for faster processing
        )

        # Get simplified DOM
        simplified_dom = await helper.get_simplified_dom()

        # Get page info
        page_info = await helper.get_page_info()

        return {
            "screenshot_path": screenshot_path,
            "screenshot_filename": screenshot_filename,
            "dom_snapshot": simplified_dom,
            "url": page_info.get("url", ""),
            "title": page_info.get("title", "")
        }

    async def _reason_next_action(self, state: Dict[str, Any], max_retries: int = 2) -> Dict[str, Any]:
        """
        Ask LLM to decide next action based on current state

        Args:
            state: Current page state
            max_retries: Maximum retry attempts for invalid JSON

        Returns:
            LLM decision dictionary
        """
        # Build prompt
        prompt = get_behavioral_prompt(
            persona_key=self.persona_key,
            task=self.task,
            step_history=self.state_tracker.get_step_history_for_llm(),
            current_dom=state.get("dom_snapshot", ""),
            current_url=state.get("url", "")
        )

        # Call LLM with screenshot
        for attempt in range(max_retries + 1):
            try:
                response = self.llm.analyze_screenshot(
                    image_path=state["screenshot_path"],
                    prompt=prompt,
                    max_tokens=2000
                )

                # Parse JSON response
                decision = self._parse_llm_decision(response)
                return decision

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    # Retry with explicit format reminder
                    prompt = get_retry_prompt(response, str(e))
                else:
                    logger.error("Max retries reached, using fallback action")
                    return DEFAULT_FALLBACK_ACTION.copy()

            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return DEFAULT_FALLBACK_ACTION.copy()

        return DEFAULT_FALLBACK_ACTION.copy()

    def _parse_llm_decision(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response into decision dictionary

        Args:
            response: Raw response string from LLM

        Returns:
            Parsed decision dictionary

        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        # Handle markdown code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()

        # Parse JSON
        decision = json.loads(response)

        # Validate required fields
        if "next_action" not in decision:
            decision["next_action"] = {"action_type": "scroll_down", "reasoning": "No action specified"}

        if "task_status" not in decision:
            decision["task_status"] = "in_progress"

        return decision

    async def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the decided action

        Args:
            action: Action dictionary from LLM decision

        Returns:
            Execution result dictionary
        """
        if not action:
            return {"status": "failure", "error": "No action provided"}

        return await self.action_executor.execute(action)

    def _should_terminate(
        self,
        llm_decision: Dict[str, Any],
        action_result: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if simulation should stop

        Args:
            llm_decision: LLM's decision including task_status
            action_result: Result of executing the action

        Returns:
            Tuple of (should_stop, termination_reason)
        """
        task_status = llm_decision.get("task_status", "in_progress")

        # Task completed
        if task_status == "completed" or action_result.get("task_completed"):
            return True, "task_completed"

        # Task blocked
        if task_status == "blocked":
            return True, "task_blocked"

        # Stuck detection
        if self.state_tracker.is_stuck():
            return True, "stuck_detected"

        # Too many recent failures
        if self.state_tracker.count_recent_failures() >= 3:
            return True, "repeated_failures"

        return False, None

    def _create_step_record(
        self,
        step_id: int,
        state: Dict[str, Any],
        llm_decision: Dict[str, Any],
        action_result: Dict[str, Any]
    ) -> BehaviorStep:
        """
        Create a BehaviorStep record

        Args:
            step_id: Step number
            state: Observed state
            llm_decision: LLM's decision
            action_result: Action execution result

        Returns:
            BehaviorStep instance
        """
        next_action = llm_decision.get("next_action", {})

        return BehaviorStep(
            step_id=step_id,
            screenshot=state.get("screenshot_filename", ""),
            dom_snapshot=state.get("dom_snapshot", "")[:5000],  # Truncate for storage
            agent_thought=llm_decision.get("current_state_analysis", "") + " " + llm_decision.get("progress_towards_task", ""),
            action_taken=json.dumps(next_action, ensure_ascii=False),
            status="success" if action_result.get("status") == "success" else "failure",
            url=state.get("url", ""),
            sentiment=llm_decision.get("emotional_state", "NEUTRAL")
        )

    def _save_behavioral_log(self) -> None:
        """Save behavioral log to JSON file"""
        output_file = self.session_dir / "module_b_behavioral_log.json"

        behavioral_log = [step.dict() for step in self.state_tracker.history]

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(behavioral_log, f, ensure_ascii=False, indent=2)

        logger.info(f"Behavioral log saved: {output_file}")

    def print_summary(self, result: Dict[str, Any]) -> None:
        """
        Print human-readable summary of simulation

        Args:
            result: Result from simulate_behavior()
        """
        print("\n" + "="*60)
        print("📊 MODULE B: ПОВЕДЕНЧЕСКАЯ СИМУЛЯЦИЯ - РЕЗУЛЬТАТЫ")
        print("="*60)

        print(f"\n🎭 Персона: {self.persona.get('name', self.persona_key)}")
        print(f"🎯 Задача: {self.task}")
        print(f"\n📈 Статистика:")
        print(f"   - Всего шагов: {result['total_steps']}")
        print(f"   - Статус задачи: {result['task_status']}")
        print(f"   - Причина завершения: {result['termination_reason']}")

        # Show emotional trend
        emotional_trend = self.state_tracker.get_emotional_trend()
        trend_icon = {"improving": "📈", "stable": "➡️", "declining": "📉"}.get(emotional_trend, "➡️")
        print(f"   - Эмоциональный тренд: {trend_icon} {emotional_trend}")

        # Count success/failure
        if result.get("behavioral_log"):
            successes = sum(1 for s in result["behavioral_log"] if s.get("status") == "success")
            failures = sum(1 for s in result["behavioral_log"] if s.get("status") == "failure")
            print(f"   - Успешных действий: {successes}")
            print(f"   - Неудачных действий: {failures}")

        # Show last few actions
        if result.get("behavioral_log"):
            print(f"\n📋 ПОСЛЕДНИЕ ДЕЙСТВИЯ:")
            for step in result["behavioral_log"][-5:]:
                step_id = step.get("step_id", "?")
                action = step.get("action_taken", "")
                try:
                    action_data = json.loads(action)
                    action_type = action_data.get("action_type", "?")
                    reasoning = action_data.get("reasoning", "")[:50]
                except:
                    action_type = action[:30]
                    reasoning = ""

                status_icon = "✓" if step.get("status") == "success" else "✗"
                print(f"   {step_id}. {status_icon} {action_type}: {reasoning}")

        print("\n" + "="*60)


async def demo_module_b():
    """Demo usage of Module B"""
    from src.config import SCREENSHOTS_DIR

    # Create test session directory
    from datetime import datetime
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = SCREENSHOTS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Session directory: {session_dir}")

    # Initialize Module B
    module_b = ModuleB(
        session_dir=session_dir,
        persona_key="student",
        task="Найти нужную информацию на сайте",
        max_steps=10
    )

    # Run simulation
    result = await module_b.simulate_behavior(
        starting_url="https://example.com"
    )

    # Print summary
    module_b.print_summary(result)

    print(f"\n💾 Behavioral log saved to: {session_dir / 'module_b_behavioral_log.json'}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(demo_module_b())
