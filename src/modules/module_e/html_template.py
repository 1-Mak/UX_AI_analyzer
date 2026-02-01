"""
Module E - HTML Report Template
Generates detailed HTML reports from report data
"""
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from .report_config import RATING_THRESHOLDS, ISSUE_ICONS


class HTMLReportGenerator:
    """Generates comprehensive HTML reports from report data"""

    def __init__(self, report_data: Dict[str, Any]):
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
        {self._render_detailed_findings()}
        {self._render_module_details()}
        {self._render_all_issues_detailed()}
        {self._render_recommendations_detailed()}
        {self._render_footer()}
    </div>
</body>
</html>"""

    def _get_styles(self) -> str:
        """Get CSS styles"""
        return """
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
            line-height: 1.7;
            color: #1f2937;
            background: #f3f4f6;
            font-size: 15px;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 24px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 28px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.05);
        }

        /* Header */
        .header {
            text-align: center;
            padding: 48px 24px;
            background: linear-gradient(135deg, #1e40af, #3b82f6);
            color: white;
            border-radius: 12px;
            margin-bottom: 24px;
        }
        .header h1 { font-size: 2.2em; margin-bottom: 16px; font-weight: 700; }
        .header .meta { opacity: 0.95; font-size: 1em; }
        .header .meta div { margin: 6px 0; }
        .header .task-box {
            background: rgba(255,255,255,0.15);
            padding: 12px 20px;
            border-radius: 8px;
            margin-top: 16px;
            display: inline-block;
        }

        /* Score Section */
        .score-card { text-align: center; padding: 36px; }
        .score-circle {
            width: 160px;
            height: 160px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 3.2em;
            font-weight: bold;
            color: white;
            margin-bottom: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        .score-label { font-size: 1.6em; font-weight: 600; margin-bottom: 8px; }
        .score-description { color: #6b7280; max-width: 600px; margin: 0 auto 24px; }
        .score-breakdown {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 24px;
            flex-wrap: wrap;
        }
        .score-item { text-align: center; }
        .score-item .value { font-size: 1.8em; font-weight: 700; }
        .score-item .label { color: #6b7280; font-size: 0.9em; margin-top: 4px; }
        .score-item .bar {
            width: 80px;
            height: 6px;
            background: #e5e7eb;
            border-radius: 3px;
            margin-top: 8px;
            overflow: hidden;
        }
        .score-item .bar-fill { height: 100%; border-radius: 3px; }

        /* Typography */
        h2 {
            font-size: 1.5em;
            margin-bottom: 20px;
            color: #111827;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 10px;
            font-weight: 600;
        }
        h3 {
            font-size: 1.2em;
            margin: 20px 0 12px;
            color: #374151;
            font-weight: 600;
        }
        h4 {
            font-size: 1em;
            margin: 16px 0 8px;
            color: #4b5563;
            font-weight: 600;
        }

        /* Summary Points */
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .summary-box {
            background: #f9fafb;
            border-radius: 8px;
            padding: 20px;
            border: 1px solid #e5e7eb;
        }
        .summary-box.negative { background: #fef2f2; border-color: #fecaca; }
        .summary-box.positive { background: #f0fdf4; border-color: #bbf7d0; }
        .summary-box.warning { background: #fffbeb; border-color: #fde68a; }
        .summary-box h4 { margin-top: 0; }
        .summary-box ul { margin-left: 20px; }
        .summary-box li { margin: 8px 0; }

        /* Critical Findings */
        .critical-section {
            background: linear-gradient(135deg, #fef2f2, #fee2e2);
            border: 2px solid #ef4444;
            border-radius: 12px;
            padding: 24px;
            margin: 24px 0;
        }
        .critical-section h3 {
            color: #dc2626;
            margin-top: 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .critical-section h3::before { content: "!!!"; font-weight: bold; }
        .critical-item {
            background: white;
            border-radius: 8px;
            padding: 16px;
            margin: 12px 0;
            border-left: 4px solid #ef4444;
        }
        .critical-item .title { font-weight: 600; color: #991b1b; }
        .critical-item .detail { margin-top: 8px; color: #4b5563; }

        /* Module Cards */
        .module-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }
        @media (max-width: 768px) {
            .module-grid { grid-template-columns: 1fr; }
        }
        .module-card {
            background: #f9fafb;
            border-radius: 10px;
            padding: 20px;
            border: 1px solid #e5e7eb;
        }
        .module-card h3 {
            font-size: 1.1em;
            margin: 0 0 16px;
            color: #1f2937;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .module-card .icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2em;
        }
        .module-card .stats { margin-bottom: 12px; }
        .module-card .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #e5e7eb;
        }
        .module-card .stat-row:last-child { border-bottom: none; }
        .module-card .stat-label { color: #6b7280; }
        .module-card .stat-value { font-weight: 600; }
        .module-card .description {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid #e5e7eb;
            color: #4b5563;
            font-size: 0.9em;
        }

        /* Issues List */
        .issues-section { margin-top: 16px; }
        .issue-group { margin-bottom: 24px; }
        .issue-group-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }
        .issue-group-header .badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .issue-group-header .badge.critical { background: #fee2e2; color: #991b1b; }
        .issue-group-header .badge.high, .issue-group-header .badge.serious { background: #ffedd5; color: #9a3412; }
        .issue-group-header .badge.medium, .issue-group-header .badge.moderate { background: #fef3c7; color: #92400e; }
        .issue-group-header .badge.low, .issue-group-header .badge.minor { background: #dcfce7; color: #166534; }

        .issue-item {
            background: white;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            border: 1px solid #e5e7eb;
            border-left: 4px solid;
        }
        .issue-item.critical { border-left-color: #ef4444; }
        .issue-item.high, .issue-item.serious { border-left-color: #f97316; }
        .issue-item.medium, .issue-item.moderate { border-left-color: #eab308; }
        .issue-item.low, .issue-item.minor { border-left-color: #22c55e; }

        .issue-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }
        .issue-title { font-weight: 600; color: #1f2937; }
        .issue-source {
            font-size: 0.8em;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            background: #6b7280;
        }
        .issue-description { color: #4b5563; margin-bottom: 12px; }
        .issue-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            font-size: 0.85em;
            color: #6b7280;
        }
        .issue-meta span {
            background: #f3f4f6;
            padding: 4px 10px;
            border-radius: 4px;
        }

        /* Recommendations */
        .rec-item {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 16px;
            border: 1px solid #e5e7eb;
            border-left: 5px solid #3b82f6;
        }
        .rec-item.critical { border-left-color: #ef4444; background: #fef2f2; }
        .rec-item.high { border-left-color: #f97316; background: #fff7ed; }
        .rec-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .rec-priority {
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
            padding: 4px 10px;
            border-radius: 4px;
        }
        .rec-priority.critical { background: #fee2e2; color: #991b1b; }
        .rec-priority.high { background: #ffedd5; color: #9a3412; }
        .rec-priority.medium { background: #e0e7ff; color: #3730a3; }
        .rec-category {
            font-size: 0.85em;
            color: #6b7280;
        }
        .rec-title { font-weight: 600; font-size: 1.1em; margin-bottom: 8px; }
        .rec-rationale {
            color: #4b5563;
            padding: 12px;
            background: #f9fafb;
            border-radius: 6px;
            margin-top: 12px;
            font-size: 0.9em;
        }
        .rec-rationale strong { color: #374151; }

        /* Insights */
        .insights-list { margin-top: 16px; }
        .insight-item {
            padding: 12px 16px;
            background: #eff6ff;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 3px solid #3b82f6;
        }

        /* Timeline */
        .timeline { margin: 16px 0; }
        .timeline-item {
            display: flex;
            gap: 16px;
            padding: 12px 0;
            border-bottom: 1px solid #e5e7eb;
        }
        .timeline-item:last-child { border-bottom: none; }
        .timeline-step {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 0.9em;
            flex-shrink: 0;
        }
        .timeline-step.success { background: #dcfce7; color: #166534; }
        .timeline-step.failure { background: #fee2e2; color: #991b1b; }
        .timeline-content { flex: 1; }
        .timeline-action { font-weight: 500; }
        .timeline-detail { color: #6b7280; font-size: 0.9em; margin-top: 4px; }

        /* Footer */
        .footer {
            text-align: center;
            padding: 24px;
            color: #6b7280;
            font-size: 0.9em;
        }

        /* Print */
        @media print {
            body { background: white; font-size: 12px; }
            .container { max-width: none; padding: 0; }
            .card { box-shadow: none; border: 1px solid #e5e7eb; page-break-inside: avoid; }
            .header { padding: 24px; }
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
                <div><strong>URL:</strong> {meta.get('url', 'N/A')}</div>
                <div><strong>Персона:</strong> {persona.get('name', 'N/A')} - {persona.get('description', '')}</div>
                <div class="task-box">
                    <strong>Задача:</strong> {meta.get('task', 'N/A')}
                </div>
                <div style="margin-top: 12px; font-size: 0.9em; opacity: 0.8;">
                    Session ID: {meta.get('session_id', 'N/A')}
                </div>
            </div>
        </div>
        """

    def _render_overall_score(self) -> str:
        """Render overall score section with explanation"""
        score = self.data.get("overall_score", {})
        overall = score.get("overall", 0)
        color = score.get("rating_color", "#6b7280")
        label = score.get("rating_label", "N/A")
        breakdown = score.get("breakdown", {})

        # Score description based on rating
        descriptions = {
            "excellent": "Интерфейс демонстрирует отличное качество UX. Минимальные проблемы, высокая доступность.",
            "good": "Хороший уровень UX с некоторыми областями для улучшения. Основной функционал работает корректно.",
            "fair": "Удовлетворительный UX, но есть заметные проблемы, влияющие на пользовательский опыт.",
            "poor": "Серьёзные проблемы с UX, требующие немедленного внимания. Пользователи испытывают затруднения.",
            "critical": "Критические проблемы юзабилити и доступности. Интерфейс требует существенной переработки."
        }
        desc = descriptions.get(score.get("rating", "fair"), "")

        breakdown_html = ""
        labels = {
            "visual": ("Визуал", "#8b5cf6"),
            "behavioral": ("Поведение", "#3b82f6"),
            "accessibility": ("Доступность", "#10b981"),
            "sentiment": ("Эмоции", "#f59e0b")
        }
        for key, val in breakdown.items():
            label_name, bar_color = labels.get(key, (key, "#6b7280"))
            pct = int(val * 100)
            breakdown_html += f"""
            <div class="score-item">
                <div class="value" style="color: {bar_color};">{pct}%</div>
                <div class="label">{label_name}</div>
                <div class="bar">
                    <div class="bar-fill" style="width: {pct}%; background: {bar_color};"></div>
                </div>
            </div>
            """

        return f"""
        <div class="card score-card">
            <div class="score-circle" style="background-color: {color};">
                {int(overall * 100)}
            </div>
            <div class="score-label">{label}</div>
            <p class="score-description">{desc}</p>
            <div class="score-breakdown">
                {breakdown_html}
            </div>
        </div>
        """

    def _render_executive_summary(self) -> str:
        """Render executive summary with details"""
        summary = self.data.get("executive_summary", {})
        points = summary.get("summary_points", [])
        critical = summary.get("critical_findings", [])
        modules_analyzed = summary.get("modules_analyzed", 0)

        points_html = ""
        for p in points:
            points_html += f"<li>{p}</li>"

        critical_html = ""
        if critical:
            critical_items = ""
            for c in critical:
                # Support both old string format and new dict format
                if isinstance(c, dict):
                    title = c.get("title", "Критическая проблема")
                    detail = c.get("detail", "Требует немедленного внимания")
                    source = c.get("source", "")
                    source_badge = f'<span style="font-size: 0.8em; color: #6b7280; margin-left: 8px;">({source})</span>' if source else ""
                else:
                    title = c
                    detail = "Требует немедленного внимания для обеспечения качественного пользовательского опыта."
                    source_badge = ""

                critical_items += f"""
                <div class="critical-item">
                    <div class="title">{title}{source_badge}</div>
                    <div class="detail">{detail}</div>
                </div>
                """
            critical_html = f"""
            <div class="critical-section">
                <h3>Критические находки</h3>
                <p style="margin-bottom: 12px; color: #991b1b;">
                    Обнаружены проблемы, которые существенно влияют на возможность пользователей
                    достигать своих целей на сайте.
                </p>
                {critical_items}
            </div>
            """

        return f"""
        <div class="card">
            <h2>Краткое резюме</h2>
            <p style="color: #6b7280; margin-bottom: 16px;">
                Проанализировано {modules_analyzed} модулей. Ниже представлены ключевые выводы аудита.
            </p>

            <div class="summary-grid">
                <div class="summary-box">
                    <h4>Основные выводы</h4>
                    <ul>{points_html}</ul>
                </div>
            </div>

            {critical_html}
        </div>
        """

    def _render_detailed_findings(self) -> str:
        """Render detailed findings from Module D insights"""
        summaries = self.data.get("module_summaries", {})
        module_d = summaries.get("module_d", {})
        insights = module_d.get("insights", [])

        if not insights:
            return ""

        insights_html = ""
        for insight in insights:
            insights_html += f'<div class="insight-item">{insight}</div>'

        return f"""
        <div class="card">
            <h2>Детальный анализ пользовательского опыта</h2>
            <p style="color: #6b7280; margin-bottom: 16px;">
                На основе анализа эмоционального состояния и поведения пользователя выявлены следующие паттерны:
            </p>
            <div class="insights-list">
                {insights_html}
            </div>
        </div>
        """

    def _render_module_details(self) -> str:
        """Render detailed module summaries"""
        summaries = self.data.get("module_summaries", {})
        cards_html = ""

        # Module A - Visual
        if "module_a" in summaries:
            m = summaries["module_a"]
            severity = m.get("severity", {})
            assessment = m.get("assessment", "")[:300]
            cards_html += f"""
            <div class="module-card">
                <h3>
                    <span class="icon" style="background: #ede9fe; color: #7c3aed;">A</span>
                    Визуальный анализ
                </h3>
                <div class="stats">
                    <div class="stat-row">
                        <span class="stat-label">Всего проблем</span>
                        <span class="stat-value">{m.get('total_issues', 0)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Критичные</span>
                        <span class="stat-value" style="color: #dc2626;">{severity.get('critical', 0)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Высокие</span>
                        <span class="stat-value" style="color: #ea580c;">{severity.get('high', 0)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Средние</span>
                        <span class="stat-value">{severity.get('medium', 0)}</span>
                    </div>
                </div>
                <div class="description">
                    <strong>Оценка:</strong> {assessment}{'...' if len(m.get('assessment', '')) > 300 else ''}
                </div>
            </div>
            """

        # Module B - Behavioral
        if "module_b" in summaries:
            m = summaries["module_b"]
            status_labels = {
                "completed": ("Выполнена", "#16a34a"),
                "failed": ("Не выполнена", "#dc2626"),
                "max_steps_reached": ("Прервана (лимит шагов)", "#ea580c"),
                "partial": ("Частично выполнена", "#ca8a04")
            }
            status, color = status_labels.get(m.get('task_status'), ("Неизвестно", "#6b7280"))
            cards_html += f"""
            <div class="module-card">
                <h3>
                    <span class="icon" style="background: #dbeafe; color: #2563eb;">B</span>
                    Поведенческий анализ
                </h3>
                <div class="stats">
                    <div class="stat-row">
                        <span class="stat-label">Шагов выполнено</span>
                        <span class="stat-value">{m.get('total_steps', 0)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Статус задачи</span>
                        <span class="stat-value" style="color: {color};">{status}</span>
                    </div>
                </div>
                <div class="description">
                    <strong>Причина завершения:</strong> {m.get('termination_reason', 'N/A')}
                </div>
            </div>
            """

        # Module C - Accessibility
        if "module_c" in summaries:
            m = summaries["module_c"]
            impact = m.get("by_impact", {})
            cards_html += f"""
            <div class="module-card">
                <h3>
                    <span class="icon" style="background: #d1fae5; color: #059669;">C</span>
                    Аудит доступности (WCAG {m.get('wcag_level', 'AA')})
                </h3>
                <div class="stats">
                    <div class="stat-row">
                        <span class="stat-label">Всего проблем</span>
                        <span class="stat-value">{m.get('total_issues', 0)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Критичные</span>
                        <span class="stat-value" style="color: #dc2626;">{impact.get('critical', 0)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Серьёзные</span>
                        <span class="stat-value" style="color: #ea580c;">{impact.get('serious', 0)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Страниц проверено</span>
                        <span class="stat-value">{m.get('pages_scanned', 0)}</span>
                    </div>
                </div>
                <div class="description">
                    Проверка соответствия стандартам WCAG 2.1 уровня {m.get('wcag_level', 'AA')}.
                    {'<br><strong style="color: #dc2626;">Критические проблемы требуют немедленного исправления!</strong>' if impact.get('critical', 0) > 0 else ''}
                </div>
            </div>
            """

        # Module D - Sentiment
        if "module_d" in summaries:
            m = summaries["module_d"]
            trend_info = {
                "improving": ("Улучшение", "#16a34a", "Пользователь становился более удовлетворён"),
                "stable": ("Стабильно", "#6b7280", "Эмоциональное состояние не менялось"),
                "declining": ("Ухудшение", "#dc2626", "Пользователь испытывал нарастающую фрустрацию")
            }
            trend, trend_color, trend_desc = trend_info.get(m.get('trend'), ("N/A", "#6b7280", ""))
            score = m.get("session_score", 0)
            dist = m.get("distribution", {})

            cards_html += f"""
            <div class="module-card">
                <h3>
                    <span class="icon" style="background: #fef3c7; color: #d97706;">D</span>
                    Анализ эмоций
                </h3>
                <div class="stats">
                    <div class="stat-row">
                        <span class="stat-label">Оценка сессии</span>
                        <span class="stat-value" style="color: {'#16a34a' if score > 0 else '#dc2626' if score < 0 else '#6b7280'};">{score:+.2f}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Тренд</span>
                        <span class="stat-value" style="color: {trend_color};">{trend}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Болевые точки</span>
                        <span class="stat-value" style="color: #dc2626;">{m.get('pain_points_count', 0)}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Распределение</span>
                        <span class="stat-value" style="font-size: 0.85em;">
                            +{dist.get('POSITIVE', 0)} / ~{dist.get('NEUTRAL', 0)} / -{dist.get('NEGATIVE', 0)}
                        </span>
                    </div>
                </div>
                <div class="description">
                    {trend_desc}
                </div>
            </div>
            """

        return f"""
        <div class="card">
            <h2>Результаты по модулям</h2>
            <p style="color: #6b7280; margin-bottom: 20px;">
                Детальная разбивка результатов каждого модуля анализа.
            </p>
            <div class="module-grid">
                {cards_html}
            </div>
        </div>
        """

    def _render_all_issues_detailed(self) -> str:
        """Render all issues with full details grouped by severity"""
        issues = self.data.get("all_issues", [])

        if not issues:
            return """
            <div class="card">
                <h2>Выявленные проблемы</h2>
                <p style="color: #16a34a; text-align: center; padding: 20px;">
                    Критических проблем не обнаружено.
                </p>
            </div>
            """

        # Group issues by severity
        grouped = {}
        for issue in issues:
            sev = issue.get("severity", "medium").lower()
            if sev not in grouped:
                grouped[sev] = []
            grouped[sev].append(issue)

        severity_order = ["critical", "high", "serious", "medium", "moderate", "low", "minor"]
        severity_names = {
            "critical": "Критические",
            "high": "Высокие",
            "serious": "Серьёзные",
            "medium": "Средние",
            "moderate": "Умеренные",
            "low": "Низкие",
            "minor": "Минорные"
        }

        groups_html = ""
        for sev in severity_order:
            if sev not in grouped:
                continue

            issues_html = ""
            for issue in grouped[sev]:
                source = issue.get("source", "Unknown")
                desc = issue.get("description", "")

                # Build metadata
                meta_items = []
                if issue.get("location"):
                    meta_items.append(f"Локация: {issue['location']}")
                if issue.get("heuristic"):
                    meta_items.append(f"Эвристика: {issue['heuristic']}")
                if issue.get("wcag"):
                    meta_items.append(f"WCAG: {issue['wcag']}")
                if issue.get("affected_nodes"):
                    meta_items.append(f"Затронуто элементов: {issue['affected_nodes']}")
                if issue.get("emotion"):
                    meta_items.append(f"Эмоция: {issue['emotion']}")
                if issue.get("step_id"):
                    meta_items.append(f"Шаг #{issue['step_id']}")

                meta_html = "".join(f"<span>{m}</span>" for m in meta_items)

                # Recommendation block if exists
                rec = issue.get("recommendation", "")
                rec_html = ""
                if rec:
                    rec_html = f'''
                    <div style="margin-top: 12px; padding: 12px; background: #f0fdf4; border-radius: 6px; border-left: 3px solid #22c55e;">
                        <strong style="color: #166534;">Рекомендация:</strong> {rec}
                    </div>
                    '''

                issues_html += f"""
                <div class="issue-item {sev}">
                    <div class="issue-header">
                        <div class="issue-title">{desc[:150]}{'...' if len(desc) > 150 else ''}</div>
                        <span class="issue-source">{source}</span>
                    </div>
                    <div class="issue-description">{desc}</div>
                    {f'<div class="issue-meta">{meta_html}</div>' if meta_items else ''}
                    {rec_html}
                </div>
                """

            groups_html += f"""
            <div class="issue-group">
                <div class="issue-group-header">
                    <span class="badge {sev}">{severity_names.get(sev, sev).upper()}</span>
                    <span style="color: #6b7280;">{len(grouped[sev])} проблем(ы)</span>
                </div>
                {issues_html}
            </div>
            """

        return f"""
        <div class="card">
            <h2>Все выявленные проблемы ({len(issues)})</h2>
            <p style="color: #6b7280; margin-bottom: 20px;">
                Проблемы сгруппированы по уровню серьёзности. Рекомендуется начать исправление с критических.
            </p>
            <div class="issues-section">
                {groups_html}
            </div>
        </div>
        """

    def _render_recommendations_detailed(self) -> str:
        """Render detailed recommendations with rationale"""
        recs = self.data.get("recommendations", [])

        if not recs:
            return ""

        # Add rationale to recommendations
        rationales = {
            "Доступность": "Проблемы доступности исключают часть пользователей и могут нарушать законодательные требования.",
            "Интерфейс": "Визуальные проблемы влияют на первое впечатление и доверие пользователей к сайту.",
            "Навигация": "Проблемы навигации напрямую влияют на способность пользователей достигать своих целей.",
            "UX": "Эмоциональный опыт пользователя определяет его лояльность и вероятность повторного визита."
        }

        recs_html = ""
        for i, rec in enumerate(recs, 1):
            priority = rec.get("priority", "medium")
            category = rec.get("category", "")
            text = rec.get("text", "")
            source = rec.get("source", "")
            rationale = rationales.get(category, "Рекомендация основана на комплексном анализе.")

            recs_html += f"""
            <div class="rec-item {priority}">
                <div class="rec-header">
                    <span class="rec-category">{category} | {source}</span>
                    <span class="rec-priority {priority}">{priority.upper()}</span>
                </div>
                <div class="rec-title">{i}. {text}</div>
                <div class="rec-rationale">
                    <strong>Почему это важно:</strong> {rationale}
                </div>
            </div>
            """

        return f"""
        <div class="card">
            <h2>Рекомендации по улучшению ({len(recs)})</h2>
            <p style="color: #6b7280; margin-bottom: 20px;">
                Приоритизированный список действий для улучшения UX. Рекомендуется выполнять в указанном порядке.
            </p>
            {recs_html}
        </div>
        """

    def _render_footer(self) -> str:
        """Render footer"""
        generated = self.data.get("generated_at", datetime.now().isoformat())

        return f"""
        <div class="footer">
            <p><strong>UX AI Audit System</strong></p>
            <p>Сгенерировано: {generated}</p>
            <p style="margin-top: 8px; font-size: 0.85em;">
                Отчёт создан автоматически на основе анализа модулей A-D.
            </p>
        </div>
        """

    def save_html(self, output_path: Path) -> Path:
        """Save HTML report to file"""
        html = self.generate_html()
        output_path = Path(output_path)
        output_path.write_text(html, encoding="utf-8")
        return output_path
