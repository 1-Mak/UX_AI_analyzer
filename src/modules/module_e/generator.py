"""
Module E - Report Generator
Generates structured reports from all module results
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from .report_config import (
    REPORT_SECTIONS,
    SEVERITY_ORDER,
    RATING_THRESHOLDS,
    SCORE_WEIGHTS,
    ISSUE_ICONS,
    MODULE_STATUS,
    PERSONA_CONTEXT
)


class ReportGenerator:
    """Generates comprehensive UX audit reports"""

    def __init__(self, session_dir: Path, audit_results: Dict[str, Any]):
        """
        Initialize report generator

        Args:
            session_dir: Directory containing module outputs
            audit_results: Combined results from all modules
        """
        self.session_dir = Path(session_dir)
        self.audit_results = audit_results
        self.report_data = {}

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive report from all module results

        Returns:
            Complete report data structure
        """
        self.report_data = {
            "metadata": self._generate_metadata(),
            "overall_score": self._calculate_overall_score(),
            "executive_summary": self._generate_executive_summary(),
            "module_summaries": self._generate_module_summaries(),
            "all_issues": self._collect_all_issues(),
            "recommendations": self._generate_recommendations(),
            "generated_at": datetime.now().isoformat()
        }

        return self.report_data

    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate report metadata"""
        config = self.audit_results.get("config", {})
        persona_key = config.get("persona", "student")
        persona_info = PERSONA_CONTEXT.get(persona_key, PERSONA_CONTEXT["student"])

        return {
            "session_id": self.audit_results.get("session_id", "unknown"),
            "url": config.get("url", "N/A"),
            "task": config.get("task", "N/A"),
            "persona": {
                "key": persona_key,
                "name": persona_info["name_ru"],
                "description": persona_info["description_ru"]
            },
            "modules_run": self._get_modules_status()
        }

    def _get_modules_status(self) -> Dict[str, str]:
        """Get status of each module run"""
        status = {}

        modules = ["module_a", "module_b", "module_c", "module_d"]
        for module in modules:
            result = self.audit_results.get(f"{module}_results", {})

            if not result:
                status[module] = "not_run"
            elif "error" in result:
                status[module] = "error"
            elif "skipped" in result:
                status[module] = "skipped"
            else:
                status[module] = "success"

        return status

    def _calculate_overall_score(self) -> Dict[str, Any]:
        """
        Calculate overall UX score from all modules

        Returns:
            Score data with breakdown
        """
        scores = {}
        weights_used = {}

        # Module A score (visual issues)
        module_a = self.audit_results.get("module_a_results", {})
        if module_a and "error" not in module_a and "skipped" not in module_a:
            total_issues = module_a.get("total_issues", 0)
            severity = module_a.get("severity_breakdown", {})
            # Score based on issue severity (fewer critical = better)
            critical = severity.get("critical", 0)
            high = severity.get("high", 0)
            # Simple scoring: max 100 points, deduct for issues
            deductions = critical * 20 + high * 10 + (total_issues - critical - high) * 5
            scores["visual"] = max(0, min(1, 1 - deductions / 100))
            weights_used["visual"] = SCORE_WEIGHTS["visual"]

        # Module B score (behavioral success)
        module_b = self.audit_results.get("module_b_results", {})
        if module_b and "error" not in module_b and "skipped" not in module_b:
            task_status = module_b.get("task_status", "failed")
            total_steps = module_b.get("total_steps", 0)
            # Score: completed = 1.0, partial = 0.6, failed = 0.3
            status_scores = {"completed": 1.0, "partial": 0.6, "failed": 0.3, "max_steps_reached": 0.4}
            scores["behavioral"] = status_scores.get(task_status, 0.5)
            weights_used["behavioral"] = SCORE_WEIGHTS["behavioral"]

        # Module C score (accessibility)
        module_c = self.audit_results.get("module_c_results", {})
        if module_c and "error" not in module_c and "skipped" not in module_c:
            by_impact = module_c.get("by_impact", {})
            critical = by_impact.get("critical", 0)
            serious = by_impact.get("serious", 0)
            moderate = by_impact.get("moderate", 0)
            # Accessibility is binary for critical issues
            if critical > 0:
                scores["accessibility"] = 0.2
            elif serious > 3:
                scores["accessibility"] = 0.4
            elif serious > 0:
                scores["accessibility"] = 0.6
            elif moderate > 0:
                scores["accessibility"] = 0.8
            else:
                scores["accessibility"] = 1.0
            weights_used["accessibility"] = SCORE_WEIGHTS["accessibility"]

        # Module D score (sentiment)
        module_d = self.audit_results.get("module_d_results", {})
        if module_d and "error" not in module_d and "skipped" not in module_d:
            session_score = module_d.get("session_score", 0)  # -1 to +1
            # Convert -1..+1 to 0..1
            scores["sentiment"] = (session_score + 1) / 2
            weights_used["sentiment"] = SCORE_WEIGHTS["sentiment"]

        # Calculate weighted average
        if scores and weights_used:
            total_weight = sum(weights_used.values())
            weighted_sum = sum(scores[k] * weights_used[k] for k in scores)
            overall = weighted_sum / total_weight if total_weight > 0 else 0
        else:
            overall = 0

        # Determine rating
        rating = "critical"
        for level, config in sorted(RATING_THRESHOLDS.items(), key=lambda x: x[1]["min_score"], reverse=True):
            if overall >= config["min_score"]:
                rating = level
                break

        return {
            "overall": round(overall, 2),
            "rating": rating,
            "rating_label": RATING_THRESHOLDS[rating]["label_ru"],
            "rating_color": RATING_THRESHOLDS[rating]["color"],
            "breakdown": {k: round(v, 2) for k, v in scores.items()},
            "weights": weights_used
        }

    def _generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary section with detailed critical findings"""
        summary_points = []
        critical_findings = []  # List of dicts with title and detail

        # Analyze Module A - load actual issues for details
        module_a = self.audit_results.get("module_a_results", {})
        if module_a and "total_issues" in module_a:
            total = module_a["total_issues"]
            severity = module_a.get("severity_breakdown", {})
            critical_count = severity.get("critical", 0)
            high = severity.get("high", 0)

            # Load actual critical/high issues from file
            module_a_file = self.session_dir / "module_a_visual_analysis.json"
            if module_a_file.exists() and (critical_count > 0 or high > 0):
                try:
                    with open(module_a_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for issue in data.get("issues", []):
                            sev = issue.get("severity", "").lower()
                            if sev == "critical":
                                critical_findings.append({
                                    "title": issue.get("title", "Критическая визуальная проблема"),
                                    "detail": issue.get("description", "")[:200],
                                    "source": "Module A"
                                })
                            elif sev == "high" and len(critical_findings) < 5:
                                critical_findings.append({
                                    "title": issue.get("title", "Серьёзная проблема юзабилити"),
                                    "detail": issue.get("description", "")[:200],
                                    "source": "Module A"
                                })
                except Exception:
                    if critical_count > 0:
                        critical_findings.append({
                            "title": f"Найдено {critical_count} критических визуальных проблем",
                            "detail": "Проблемы требуют немедленного внимания",
                            "source": "Module A"
                        })

            if high > 0:
                summary_points.append(f"Обнаружено {high} серьезных проблем юзабилити")
            summary_points.append(f"Визуальный анализ выявил {total} проблем интерфейса")

        # Analyze Module B
        module_b = self.audit_results.get("module_b_results", {})
        if module_b and "task_status" in module_b:
            status = module_b["task_status"]
            steps = module_b.get("total_steps", 0)
            reason = module_b.get("termination_reason", "")

            if status == "completed":
                summary_points.append(f"Задача выполнена за {steps} шагов")
            elif status == "failed":
                critical_findings.append({
                    "title": "Задача не была выполнена",
                    "detail": f"Пользователь не смог достичь цели. Причина: {reason}",
                    "source": "Module B"
                })
            elif status == "max_steps_reached":
                critical_findings.append({
                    "title": f"Задача не завершена за {steps} шагов",
                    "detail": "Навигация слишком сложная - пользователь не нашёл путь к цели",
                    "source": "Module B"
                })

        # Analyze Module C - load actual accessibility issues
        module_c = self.audit_results.get("module_c_results", {})
        if module_c and "total_issues" in module_c:
            total = module_c["total_issues"]
            by_impact = module_c.get("by_impact", {})
            critical_count = by_impact.get("critical", 0)
            serious = by_impact.get("serious", 0)

            # Load actual critical issues from file
            module_c_file = self.session_dir / "module_c_accessibility_scan.json"
            if module_c_file.exists() and (critical_count > 0 or serious > 0):
                try:
                    with open(module_c_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for issue in data.get("all_issues", []):
                            impact = issue.get("impact", "")
                            if impact == "critical":
                                critical_findings.append({
                                    "title": f"[WCAG] {issue.get('help', 'Критическая проблема доступности')}",
                                    "detail": f"Затронуто элементов: {issue.get('affected_nodes_count', 0)}. Теги: {', '.join(issue.get('tags', [])[:3])}",
                                    "source": "Module C"
                                })
                            elif impact == "serious" and len(critical_findings) < 7:
                                critical_findings.append({
                                    "title": f"[WCAG] {issue.get('help', 'Серьёзное нарушение доступности')}",
                                    "detail": f"Затронуто элементов: {issue.get('affected_nodes_count', 0)}",
                                    "source": "Module C"
                                })
                except Exception:
                    if critical_count > 0:
                        critical_findings.append({
                            "title": f"Найдено {critical_count} критических проблем доступности",
                            "detail": "Нарушения WCAG требуют немедленного исправления",
                            "source": "Module C"
                        })

            if serious > 0:
                summary_points.append(f"Обнаружено {serious} серьезных нарушений WCAG")
            summary_points.append(f"Аудит доступности выявил {total} проблем")

        # Analyze Module D - load pain points
        module_d = self.audit_results.get("module_d_results", {})
        if module_d and "session_score" in module_d:
            score = module_d["session_score"]
            trend = module_d.get("trend", "stable")
            pain_points = module_d.get("pain_points_count", 0)

            if score < -0.3:
                # Load actual pain points from file
                module_d_file = self.session_dir / "module_d_sentiment_analysis.json"
                if module_d_file.exists():
                    try:
                        with open(module_d_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            for point in data.get("pain_points", [])[:2]:
                                critical_findings.append({
                                    "title": f"Фрустрация на шаге #{point.get('step_id', '?')}",
                                    "detail": point.get("issue", "")[:150],
                                    "source": "Module D"
                                })
                    except Exception:
                        critical_findings.append({
                            "title": "Негативный эмоциональный опыт пользователя",
                            "detail": f"Оценка сессии: {score:.2f}",
                            "source": "Module D"
                        })

            if trend == "declining":
                summary_points.append("Эмоциональный тренд: ухудшение к концу сессии")
            if pain_points > 0:
                summary_points.append(f"Выявлено {pain_points} болевых точек")

        return {
            "summary_points": summary_points,
            "critical_findings": critical_findings,
            "modules_analyzed": sum(1 for m in ["module_a", "module_b", "module_c", "module_d"]
                                    if self.audit_results.get(f"{m}_results", {})
                                    and "error" not in self.audit_results.get(f"{m}_results", {})
                                    and "skipped" not in self.audit_results.get(f"{m}_results", {}))
        }

    def _generate_module_summaries(self) -> Dict[str, Any]:
        """Generate individual module summaries"""
        summaries = {}

        # Module A summary
        module_a = self.audit_results.get("module_a_results", {})
        if module_a and "error" not in module_a and "skipped" not in module_a:
            summaries["module_a"] = {
                "title": REPORT_SECTIONS["visual_analysis"]["title_ru"],
                "status": "success",
                "total_issues": module_a.get("total_issues", 0),
                "severity": module_a.get("severity_breakdown", {}),
                "assessment": module_a.get("overall_assessment", "")
            }

        # Module B summary
        module_b = self.audit_results.get("module_b_results", {})
        if module_b and "error" not in module_b and "skipped" not in module_b:
            summaries["module_b"] = {
                "title": REPORT_SECTIONS["behavioral_analysis"]["title_ru"],
                "status": "success",
                "total_steps": module_b.get("total_steps", 0),
                "task_status": module_b.get("task_status", "unknown"),
                "termination_reason": module_b.get("termination_reason", "")
            }

        # Module C summary
        module_c = self.audit_results.get("module_c_results", {})
        if module_c and "error" not in module_c and "skipped" not in module_c:
            summaries["module_c"] = {
                "title": REPORT_SECTIONS["accessibility_audit"]["title_ru"],
                "status": "success",
                "total_issues": module_c.get("total_issues", 0),
                "by_impact": module_c.get("by_impact", {}),
                "wcag_level": module_c.get("wcag_level", "AA"),
                "pages_scanned": module_c.get("pages_scanned", 0)
            }

        # Module D summary
        module_d = self.audit_results.get("module_d_results", {})
        if module_d and "error" not in module_d and "skipped" not in module_d:
            summaries["module_d"] = {
                "title": REPORT_SECTIONS["sentiment_analysis"]["title_ru"],
                "status": "success",
                "session_score": module_d.get("session_score", 0),
                "trend": module_d.get("trend", "stable"),
                "distribution": module_d.get("distribution", {}),
                "pain_points_count": module_d.get("pain_points_count", 0),
                "insights": module_d.get("insights", [])
            }

        return summaries

    def _collect_all_issues(self) -> List[Dict[str, Any]]:
        """Collect and prioritize all issues from all modules"""
        all_issues = []

        # Load detailed Module A issues
        module_a_file = self.session_dir / "module_a_visual_analysis.json"
        if module_a_file.exists():
            try:
                with open(module_a_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for issue in data.get("issues", []):
                        # Build full description from title + description
                        title = issue.get("title", "")
                        desc = issue.get("description", "")
                        full_desc = f"{title}: {desc}" if title and desc else title or desc

                        all_issues.append({
                            "source": "Module A",
                            "type": "visual",
                            "severity": issue.get("severity", "medium").lower(),
                            "description": full_desc,
                            "location": issue.get("location", ""),
                            "heuristic": issue.get("heuristic", ""),
                            "recommendation": issue.get("recommendation", "")
                        })
            except Exception:
                pass

        # Load detailed Module C issues
        module_c_file = self.session_dir / "module_c_accessibility_scan.json"
        if module_c_file.exists():
            try:
                with open(module_c_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for issue in data.get("all_issues", []):
                        all_issues.append({
                            "source": "Module C",
                            "type": "accessibility",
                            "severity": issue.get("impact", "moderate"),
                            "description": issue.get("help", ""),
                            "wcag": ", ".join(issue.get("tags", [])),
                            "affected_nodes": issue.get("affected_nodes_count", 0)
                        })
            except Exception:
                pass

        # Load Module D pain points
        module_d_file = self.session_dir / "module_d_sentiment_analysis.json"
        if module_d_file.exists():
            try:
                with open(module_d_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for point in data.get("pain_points", []):
                        all_issues.append({
                            "source": "Module D",
                            "type": "sentiment",
                            "severity": "high",  # Pain points are high severity
                            "description": point.get("issue", ""),
                            "emotion": point.get("emotion", ""),
                            "step_id": point.get("step_id", 0)
                        })
            except Exception:
                pass

        # Sort by severity
        def severity_key(issue):
            severity = issue.get("severity", "medium").lower()
            return SEVERITY_ORDER.index(severity) if severity in SEVERITY_ORDER else 99

        all_issues.sort(key=severity_key)

        return all_issues

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations"""
        recommendations = []

        # Analyze results and generate recommendations
        module_a = self.audit_results.get("module_a_results", {})
        module_b = self.audit_results.get("module_b_results", {})
        module_c = self.audit_results.get("module_c_results", {})
        module_d = self.audit_results.get("module_d_results", {})

        # Critical accessibility issues
        if module_c and module_c.get("by_impact", {}).get("critical", 0) > 0:
            recommendations.append({
                "priority": "critical",
                "category": "Доступность",
                "text": "Немедленно исправить критические проблемы доступности (WCAG)",
                "source": "Module C"
            })

        # Critical visual issues
        if module_a and module_a.get("severity_breakdown", {}).get("critical", 0) > 0:
            recommendations.append({
                "priority": "critical",
                "category": "Интерфейс",
                "text": "Исправить критические проблемы визуального дизайна",
                "source": "Module A"
            })

        # Task completion issues
        if module_b and module_b.get("task_status") == "failed":
            recommendations.append({
                "priority": "high",
                "category": "Навигация",
                "text": "Улучшить навигацию - пользователь не смог выполнить задачу",
                "source": "Module B"
            })

        # Negative sentiment
        if module_d and module_d.get("session_score", 0) < -0.3:
            recommendations.append({
                "priority": "high",
                "category": "UX",
                "text": "Провести глубокий анализ болевых точек пользователя",
                "source": "Module D"
            })

        # Accessibility serious issues
        if module_c and module_c.get("by_impact", {}).get("serious", 0) > 2:
            recommendations.append({
                "priority": "medium",
                "category": "Доступность",
                "text": "Устранить серьезные нарушения WCAG для соответствия стандартам",
                "source": "Module C"
            })

        # Add insights from Module D as recommendations
        if module_d:
            for insight in module_d.get("insights", [])[:3]:
                if "рекомендация" in insight.lower() or "добавить" in insight.lower():
                    recommendations.append({
                        "priority": "medium",
                        "category": "UX",
                        "text": insight,
                        "source": "Module D"
                    })

        return recommendations

    def save_json_report(self, filename: str = "module_e_final_report.json") -> Path:
        """Save report as JSON file"""
        if not self.report_data:
            self.generate_report()

        output_path = self.session_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)

        return output_path
