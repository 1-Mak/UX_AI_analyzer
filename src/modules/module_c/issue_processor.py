"""
Issue Processor - Convert axe-core results to AccessibilityIssue models
Handles deduplication and summary generation for multi-page scans
"""
from typing import Dict, List, Optional, Any
from collections import defaultdict

from src.models import AccessibilityIssue
from .wcag_config import (
    IMPACT_LEVELS,
    get_impact_weight,
    get_rule_category,
    get_rule_description_ru,
    get_persona_priority_rules
)


class IssueProcessor:
    """
    Process axe-core scan results into structured AccessibilityIssue models
    """

    def __init__(self, persona_key: Optional[str] = None):
        """
        Initialize processor

        Args:
            persona_key: Optional persona for prioritizing issues
        """
        self.persona_key = persona_key
        self.priority_rules = get_persona_priority_rules(persona_key) if persona_key else []

    def process_axe_results(
        self,
        axe_response: Dict[str, Any],
        url: str
    ) -> List[AccessibilityIssue]:
        """
        Convert axe-core response to list of AccessibilityIssue models

        Args:
            axe_response: Raw response from axe.run()
            url: URL that was scanned

        Returns:
            List of AccessibilityIssue models
        """
        issues = []
        violations = axe_response.get("violations", [])

        for violation in violations:
            issue = self._convert_violation(violation, url)
            if issue:
                issues.append(issue)

        # Sort by impact (critical first) and persona priority
        issues = self._sort_issues(issues)

        return issues

    def _convert_violation(
        self,
        violation: Dict[str, Any],
        url: str
    ) -> Optional[AccessibilityIssue]:
        """
        Convert a single axe-core violation to AccessibilityIssue

        Args:
            violation: Single violation from axe-core
            url: URL of the scanned page

        Returns:
            AccessibilityIssue model or None if conversion fails
        """
        try:
            # Process nodes to add URL context
            nodes = []
            for node in violation.get("nodes", []):
                processed_node = {
                    "target": node.get("target", []),
                    "html": node.get("html", ""),
                    "failureSummary": node.get("failureSummary", ""),
                    "url": url
                }

                # Add impact if node-specific impact differs
                if "impact" in node:
                    processed_node["impact"] = node["impact"]

                nodes.append(processed_node)

            return AccessibilityIssue(
                id=violation.get("id", "unknown"),
                impact=violation.get("impact", "minor"),
                description=violation.get("description", ""),
                help=violation.get("help", ""),
                help_url=violation.get("helpUrl", ""),
                tags=violation.get("tags", []),
                nodes=nodes
            )

        except Exception as e:
            print(f"  Warning: Failed to convert violation: {e}")
            return None

    def _sort_issues(self, issues: List[AccessibilityIssue]) -> List[AccessibilityIssue]:
        """
        Sort issues by impact and persona priority

        Args:
            issues: List of issues to sort

        Returns:
            Sorted list
        """
        def sort_key(issue: AccessibilityIssue) -> tuple:
            # Primary: impact weight (higher = more severe)
            impact_score = get_impact_weight(issue.impact)

            # Secondary: persona priority (lower index = higher priority)
            if issue.id in self.priority_rules:
                priority_score = self.priority_rules.index(issue.id)
            else:
                priority_score = 999

            # Tertiary: number of affected nodes
            nodes_count = len(issue.nodes)

            return (-impact_score, priority_score, -nodes_count)

        return sorted(issues, key=sort_key)

    def deduplicate_issues(
        self,
        all_issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate issues from multiple page scans

        Groups issues by rule ID and aggregates affected nodes/pages

        Args:
            all_issues: List of issue dicts from multiple pages

        Returns:
            Deduplicated list with aggregated statistics
        """
        grouped = defaultdict(lambda: {
            "issue": None,
            "pages_affected": set(),
            "all_nodes": [],
            "total_occurrences": 0
        })

        for issue_data in all_issues:
            issue = issue_data.get("issue")
            url = issue_data.get("url", "")

            if not issue:
                continue

            rule_id = issue.id if hasattr(issue, 'id') else issue.get("id")

            if grouped[rule_id]["issue"] is None:
                grouped[rule_id]["issue"] = issue

            grouped[rule_id]["pages_affected"].add(url)
            grouped[rule_id]["total_occurrences"] += len(
                issue.nodes if hasattr(issue, 'nodes') else issue.get("nodes", [])
            )

            # Collect all unique nodes
            nodes = issue.nodes if hasattr(issue, 'nodes') else issue.get("nodes", [])
            for node in nodes:
                node_with_url = dict(node) if isinstance(node, dict) else node.copy()
                if "url" not in node_with_url:
                    node_with_url["url"] = url
                grouped[rule_id]["all_nodes"].append(node_with_url)

        # Convert to output format
        deduplicated = []
        for rule_id, data in grouped.items():
            issue = data["issue"]

            deduplicated.append({
                "id": rule_id,
                "impact": issue.impact if hasattr(issue, 'impact') else issue.get("impact"),
                "description": issue.description if hasattr(issue, 'description') else issue.get("description"),
                "help": issue.help if hasattr(issue, 'help') else issue.get("help"),
                "help_url": issue.help_url if hasattr(issue, 'help_url') else issue.get("help_url"),
                "tags": issue.tags if hasattr(issue, 'tags') else issue.get("tags", []),
                "pages_affected": list(data["pages_affected"]),
                "total_occurrences": data["total_occurrences"],
                "nodes": data["all_nodes"][:20],  # Limit nodes to avoid huge output
                "category": get_rule_category(rule_id),
                "description_ru": get_rule_description_ru(
                    rule_id,
                    issue.description if hasattr(issue, 'description') else issue.get("description", "")
                )
            })

        # Sort by impact and occurrence count
        deduplicated.sort(
            key=lambda x: (
                -get_impact_weight(x["impact"]),
                -x["total_occurrences"]
            )
        )

        return deduplicated

    def generate_summary(
        self,
        issues: List[AccessibilityIssue]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for issues

        Args:
            issues: List of AccessibilityIssue models

        Returns:
            Summary dict with counts and statistics
        """
        # Count by impact
        by_impact = {level: 0 for level in IMPACT_LEVELS}
        for issue in issues:
            if issue.impact in by_impact:
                by_impact[issue.impact] += 1

        # Count by category
        by_category = defaultdict(int)
        for issue in issues:
            category = get_rule_category(issue.id)
            by_category[category] += 1

        # Most common issues
        issue_counts = defaultdict(int)
        for issue in issues:
            issue_counts[issue.id] += len(issue.nodes)

        most_common = sorted(
            issue_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Total affected nodes
        total_nodes = sum(len(issue.nodes) for issue in issues)

        # Calculate accessibility score (0-100, higher is better)
        # Deduct points based on impact severity
        max_deduction = 100
        deduction = 0
        for issue in issues:
            weight = get_impact_weight(issue.impact)
            nodes_count = len(issue.nodes)
            deduction += weight * min(nodes_count, 5)  # Cap per-issue deduction

        score = max(0, max_deduction - min(deduction, max_deduction))

        # Priority issues for persona
        priority_issues = []
        if self.priority_rules:
            for issue in issues:
                if issue.id in self.priority_rules:
                    priority_issues.append({
                        "id": issue.id,
                        "impact": issue.impact,
                        "nodes_count": len(issue.nodes)
                    })

        return {
            "total_issues": len(issues),
            "total_affected_nodes": total_nodes,
            "by_impact": by_impact,
            "by_category": dict(by_category),
            "most_common_issues": [
                {"id": k, "count": v} for k, v in most_common
            ],
            "accessibility_score": score,
            "priority_issues_for_persona": priority_issues if self.persona_key else None
        }

    def generate_multi_page_summary(
        self,
        deduplicated_issues: List[Dict[str, Any]],
        pages_scanned: List[str]
    ) -> Dict[str, Any]:
        """
        Generate summary for multi-page scan results

        Args:
            deduplicated_issues: Deduplicated issues from deduplicate_issues()
            pages_scanned: List of URLs that were scanned

        Returns:
            Summary dict
        """
        # Count by impact
        by_impact = {level: 0 for level in IMPACT_LEVELS}
        for issue in deduplicated_issues:
            impact = issue.get("impact", "minor")
            if impact in by_impact:
                by_impact[impact] += 1

        # Total occurrences across all pages
        total_occurrences = sum(
            issue.get("total_occurrences", 0)
            for issue in deduplicated_issues
        )

        # Issues affecting multiple pages (site-wide issues)
        site_wide_issues = [
            issue for issue in deduplicated_issues
            if len(issue.get("pages_affected", [])) > 1
        ]

        # Most common issues
        most_common = sorted(
            deduplicated_issues,
            key=lambda x: x.get("total_occurrences", 0),
            reverse=True
        )[:10]

        return {
            "total_issues": len(deduplicated_issues),
            "total_occurrences": total_occurrences,
            "pages_scanned": len(pages_scanned),
            "by_impact": by_impact,
            "site_wide_issues_count": len(site_wide_issues),
            "most_common_issues": [
                {
                    "id": issue["id"],
                    "count": issue.get("total_occurrences", 0),
                    "pages": len(issue.get("pages_affected", []))
                }
                for issue in most_common
            ]
        }
