"""
Accessibility Scanner - Wrapper over axe-playwright-python
Handles running axe-core accessibility tests on Playwright pages
"""
import asyncio
from typing import Dict, List, Optional, Any
from playwright.async_api import Page

from .wcag_config import get_wcag_tags, IMPACT_LEVELS


class AccessibilityScanner:
    """
    Wrapper over axe-playwright-python for running accessibility scans
    """

    def __init__(self, wcag_level: str = "AA"):
        """
        Initialize the scanner

        Args:
            wcag_level: WCAG conformance level ("A", "AA", or "AAA")
        """
        self.wcag_level = wcag_level.upper()
        self.wcag_tags = get_wcag_tags(self.wcag_level)
        self._axe = None

    def _get_axe_options(self) -> Dict[str, Any]:
        """
        Build options dictionary for axe.run()

        Returns:
            Options dict for axe-core
        """
        return {
            "resultTypes": ["violations", "incomplete"],
            "runOnly": {
                "type": "tag",
                "values": self.wcag_tags
            }
        }

    async def _ensure_axe(self):
        """Lazy load axe instance"""
        if self._axe is None:
            try:
                from axe_playwright_python.async_playwright import Axe
                self._axe = Axe()
            except ImportError:
                raise ImportError(
                    "axe-playwright-python is required. "
                    "Install with: pip install axe-playwright-python"
                )

    async def scan(
        self,
        page: Page,
        context: Optional[str] = None,
        include_incomplete: bool = True
    ) -> Dict[str, Any]:
        """
        Run accessibility scan on a page

        Args:
            page: Playwright Page object
            context: Optional CSS selector to limit scan scope
            include_incomplete: Whether to include incomplete (needs review) issues

        Returns:
            Dict with 'violations', 'incomplete', 'url', 'timestamp' keys
        """
        await self._ensure_axe()

        options = self._get_axe_options()

        try:
            # Run axe-core scan
            axe_results = await self._axe.run(
                page,
                context=context,
                options=options
            )

            # axe-playwright-python returns AxeResults object with .response attribute
            if hasattr(axe_results, 'response'):
                results = axe_results.response
            else:
                results = axe_results if isinstance(axe_results, dict) else {}

            # Extract relevant data
            scan_result = {
                "url": page.url,
                "timestamp": results.get("timestamp", ""),
                "violations": results.get("violations", []),
                "incomplete": results.get("incomplete", []) if include_incomplete else [],
                "passes_count": len(results.get("passes", [])),
                "inapplicable_count": len(results.get("inapplicable", [])),
                "wcag_level": self.wcag_level
            }

            return scan_result

        except Exception as e:
            return {
                "url": page.url,
                "error": str(e),
                "violations": [],
                "incomplete": [],
                "wcag_level": self.wcag_level
            }

    async def scan_multiple_contexts(
        self,
        page: Page,
        contexts: List[str]
    ) -> Dict[str, Any]:
        """
        Scan multiple regions of a page (e.g., header, main, footer)

        Args:
            page: Playwright Page object
            contexts: List of CSS selectors for regions to scan

        Returns:
            Combined results from all contexts
        """
        all_violations = []
        all_incomplete = []
        seen_violation_ids = set()

        for context in contexts:
            try:
                result = await self.scan(page, context=context)

                # Deduplicate violations
                for violation in result.get("violations", []):
                    violation_key = f"{violation['id']}_{context}"
                    if violation_key not in seen_violation_ids:
                        seen_violation_ids.add(violation_key)
                        violation["context"] = context
                        all_violations.append(violation)

                for incomplete in result.get("incomplete", []):
                    incomplete["context"] = context
                    all_incomplete.append(incomplete)

            except Exception as e:
                print(f"  Warning: Failed to scan context '{context}': {e}")

        return {
            "url": page.url,
            "violations": all_violations,
            "incomplete": all_incomplete,
            "contexts_scanned": contexts,
            "wcag_level": self.wcag_level
        }

    async def quick_scan(self, page: Page) -> Dict[str, int]:
        """
        Perform a quick scan and return only issue counts by impact

        Args:
            page: Playwright Page object

        Returns:
            Dict with impact levels as keys and counts as values
        """
        result = await self.scan(page, include_incomplete=False)

        counts = {level: 0 for level in IMPACT_LEVELS}

        for violation in result.get("violations", []):
            impact = violation.get("impact", "minor")
            if impact in counts:
                counts[impact] += len(violation.get("nodes", []))

        return counts

    def get_scan_summary(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of scan results

        Args:
            scan_result: Result from scan() method

        Returns:
            Summary dict with counts and statistics
        """
        violations = scan_result.get("violations", [])

        # Count by impact
        by_impact = {level: 0 for level in IMPACT_LEVELS}
        total_nodes = 0

        for violation in violations:
            impact = violation.get("impact", "minor")
            nodes_count = len(violation.get("nodes", []))
            if impact in by_impact:
                by_impact[impact] += 1
            total_nodes += nodes_count

        # Most common violations
        violation_counts = {}
        for v in violations:
            rule_id = v.get("id", "unknown")
            violation_counts[rule_id] = violation_counts.get(rule_id, 0) + 1

        most_common = sorted(
            violation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            "total_violations": len(violations),
            "total_affected_nodes": total_nodes,
            "by_impact": by_impact,
            "most_common": [{"id": k, "count": v} for k, v in most_common],
            "incomplete_count": len(scan_result.get("incomplete", [])),
            "wcag_level": scan_result.get("wcag_level", self.wcag_level)
        }
