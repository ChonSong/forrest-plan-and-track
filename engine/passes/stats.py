"""Statistical analysis passes — distributions, percentiles, and aggregates."""

from ..findings import Finding
from ..scoring import score_finding, default_specificity


def run(conn) -> list:
    findings = []
    findings.extend(_lock_duration_distribution(conn))
    findings.extend(_rfi_completion_distribution(conn))
    findings.extend(_isolation_point_utilization(conn))
    findings.extend(_workload_balance(conn))
    return [score_finding(f) for f in findings]


def _lock_duration_distribution(conn) -> list:
    """Analyze distribution of lock durations (time between lock-on and lock-off)."""
    sql = """SELECT 
                COUNT(*) as Total,
                AVG(ABS((julianday(LockOffDate) - julianday(LockOnDate)) * 24 * 60)) as AvgMins,
                MAX(ABS((julianday(LockOffDate) - julianday(LockOnDate)) * 24 * 60)) as MaxMins,
                MIN(ABS((julianday(LockOffDate) - julianday(LockOnDate)) * 24 * 60)) as MinMins
             FROM RFILocks
             WHERE LockOffDate IS NOT NULL AND LockOnDate IS NOT NULL"""
    cursor = conn.execute(sql)
    row = cursor.fetchone()
    if not row or row[0] == 0:
        return []

    total, avg_min, max_min, min_min = row

    # Count outliers (durations > 2x the average)
    outlier_sql = """SELECT COUNT(*) FROM RFILocks 
                     WHERE LockOffDate IS NOT NULL AND LockOnDate IS NOT NULL
                     AND ABS((julianday(LockOffDate) - julianday(LockOnDate)) * 24 * 60) > ?"""
    cursor = conn.execute(outlier_sql, (avg_min * 2,))
    outliers = cursor.fetchone()[0]

    return [Finding(
        title=f"Lock duration: avg {avg_min:.0f} min, max {max_min:.0f} min, {outliers} outliers",
        description=f"Analysis of {total} lock events: average duration is {avg_min:.0f} minutes, ranging from {min_min:.0f} to {max_min:.0f}m. {outliers} events ({100*outliers//total}%) exceed 2x the average duration — these are candidates for process investigation.",
        category="statistic",
        severity=0.5,
        specificity=default_specificity(f"Avg {avg_min:.0f}m, max {max_min:.0f}m, {outliers} outliers"),
        surprise=0.5,
        query=sql,
        affected_tables=["RFILocks"],
        evidence=f"Avg: {avg_min:.0f}m | Range: {min_min:.0f}-{max_min:.0f}m | Outliers: {outliers}",
    )]


def _rfi_completion_distribution(conn) -> list:
    """Analyze how many RFIs have expected durations."""
    sql = """SELECT 
                COUNT(*) as Total,
                AVG((julianday(ExpectedEndDate) - julianday(ExpectedStartDate))) as AvgDays
             FROM RFIs
             WHERE ExpectedEndDate IS NOT NULL AND ExpectedStartDate IS NOT NULL"""
    cursor = conn.execute(sql)
    row = cursor.fetchone()
    if not row or row[0] == 0:
        return []

    total, avg_days = row
    avg_days = abs(avg_days) if avg_days else 0

    if avg_days < 1:
        return []

    # Count RFIs with duration > 2x average
    outlier_sql = """SELECT COUNT(*) FROM RFIs
                     WHERE ExpectedEndDate IS NOT NULL AND ExpectedStartDate IS NOT NULL
                     AND (julianday(ExpectedEndDate) - julianday(ExpectedStartDate)) > ?"""
    cursor = conn.execute(outlier_sql, (avg_days * 2,))
    outliers = cursor.fetchone()[0]

    return [Finding(
        title=f"Average RFI duration: {avg_days:.1f} days ({outliers} outliers)",
        description=f"Across {total} RFIs with valid dates, the average expected duration is {avg_days:.1f} days. {outliers} RFIs ({100*outliers//total}%) exceed twice the average — these may represent complex or delayed isolations.",
        category="statistic",
        severity=0.3,
        specificity=default_specificity(f"Avg {avg_days:.1f}d, {outliers} outliers"),
        surprise=0.3,
        query=sql,
        affected_tables=["RFIs"],
        evidence=f"Avg: {avg_days:.1f}d | Outliers: {outliers}",
    )]


def _isolation_point_utilization(conn) -> list:
    """Calculate utilization rate of isolation points."""
    sql = """SELECT 
                COUNT(DISTINCT ri.IsolationPointId) as UsedPoints,
                (SELECT COUNT(*) FROM IsolationPoints) as TotalPoints
             FROM RFIIsolations ri"""
    cursor = conn.execute(sql)
    row = cursor.fetchone()
    if not row:
        return []

    used, total = row
    if total == 0:
        return []
    rate = 100 * used // total

    return [Finding(
        title=f"Isolation point utilization: {rate}% ({used}/{total})",
        description=f"Of {total} isolation points in the system, {used} ({rate}%) have been used in at least one RFI isolation. {total-used} points ({100-used}%) are unused — potential for asset review and rationalization.",
        category="statistic",
        severity=0.4,
        specificity=default_specificity(f"{rate}% utilization ({used}/{total})"),
        surprise=0.4,
        query=sql,
        affected_tables=["RFIIsolations", "IsolationPoints"],
        evidence=f"Utilization: {rate}% ({used}/{total})",
    )]


def _workload_balance(conn) -> list:
    """Check workload distribution across users."""
    sql = """SELECT 
                COUNT(*) as TotalUsers,
                (SELECT COUNT(DISTINCT UserId) FROM RFILocks) as ActiveUsers
             FROM Users"""
    cursor = conn.execute(sql)
    row = cursor.fetchone()
    if not row:
        return []

    total_users, active_users = row
    if total_users == 0:
        return []

    participation = 100 * active_users // total_users

    # Get the most active user's share
    sql2 = """SELECT MAX(cnt) * 1.0 / (SELECT COUNT(*) FROM RFILocks) FROM 
              (SELECT UserId, COUNT(*) as cnt FROM RFILocks GROUP BY UserId)"""
    cursor = conn.execute(sql2)
    top_share = cursor.fetchone()[0] or 0

    return [Finding(
        title=f"Only {participation}% of users active in lock events ({top_share:.0%} concentration)",
        description=f"Of {total_users} registered users, only {active_users} ({participation}%) have performed lock events. The most active user accounts for {top_share:.0%} of all events — a significant workload concentration risk.",
        category="statistic",
        severity=0.6,
        specificity=default_specificity(f"{participation}% participation, {top_share:.0%} concentration"),
        surprise=0.5,
        query=sql2,
        affected_tables=["Users", "RFILocks"],
        evidence=f"Active: {participation}% | Concentration: {top_share:.0%}",
    )]
