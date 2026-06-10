"""Finding scoring — rates each finding on severity, specificity, and surprise."""

from .findings import Finding


def score_finding(finding: Finding) -> Finding:
    """
    Score a finding on three dimensions (0-1 each):
    - Severity: How impactful/anomalous is this?
    - Specificity: How precise is the evidence?
    - Surprise: How unexpected is it to a domain expert?

    Final = 0.5×severity + 0.3×specificity + 0.2×surprise
    """
    score = 0.5 * finding.severity + 0.3 * finding.specificity + 0.2 * finding.surprise
    finding.score = min(score, 1.0)
    return finding


def default_specificity(evidence: str) -> float:
    """Estimate specificity from evidence text length and detail."""
    if not evidence:
        return 0.0
    # Check for specific numbers, names, percentages
    import re
    has_numbers = bool(re.search(r'\d+', evidence))
    has_percent = '%' in evidence
    has_names = bool(re.search(r'[A-Z][a-z]+-[A-Z0-9]+', evidence))  # e.g. "PV-101"
    score = 0.3
    if has_numbers:
        score += 0.3
    if has_percent:
        score += 0.2
    if has_names:
        score += 0.2
    return min(score, 1.0)


def default_severity(rows_affected: int, total_rows: int) -> float:
    """Estimate severity from proportion of affected rows."""
    if total_rows == 0:
        return 0.0
    ratio = rows_affected / total_rows
    # Peak at 0.1-0.3 range (a few anomalies among many normal rows)
    if ratio <= 0.01:
        return 0.9  # Very few anomalies = potentially critical
    elif ratio <= 0.05:
        return 0.8
    elif ratio <= 0.15:
        return 0.6
    elif ratio <= 0.30:
        return 0.4
    else:
        return 0.2  # Too many = not anomalous, just normal
