"""
Module E - HTML Report Template
Generates HTML reports from report data
"""
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from .report_config import RATING_THRESHOLDS, ISSUE_ICONS


class HTMLReportGenerator:
    """Generates HTML reports from report data"""

    def __init__(self, report_data: Dict[str, Any]):
        """
        Initialize HTML generator

        Args:
            report_data: Report data from ReportGenerator
        """
        self.data = report_data

    def generate_html(self) -> str:
        """Generate complete HTML report"""
        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UX Audit Report - {self.data.get('metadata', {}).get('session_id', 'Report')}</title>
    <style>
{self._get_styles()}
    </style>
</head>
<body>
    <div class="container">
        {self._render_header()}
        {self._render_overall_score()}
        {self._render_executive_summary()}
        {self._render_module_summaries()}
        {self._render_issues()}
        {self._render_recommendations()}
        {self._render_footer()}
    </div>
</body>
</html>"""

    def _get_styles(self) -> str:
        """Get CSS styles"""
        return """
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: system-ui, -apple-system, sans-serif;
            line-height: 1.6;
            color: #1f2937;
            background: #f3f4f6;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .header h1 { font-size: 2em; margin-bottom: 10px; }
        .header .meta { opacity: 0.9; font-size: 0.95em; }

        .score-card {
            text-align: center;
            padding: 30px;
        }
        .score-circle {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 3em;
            font-weight: bold;
            color: white;
            margin-bottom: 15px;
        }
        .score-label { font-size: 1.5em; font-weight: 600; }
        .score-breakdown {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .score-item {
            text-align: center;
        }
        .score-item .value { font-size: 1.5em; font-weight: 600; }
        .score-item .label { color: #6b7280; font-size: 0.9em; }

        h2 {
            font-size: 1.4em;
            margin-bottom: 16px;
            color: #111827;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 8px;
        }

        .summary-points { list-style: none; }
        .summary-points li {
            padding: 8px 0;
            padding-left: 24px;
            position: relative;
        }
        .summary-points li::before {
            content: ">";
            position: absolute;
            left: 0;
            color: #3b82f6;
            font-weight: bold;
        }

        .critical-findings {
            background: #fef2f2;
            border-left: 4px solid #ef4444;
            padding: 16px;
            margin-top: 16px;
            border-radius: 0 8px 8px 0;
        }
        .critical-findings h3 {
            color: #dc2626;
            margin-bottom: 8px;
        }

        .module-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
        }
        .module-card {
            background: #f9fafb;
            border-radius: 8px;
            padding: 16px;
            border: 1px solid #e5e7eb;
        }
        .module-card h3 {
            font-size: 1em;
            margin-bottom: 12px;
            color: #374151;
        }
        .module-stat {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            font-size: 0.9em;
        }
        .module-stat .label { color: #6b7280; }
        .module-stat .value { font-weight: 600; }

        .issues-list { list-style: none; }
        .issue-item {
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 6px;
            border-left: 4px solid;
        }
        .issue-item.critical { background: #fef2f2; border-color: #ef4444; }
        .issue-item.high, .issue-item.serious { background: #fff7ed; border-color: #f97316; }
        .issue-item.medium, .issue-item.moderate { background: #fefce8; border-color: #eab308; }
        .issue-item.low, .issue-item.minor { background: #f0fdf4; border-color: #22c55e; }
        .issue-source {
            font-size: 0.8em;
            color: #6b7280;
            margin-bottom: 4px;
        }
        .issue-text { font-size: 0.95em; }

        .recommendations-list { list-style: none; }
        .rec-item {
            padding: 16px;
            margin-bottom: 12px;
            background: #eff6ff;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }
        .rec-item.critical { background: #fef2f2; border-color: #ef4444; }
        .rec-item.high { background: #fff7ed; border-color: #f97316; }
        .rec-category {
            font-size: 0.8em;
            color: #3b82f6;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 4px;
        }

        .footer {
            text-align: center;
            padding: 20px;
            color: #6b7280;
            font-size: 0.9em;
        }

        @media print {
            body { background: white; }
            .container { max-width: none; padding: 0; }
            .card { box-shadow: none; border: 1px solid #e5e7eb; }
        }
        """

    def _render_header(self) -> str:
        """Render report header"""
        meta = self.data.get("metadata", {})
        persona = meta.get("persona", {})

        return f"""
        <div class="header">
            <h1>UX Audit Report</h1>
            <div class="meta">
                <div>URL: {meta.get('url', 'N/A')}</div>
                <div>Задача: {meta.get('task', 'N/A')}</div>
                <div>Персона: {persona.get('name', 'N/A')} - {persona.get('description', '')}</div>
                <div>Session: {meta.get('session_id', 'N/A')}</div>
            </div>
        </div>
        """

    def _render_overall_score(self) -> str:
        """Render overall score section"""
        score = self.data.get("overall_score", {})
        overall = score.get("overall", 0)
        color = score.get("rating_color", "#6b7280")
        label = score.get("rating_label", "N/A")
        breakdown = score.get("breakdown", {})

        breakdown_html = ""
        labels = {
            "visual": "Визуал",
            "behavioral": "Поведение",
            "accessibility": "Доступность",
            "sentiment": "Эмоции"
        }
        for key, val in breakdown.items():
            breakdown_html += f"""
            <div class="score-item">
                <div class="value">{int(val * 100)}%</div>
                <div class="label">{labels.get(key, key)}</div>
            </div>
            """

        return f"""
        <div class="card score-card">
            <div class="score-circle" style="background-color: {color};">
                {int(overall * 100)}
            </div>
            <div class="score-label">{label}</div>
            <div class="score-breakdown">
                {breakdown_html}
            </div>
        </div>
        """

    def _render_executive_summary(self) -> str:
        """Render executive summary"""
        summary = self.data.get("executive_summary", {})
        points = summary.get("summary_points", [])
        critical = summary.get("critical_findings", [])

        points_html = "".join(f"<li>{p}</li>" for p in points)

        critical_html = ""
        if critical:
            critical_items = "".join(f"<li>{c}</li>" for c in critical)
            critical_html = f"""
            <div class="critical-findings">
                <h3>Критические находки</h3>
                <ul class="summary-points">{critical_items}</ul>
            </div>
            """

        return f"""
        <div class="card">
            <h2>Краткое резюме</h2>
            <ul class="summary-points">
                {points_html}
            </ul>
            {critical_html}
        </div>
        """

    def _render_module_summaries(self) -> str:
        """Render module summaries"""
        summaries = self.data.get("module_summaries", {})

        cards_html = ""

        # Module A
        if "module_a" in summaries:
            m = summaries["module_a"]
            severity = m.get("severity", {})
            cards_html += f"""
            <div class="module-card">
                <h3>{m.get('title', 'Module A')}</h3>
                <div class="module-stat">
                    <span class="label">Всего проблем:</span>
                    <span class="value">{m.get('total_issues', 0)}</span>
                </div>
                <div class="module-stat">
                    <span class="label">Критичные:</span>
                    <span class="value">{severity.get('critical', 0)}</span>
                </div>
                <div class="module-stat">
                    <span class="label">Высокие:</span>
                    <span class="value">{severity.get('high', 0)}</span>
                </div>
            </div>
            """

        # Module B
        if "module_b" in summaries:
            m = summaries["module_b"]
            status_labels = {
                "completed": "Выполнена",
                "failed": "Не выполнена",
                "max_steps_reached": "Прервана",
                "partial": "Частично"
            }
            cards_html += f"""
            <div class="module-card">
                <h3>{m.get('title', 'Module B')}</h3>
                <div class="module-stat">
                    <span class="label">Шагов:</span>
                    <span class="value">{m.get('total_steps', 0)}</span>
                </div>
                <div class="module-stat">
                    <span class="label">Статус задачи:</span>
                    <span class="value">{status_labels.get(m.get('task_status'), m.get('task_status', 'N/A'))}</span>
                </div>
            </div>
            """

        # Module C
        if "module_c" in summaries:
            m = summaries["module_c"]
            impact = m.get("by_impact", {})
            cards_html += f"""
            <div class="module-card">
                <h3>{m.get('title', 'Module C')}</h3>
                <div class="module-stat">
                    <span class="label">Всего проблем:</span>
                    <span class="value">{m.get('total_issues', 0)}</span>
                </div>
                <div class="module-stat">
                    <span class="label">Критичные:</span>
                    <span class="value">{impact.get('critical', 0)}</span>
                </div>
                <div class="module-stat">
                    <span class="label">Серьезные:</span>
                    <span class="value">{impact.get('serious', 0)}</span>
                </div>
                <div class="module-stat">
                    <span class="label">WCAG уровень:</span>
                    <span class="value">{m.get('wcag_level', 'AA')}</span>
                </div>
            </div>
            """

        # Module D
        if "module_d" in summaries:
            m = summaries["module_d"]
            trend_labels = {"improving": "Улучшение", "stable": "Стабильно", "declining": "Ухудшение"}
            score = m.get("session_score", 0)
            cards_html += f"""
            <div class="module-card">
                <h3>{m.get('title', 'Module D')}</h3>
                <div class="module-stat">
                    <span class="label">Оценка сессии:</span>
                    <span class="value">{score:+.2f}</span>
                </div>
                <div class="module-stat">
                    <span class="label">Тренд:</span>
                    <span class="value">{trend_labels.get(m.get('trend'), m.get('trend', 'N/A'))}</span>
                </div>
                <div class="module-stat">
                    <span class="label">Болевые точки:</span>
                    <span class="value">{m.get('pain_points_count', 0)}</span>
                </div>
            </div>
            """

        return f"""
        <div class="card">
            <h2>Результаты по модулям</h2>
            <div class="module-grid">
                {cards_html}
            </div>
        </div>
        """

    def _render_issues(self) -> str:
        """Render all issues"""
        issues = self.data.get("all_issues", [])[:20]  # Limit to top 20

        if not issues:
            return ""

        issues_html = ""
        for issue in issues:
            severity = issue.get("severity", "medium").lower()
            source = issue.get("source", "Unknown")
            desc = issue.get("description", "")

            issues_html += f"""
            <li class="issue-item {severity}">
                <div class="issue-source">{source} | {severity.upper()}</div>
                <div class="issue-text">{desc}</div>
            </li>
            """

        return f"""
        <div class="card">
            <h2>Выявленные проблемы (топ-20)</h2>
            <ul class="issues-list">
                {issues_html}
            </ul>
        </div>
        """

    def _render_recommendations(self) -> str:
        """Render recommendations"""
        recs = self.data.get("recommendations", [])

        if not recs:
            return ""

        recs_html = ""
        for rec in recs:
            priority = rec.get("priority", "medium")
            category = rec.get("category", "")
            text = rec.get("text", "")

            recs_html += f"""
            <li class="rec-item {priority}">
                <div class="rec-category">{category}</div>
                <div>{text}</div>
            </li>
            """

        return f"""
        <div class="card">
            <h2>Рекомендации</h2>
            <ul class="recommendations-list">
                {recs_html}
            </ul>
        </div>
        """

    def _render_footer(self) -> str:
        """Render footer"""
        generated = self.data.get("generated_at", datetime.now().isoformat())

        return f"""
        <div class="footer">
            <p>Generated by UX AI Audit System</p>
            <p>{generated}</p>
        </div>
        """

    def save_html(self, output_path: Path) -> Path:
        """Save HTML report to file"""
        html = self.generate_html()
        output_path = Path(output_path)
        output_path.write_text(html, encoding="utf-8")
        return output_path
