"""
Module E - Report Synthesizer Agent
Main entry point for report generation
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

from .generator import ReportGenerator
from .html_template import HTMLReportGenerator


class ModuleE:
    """
    Module E: Report Synthesizer

    Combines results from all modules (A-D) into a comprehensive
    UX audit report with executive summary, issues list, and recommendations.
    """

    def __init__(self, session_dir: Path):
        """
        Initialize Module E

        Args:
            session_dir: Directory containing module outputs and audit_results.json
        """
        self.session_dir = Path(session_dir)
        self.audit_results = {}
        self.report_data = {}

    def load_audit_results(self, results_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load audit results from JSON file

        Args:
            results_path: Path to audit_results.json (default: session_dir/audit_results.json)

        Returns:
            Loaded audit results
        """
        if results_path is None:
            results_path = self.session_dir / "audit_results.json"

        if not results_path.exists():
            raise FileNotFoundError(f"Audit results not found: {results_path}")

        with open(results_path, "r", encoding="utf-8") as f:
            self.audit_results = json.load(f)

        return self.audit_results

    def generate_report(self, audit_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive report from audit results

        Args:
            audit_results: Optional audit results dict. If not provided,
                           loads from audit_results.json

        Returns:
            Complete report data
        """
        if audit_results:
            self.audit_results = audit_results
        elif not self.audit_results:
            self.load_audit_results()

        # Generate report
        generator = ReportGenerator(self.session_dir, self.audit_results)
        self.report_data = generator.generate_report()

        # Save JSON report
        json_path = generator.save_json_report()
        print(f"    JSON report saved: {json_path.name}")

        return self.report_data

    def generate_html_report(self, output_filename: str = "ux_audit_report.html") -> Path:
        """
        Generate HTML report

        Args:
            output_filename: Output filename for HTML report

        Returns:
            Path to generated HTML file
        """
        if not self.report_data:
            self.generate_report()

        html_generator = HTMLReportGenerator(self.report_data)
        output_path = self.session_dir / output_filename
        html_generator.save_html(output_path)

        print(f"    HTML report saved: {output_path.name}")

        return output_path

    def print_summary(self, report: Optional[Dict[str, Any]] = None):
        """Print report summary to console"""
        if report is None:
            report = self.report_data

        if not report:
            print("  No report data available")
            return

        print("\n  " + "-" * 50)
        print("  MODULE E: FINAL REPORT SUMMARY")
        print("  " + "-" * 50)

        # Overall score
        score = report.get("overall_score", {})
        overall = score.get("overall", 0)
        rating = score.get("rating_label", "N/A")
        print(f"\n    Overall Score: {int(overall * 100)}% ({rating})")

        # Breakdown
        breakdown = score.get("breakdown", {})
        if breakdown:
            print("\n    Score Breakdown:")
            labels = {
                "visual": "Visual (A)",
                "behavioral": "Behavioral (B)",
                "accessibility": "Accessibility (C)",
                "sentiment": "Sentiment (D)"
            }
            for key, val in breakdown.items():
                print(f"      {labels.get(key, key)}: {int(val * 100)}%")

        # Executive summary
        summary = report.get("executive_summary", {})
        critical = summary.get("critical_findings", [])
        if critical:
            print("\n    Critical Findings:")
            for finding in critical:
                print(f"      [!] {finding}")

        # Issues count
        issues = report.get("all_issues", [])
        if issues:
            print(f"\n    Total Issues Found: {len(issues)}")

            # Count by severity
            severity_counts = {}
            for issue in issues:
                sev = issue.get("severity", "unknown")
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

            for sev in ["critical", "high", "serious", "medium", "moderate", "low", "minor"]:
                if sev in severity_counts:
                    print(f"      {sev}: {severity_counts[sev]}")

        # Recommendations
        recs = report.get("recommendations", [])
        if recs:
            print(f"\n    Recommendations: {len(recs)}")
            for rec in recs[:3]:  # Show top 3
                priority = rec.get("priority", "").upper()
                text = rec.get("text", "")[:60]
                print(f"      [{priority}] {text}...")

        print("\n  " + "-" * 50)


async def demo_module_e():
    """Demo function to test Module E"""
    from pathlib import Path

    # Find a session with audit results
    screenshots_dir = Path("screenshots")

    if not screenshots_dir.exists():
        print("No screenshots directory found")
        return

    # Find latest session with audit results
    audit_files = list(screenshots_dir.glob("*/audit_results.json"))

    if not audit_files:
        print("No audit_results.json found in any session")
        return

    latest_audit = max(audit_files, key=lambda p: p.stat().st_mtime)
    session_dir = latest_audit.parent

    print(f"Testing Module E with: {session_dir}")

    # Run report generation
    module_e = ModuleE(session_dir=session_dir)
    report = module_e.generate_report()
    html_path = module_e.generate_html_report()

    module_e.print_summary(report)

    print(f"\n  HTML Report: {html_path}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_module_e())
