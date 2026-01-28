"""
Action Executor for Module B - Behavioral Simulator
Translates LLM actions to Playwright commands
"""
import asyncio
import logging
from typing import Dict, Any, Optional

from src.utils.playwright_helper import PlaywrightHelper

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Executes actions from LLM decisions using Playwright

    Supports actions: click, type, scroll_down, scroll_up, wait, navigate, back, task_complete
    """

    def __init__(self, playwright_helper: PlaywrightHelper):
        """
        Initialize ActionExecutor

        Args:
            playwright_helper: Initialized PlaywrightHelper instance
        """
        self.helper = playwright_helper
        self.default_wait_time = 1.0  # seconds
        self.scroll_pixels = 500

    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action and return result

        Args:
            action: Action dictionary with action_type, target, value, reasoning

        Returns:
            Dictionary with status ('success' or 'failure'), error message if any
        """
        action_type = action.get("action_type", "").lower()

        # Map action types to handlers
        handlers = {
            "click": self._handle_click,
            "type": self._handle_type,
            "scroll_down": self._handle_scroll_down,
            "scroll_up": self._handle_scroll_up,
            "wait": self._handle_wait,
            "navigate": self._handle_navigate,
            "back": self._handle_back,
            "task_complete": self._handle_task_complete,
        }

        handler = handlers.get(action_type)

        if not handler:
            logger.warning(f"Unknown action type: {action_type}")
            return {
                "status": "failure",
                "error": f"Unknown action type: {action_type}",
                "action_type": action_type
            }

        try:
            result = await handler(action)
            result["action_type"] = action_type
            return result
        except Exception as e:
            logger.error(f"Error executing action {action_type}: {e}")
            return {
                "status": "failure",
                "error": str(e),
                "action_type": action_type
            }

    async def _handle_click(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle click action

        Tries multiple selector strategies:
        1. data-audit-id attribute
        2. id attribute
        3. Raw CSS selector
        """
        target = action.get("target")

        if not target:
            return {"status": "failure", "error": "No target specified for click"}

        target_str = str(target)

        # Strategy 1: Try as data-audit-id
        selector = f'[data-audit-id="{target_str}"]'
        success = await self.helper.click_element(selector)

        if success:
            logger.info(f"Click success with data-audit-id: {target_str}")
            await asyncio.sleep(0.5)  # Wait for potential page changes
            return {"status": "success", "selector_used": selector}

        # Strategy 2: Try as id attribute
        selector = f'#{target_str}'
        success = await self.helper.click_element(selector)

        if success:
            logger.info(f"Click success with id: {target_str}")
            await asyncio.sleep(0.5)
            return {"status": "success", "selector_used": selector}

        # Strategy 3: Try as raw selector (if it looks like one)
        if any(c in target_str for c in ['.', '#', '[', '>']):
            success = await self.helper.click_element(target_str)
            if success:
                logger.info(f"Click success with raw selector: {target_str}")
                await asyncio.sleep(0.5)
                return {"status": "success", "selector_used": target_str}

        logger.warning(f"Click failed for target: {target_str}")
        return {"status": "failure", "error": f"Element not found: {target_str}"}

    async def _handle_type(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle type action (enter text into input field)
        """
        target = action.get("target")
        value = action.get("value", "")

        if not target:
            return {"status": "failure", "error": "No target specified for type"}

        if not value:
            return {"status": "failure", "error": "No value specified for type"}

        target_str = str(target)

        # Try to find the element
        selectors_to_try = [
            f'[data-audit-id="{target_str}"]',
            f'#{target_str}',
            target_str  # Raw selector
        ]

        for selector in selectors_to_try:
            try:
                element = await self.helper.page.query_selector(selector)
                if element:
                    # Clear existing content and type new value
                    await element.fill("")
                    await element.type(value, delay=50)  # Human-like typing delay
                    logger.info(f"Type success: '{value}' into {selector}")
                    await asyncio.sleep(0.3)
                    return {"status": "success", "selector_used": selector, "typed_value": value}
            except Exception as e:
                logger.debug(f"Type attempt failed for {selector}: {e}")
                continue

        return {"status": "failure", "error": f"Input element not found: {target_str}"}

    async def _handle_scroll_down(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle scroll down action
        """
        try:
            await self.helper.scroll_down(self.scroll_pixels)
            logger.info(f"Scrolled down {self.scroll_pixels}px")
            return {"status": "success", "pixels": self.scroll_pixels}
        except Exception as e:
            return {"status": "failure", "error": str(e)}

    async def _handle_scroll_up(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle scroll up action
        """
        try:
            await self.helper.scroll_up(self.scroll_pixels)
            logger.info(f"Scrolled up {self.scroll_pixels}px")
            return {"status": "success", "pixels": self.scroll_pixels}
        except Exception as e:
            return {"status": "failure", "error": str(e)}

    async def _handle_wait(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle wait action
        """
        wait_time = action.get("value", self.default_wait_time)
        try:
            wait_time = float(wait_time)
        except (TypeError, ValueError):
            wait_time = self.default_wait_time

        # Cap wait time at 5 seconds
        wait_time = min(wait_time, 5.0)

        await asyncio.sleep(wait_time)
        logger.info(f"Waited {wait_time}s")
        return {"status": "success", "waited_seconds": wait_time}

    async def _handle_navigate(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle navigate action (go to specific URL)
        """
        url = action.get("value")

        if not url:
            return {"status": "failure", "error": "No URL specified for navigate"}

        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            success = await self.helper.navigate(url)
            if success:
                logger.info(f"Navigation success to: {url}")
                return {"status": "success", "url": url}
            else:
                return {"status": "failure", "error": f"Navigation failed to: {url}"}
        except Exception as e:
            return {"status": "failure", "error": str(e)}

    async def _handle_back(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle back action (browser back button)
        """
        try:
            await self.helper.page.go_back(wait_until="networkidle", timeout=10000)
            logger.info("Navigated back")
            await asyncio.sleep(0.5)
            return {"status": "success"}
        except Exception as e:
            logger.warning(f"Back navigation failed: {e}")
            return {"status": "failure", "error": str(e)}

    async def _handle_task_complete(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle task_complete action (signal that task is done)

        This is a signal action - no actual browser interaction
        """
        reasoning = action.get("reasoning", "Task completed")
        logger.info(f"Task complete signal: {reasoning}")
        return {"status": "success", "task_completed": True, "reasoning": reasoning}


async def demo_action_executor():
    """Demo usage of ActionExecutor"""
    async with PlaywrightHelper(headless=False) as helper:
        executor = ActionExecutor(helper)

        # Navigate to example
        await helper.navigate("https://example.com")

        # Test scroll
        print("Testing scroll_down...")
        result = await executor.execute({"action_type": "scroll_down"})
        print(f"Result: {result}")

        # Test wait
        print("Testing wait...")
        result = await executor.execute({"action_type": "wait", "value": 1})
        print(f"Result: {result}")

        # Test scroll up
        print("Testing scroll_up...")
        result = await executor.execute({"action_type": "scroll_up"})
        print(f"Result: {result}")

        print("\nAll tests completed!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo_action_executor())
