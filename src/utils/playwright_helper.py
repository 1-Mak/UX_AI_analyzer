"""
Playwright helper utilities for browser automation and data extraction
"""
import asyncio
import json
from pathlib import Path
from typing import Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser
from src.config import (
    SCREENSHOTS_DIR,
    DEFAULT_VIEWPORT_WIDTH,
    DEFAULT_VIEWPORT_HEIGHT,
    SCREENSHOT_TIMEOUT
)


class PlaywrightHelper:
    """Helper class for Playwright browser automation"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def initialize(self):
        """Initialize browser and page"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page(
            viewport={
                "width": DEFAULT_VIEWPORT_WIDTH,
                "height": DEFAULT_VIEWPORT_HEIGHT
            }
        )

    async def close(self):
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate(self, url: str, wait_until: str = "networkidle") -> bool:
        """
        Navigate to a URL

        Args:
            url: Target URL
            wait_until: When to consider navigation complete ('load', 'domcontentloaded', 'networkidle')

        Returns:
            True if navigation successful
        """
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=SCREENSHOT_TIMEOUT)
            return True
        except Exception as e:
            print(f"Navigation error: {e}")
            return False

    async def take_screenshot(
        self,
        filename: str,
        full_page: bool = True,
        path: Optional[Path] = None
    ) -> Path:
        """
        Take a screenshot of the current page

        Args:
            filename: Name of the screenshot file
            full_page: Whether to capture the full scrollable page
            path: Custom path to save screenshot (default: SCREENSHOTS_DIR)

        Returns:
            Path to the saved screenshot
        """
        if path is None:
            path = SCREENSHOTS_DIR

        screenshot_path = path / filename

        await self.page.screenshot(
            path=str(screenshot_path),
            full_page=full_page,
            timeout=SCREENSHOT_TIMEOUT
        )

        return screenshot_path

    async def get_dom_snapshot(self) -> str:
        """
        Get the full HTML DOM snapshot

        Returns:
            HTML content as string
        """
        return await self.page.content()

    async def get_accessibility_tree(self) -> Dict[str, Any]:
        """
        Get the accessibility tree snapshot

        Returns:
            Accessibility tree as dictionary
        """
        try:
            snapshot = await self.page.accessibility.snapshot()
            return snapshot if snapshot else {}
        except Exception as e:
            print(f"Error getting accessibility tree: {e}")
            return {}

    async def get_simplified_dom(self) -> str:
        """
        Get simplified DOM by removing non-interactive elements

        Returns:
            Simplified HTML string with only interactive elements
        """
        # JavaScript to extract only interactive elements with IDs
        js_code = """
        () => {
            let counter = 1;
            const interactiveTags = ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'LABEL'];
            const elements = Array.from(document.querySelectorAll('body *'));

            let result = '';

            elements.forEach(el => {
                if (interactiveTags.includes(el.tagName)) {
                    if (!el.id) {
                        el.setAttribute('data-audit-id', counter++);
                    }

                    const id = el.id || el.getAttribute('data-audit-id');
                    const tag = el.tagName.toLowerCase();
                    const text = el.innerText?.substring(0, 50) || '';
                    const type = el.getAttribute('type') || '';
                    const ariaLabel = el.getAttribute('aria-label') || '';

                    result += `<${tag} id="${id}" text="${text}" type="${type}" aria-label="${ariaLabel}"/>\\n`;
                }
            });

            return result;
        }
        """

        try:
            simplified = await self.page.evaluate(js_code)
            return simplified
        except Exception as e:
            print(f"Error getting simplified DOM: {e}")
            return ""

    async def scroll_down(self, pixels: int = 500):
        """Scroll down by specified pixels"""
        await self.page.mouse.wheel(0, pixels)
        await asyncio.sleep(0.5)  # Wait for content to load

    async def scroll_up(self, pixels: int = 500):
        """Scroll up by specified pixels"""
        await self.page.mouse.wheel(0, -pixels)
        await asyncio.sleep(0.5)

    async def click_element(self, selector: str) -> bool:
        """
        Click an element by selector

        Args:
            selector: CSS selector or data-audit-id

        Returns:
            True if click successful
        """
        try:
            # Try as CSS selector first
            if await self.page.query_selector(selector):
                await self.page.click(selector)
                return True

            # Try as data-audit-id
            element = await self.page.query_selector(f'[data-audit-id="{selector}"]')
            if element:
                await element.click()
                return True

            return False
        except Exception as e:
            print(f"Click error: {e}")
            return False

    async def get_page_info(self) -> Dict[str, Any]:
        """
        Get comprehensive page information

        Returns:
            Dictionary with page title, URL, and viewport
        """
        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "viewport": self.page.viewport_size
        }


async def demo_usage():
    """Demo usage of PlaywrightHelper"""
    async with PlaywrightHelper(headless=False) as helper:
        # Navigate to a page
        print("Navigating to example.com...")
        await helper.navigate("https://example.com")

        # Take screenshot
        print("Taking screenshot...")
        screenshot_path = await helper.take_screenshot("demo_screenshot.png")
        print(f"Screenshot saved to: {screenshot_path}")

        # Get DOM
        print("Getting DOM snapshot...")
        dom = await helper.get_dom_snapshot()
        print(f"DOM length: {len(dom)} characters")

        # Get accessibility tree
        print("Getting accessibility tree...")
        a11y_tree = await helper.get_accessibility_tree()
        print(f"Accessibility tree: {json.dumps(a11y_tree, indent=2)[:200]}...")

        # Get simplified DOM
        print("Getting simplified DOM...")
        simplified = await helper.get_simplified_dom()
        print(f"Simplified DOM:\n{simplified[:500]}")


if __name__ == "__main__":
    asyncio.run(demo_usage())
