"""Finding data model for the Forrest analysis engine."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Finding:
    """One analysis finding — an anomaly, pattern, relationship, or statistic."""

    title: str
    description: str
    category: str  # anomaly, pattern, relationship, statistic
    score: float = 0.0
    severity: float = 0.0
    specificity: float = 0.0
    surprise: float = 0.0
    query: str = ""
    affected_tables: list = field(default_factory=list)
    evidence: str = ""

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "score": round(self.score, 3),
            "severity": round(self.severity, 3),
            "specificity": round(self.specificity, 3),
            "surprise": round(self.surprise, 3),
            "query": self.query,
            "affected_tables": self.affected_tables,
            "evidence": self.evidence,
        }

    def __str__(self):
        sev = {0.8: "🔴", 0.5: "🟡", 0.0: "🟢"}
        icon = "🔴" if self.score >= 0.7 else ("🟡" if self.score >= 0.4 else "🟢")
        return (
            f"{icon} [{self.category.upper():11s}] {self.title}\n"
            f"   Score: {self.score:.3f}  |  {self.description[:120]}\n"
            f"   Tables: {', '.join(self.affected_tables)}\n"
        )


@dataclass
class RunResult:
    """Result of a full analysis run."""

    passes_run: int = 0
    total_findings: int = 0
    findings: list = field(default_factory=list)
    duration_seconds: float = 0.0

    def top(self, n=3):
        return sorted(self.findings, key=lambda f: f.score, reverse=True)[:n]

    def summary(self):
        if not self.findings:
            return "No findings generated."
        top = self.top(3)
        lines = [f"Analysis complete: {self.passes_run} passes, {self.total_findings} findings"]
        for f in top:
            lines.append(str(f))
        return "\n".join(lines)
