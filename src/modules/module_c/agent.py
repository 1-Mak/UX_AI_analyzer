"""
Module C - Accessibility Auditor (Code Auditor)
Main orchestration class for WCAG accessibility scanning
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from playwright.async_api import async_playwright, Page, Browser

from .scanner import AccessibilityScanner
from .issue_processor import IssueProcessor
from .wcag_config import IMPACT_LEVELS, get_rule_description_ru


class ModuleC:
    """
    Module C - Accessibility Auditor

    Scans web pages for WCAG accessibility violations using axe-core.
    Supports single-page and multi-page scanning with deduplication.
    """

    def __init__(
        self,
        session_dir: Path,
        persona_key: Optional[str] = None,
        wcag_level: str = "AA"
    ):
        """
        Initialize Module C

        Args:
            session_dir: Directory to save results
            persona_key: Optional persona for prioritizing issues
            wcag_level: WCAG conformance level ("A", "AA", or "AAA")
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.persona_key = persona_key
        self.wcag_level = wcag_level.upper()

        self.scanner = AccessibilityScanner(wcag_level=self.wcag_level)
        self.processor = IssueProcessor(persona_key=persona_key)

        self._results = None

    async def scan_page(
        self,
        page: Page,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scan a single page for accessibility issues

        Args:
            page: Playwright Page object (already navigated)
            url: Optional URL override (uses page.url if not provided)

        Returns:
            Dict with issues, summary, and metadata
        """
        current_url = url or page.url
        print(f"    Сканирование: {current_url}")

        # Run axe-core scan
        scan_result = await self.scanner.scan(page)

        # Convert to AccessibilityIssue models
        issues = self.processor.process_axe_results(scan_result, current_url)

        # Generate summary
        summary = self.processor.generate_summary(issues)

        result = {
            "url": current_url,
            "timestamp": datetime.now().isoformat(),
            "wcag_level": self.wcag_level,
            "issues": [issue.model_dump() for issue in issues],
            "summary": summary,
            "pages_scanned": [current_url],
            "raw_violations_count": len(scan_result.get("violations", [])),
            "incomplete_count": len(scan_result.get("incomplete", []))
        }

        return result

    async def scan_urls(
        self,
        urls: List[str],
        headless: bool = True,
        viewport_width: int = 1920,
        viewport_height: int = 1080
    ) -> Dict[str, Any]:
        """
        Scan multiple URLs with deduplication

        Args:
            urls: List of URLs to scan
            headless: Run browser in headless mode
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height

        Returns:
            Combined result with deduplicated issues
        """
        # Remove duplicates while preserving order
        unique_urls = list(dict.fromkeys(urls))
        print(f"    Сканирование {len(unique_urls)} страниц...")

        all_issues = []
        pages_scanned = []
        errors = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={"width": viewport_width, "height": viewport_height}
            )
            page = await context.new_page()

            for i, url in enumerate(unique_urls, 1):
                try:
                    print(f"    [{i}/{len(unique_urls)}] {url}")

                    # Navigate to URL
                    await page.goto(url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(1)  # Allow dynamic content to load

                    # Scan the page
                    scan_result = await self.scanner.scan(page)

                    # Convert to issues
                    issues = self.processor.process_axe_results(scan_result, url)

                    # Collect for deduplication
                    for issue in issues:
                        all_issues.append({
                            "issue": issue,
                            "url": url
                        })

                    pages_scanned.append(url)

                except Exception as e:
                    error_msg = f"Failed to scan {url}: {str(e)}"
                    print(f"      Ошибка: {e}")
                    errors.append(error_msg)

            await browser.close()

        # Deduplicate issues across pages
        deduplicated = self.processor.deduplicate_issues(all_issues)

        # Generate multi-page summary
        summary = self.processor.generate_multi_page_summary(
            deduplicated,
            pages_scanned
        )

        result = {
            "timestamp": datetime.now().isoformat(),
            "wcag_level": self.wcag_level,
            "pages_scanned": pages_scanned,
            "issues": deduplicated,
            "summary": summary,
            "errors": errors if errors else None
        }

        # Save results
        self._save_results(result)
        self._results = result

        return result

    async def scan_from_module_b_log(
        self,
        behavioral_log_path: Path,
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Extract URLs from Module B behavioral log and scan them

        Args:
            behavioral_log_path: Path to module_b_behavioral_log.json
            headless: Run browser in headless mode

        Returns:
            Scan results for all visited pages
        """
        log_path = Path(behavioral_log_path)

        if not log_path.exists():
            raise FileNotFoundError(f"Behavioral log not found: {log_path}")

        print(f"    Загрузка лога Module B: {log_path.name}")

        with open(log_path, 'r', encoding='utf-8') as f:
            behavioral_log = json.load(f)

        # Extract unique URLs from behavioral steps
        urls = set()

        # Check different possible log formats
        # Module B saves as plain list, but could also be dict with "steps" key
        if isinstance(behavioral_log, list):
            steps = behavioral_log
        else:
            steps = behavioral_log.get("steps", behavioral_log.get("behavioral_log", []))

        for step in steps:
            url = step.get("url")
            if url:
                urls.add(url)

        # Also check for starting_url (only if dict format)
        if isinstance(behavioral_log, dict):
            starting_url = behavioral_log.get("starting_url")
            if starting_url:
                urls.add(starting_url)

        if not urls:
            raise ValueError("No URLs found in behavioral log")

        print(f"    Найдено {len(urls)} уникальных URL")

        return await self.scan_urls(list(urls), headless=headless)

    def _save_results(self, result: Dict[str, Any]):
        """
        Save scan results to JSON file

        Args:
            result: Scan results to save
        """
        output_path = self.session_dir / "module_c_accessibility_scan.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"    Результаты сохранены: {output_path.name}")

    def print_summary(self, result: Optional[Dict[str, Any]] = None):
        """
        Print human-readable summary of scan results

        Args:
            result: Scan results (uses cached results if not provided)
        """
        result = result or self._results

        if not result:
            print("  Нет результатов для отображения")
            return

        summary = result.get("summary", {})
        issues = result.get("issues", [])

        print("\n  " + "=" * 50)
        print("  ОТЧЁТ О ДОСТУПНОСТИ (WCAG " + result.get("wcag_level", "AA") + ")")
        print("  " + "=" * 50)

        # Pages scanned
        pages = result.get("pages_scanned", [])
        print(f"\n  Просканировано страниц: {len(pages)}")

        # Impact breakdown
        by_impact = summary.get("by_impact", {})
        print("\n  Проблемы по критичности:")
        for level in IMPACT_LEVELS:
            count = by_impact.get(level, 0)
            if count > 0:
                emoji = {"critical": "🔴", "serious": "🟠", "moderate": "🟡", "minor": "🟢"}.get(level, "⚪")
                print(f"    {emoji} {level.upper()}: {count}")

        # Total
        total = summary.get("total_issues", len(issues))
        print(f"\n  Всего уникальных проблем: {total}")

        if summary.get("total_occurrences"):
            print(f"  Всего вхождений: {summary['total_occurrences']}")

        # Site-wide issues (multi-page only)
        if summary.get("site_wide_issues_count"):
            print(f"  Проблем на всём сайте: {summary['site_wide_issues_count']}")

        # Top issues
        most_common = summary.get("most_common_issues", [])
        if most_common:
            print("\n  Самые частые проблемы:")
            for i, item in enumerate(most_common[:5], 1):
                rule_id = item.get("id", "unknown")
                count = item.get("count", 0)
                desc_ru = get_rule_description_ru(rule_id, rule_id)
                print(f"    {i}. {desc_ru} ({count}x)")

        # Accessibility score (single page only)
        if "accessibility_score" in summary:
            score = summary["accessibility_score"]
            print(f"\n  Оценка доступности: {score}/100")

        # Errors
        errors = result.get("errors")
        if errors:
            print(f"\n  Ошибки сканирования: {len(errors)}")

        print("\n  " + "=" * 50)

    def get_critical_issues(self) -> List[Dict[str, Any]]:
        """
        Get only critical and serious issues

        Returns:
            List of critical/serious issues
        """
        if not self._results:
            return []

        issues = self._results.get("issues", [])
        return [
            issue for issue in issues
            if issue.get("impact") in ["critical", "serious"]
        ]

    def get_issues_for_report(self) -> Dict[str, Any]:
        """
        Get issues formatted for final report (Module E)

        Returns:
            Dict with issues and summary suitable for report generation
        """
        if not self._results:
            return {"issues": [], "summary": {}}

        return {
            "issues": self._results.get("issues", []),
            "summary": self._results.get("summary", {}),
            "wcag_level": self._results.get("wcag_level", self.wcag_level),
            "pages_scanned": self._results.get("pages_scanned", [])
        }
