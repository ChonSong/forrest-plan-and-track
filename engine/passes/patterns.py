"""Pattern recognition passes — finds trends, hot spots, and common behaviors."""

from ..findings import Finding
from ..scoring import score_finding, default_severity, default_specificity


def run(conn) -> list:
    findings = []
    findings.extend(_most_isolated_points(conn))
    findings.extend(_peak_activity_periods(conn))
    findings.extend(_user_activity_hotspots(conn))
    findings.extend(_rfi_state_distribution(conn))
    findings.extend(_common_workflow_paths(conn))
    return [score_finding(f) for f in findings]


def _most_isolated_points(conn) -> list:
    """Find which isolation points are used most frequently."""
    sql = """SELECT ip.Name, COUNT(ri.Id) as UsageCount
             FROM IsolationPoints ip
             JOIN RFIIsolations ri ON ri.IsolationPointId = ip.Id
             GROUP BY ip.Id, ip.Name
             ORDER BY UsageCount DESC
             LIMIT 3"""
    cursor = conn.execute(sql)
    rows = cursor.fetchall()
    if not rows:
        return []

    cursor.execute("SELECT COUNT(*) FROM IsolationPoints")
    total_ips = cursor.fetchone()[0]
    total_uses = sum(r[1] for r in rows)

    names = [f"{r[0]} ({r[1]}x)" for r in rows]
    top_name, top_count = rows[0]

    return [Finding(
        title=f"Top isolation point: {top_name} used {top_count} times",
        description=f"{top_name} is the most-used isolation point with {top_count} RFI references — more than any other point by {' vs '.join(str(r[1]) for r in rows[1:3])}. This suggests high operational dependency on a single point, which is a concentration risk.",
        category="pattern",
        severity=0.5,
        specificity=default_specificity(f"Top: {top_name} ({top_count}x)"),
        surprise=0.5,
        query=sql,
        affected_tables=["IsolationPoints", "RFIIsolations"],
        evidence=f"Top 3: {', '.join(names)}",
    )]


def _peak_activity_periods(conn) -> list:
    """Find which hours of day have the most lock events."""
    sql = """SELECT CAST(strftime('%H', LockOnDate) AS INTEGER) as Hour, COUNT(*) as Events
             FROM RFILocks
             WHERE LockOnDate IS NOT NULL
             GROUP BY Hour
             ORDER BY Events DESC
             LIMIT 3"""
    cursor = conn.execute(sql)
    rows = cursor.fetchall()
    if not rows:
        return []

    peak_hour, peak_count = rows[0]
    cursor.execute("SELECT COUNT(*) FROM RFILocks")
    total = cursor.fetchone()[0]

    return [Finding(
        title=f"Peak lock activity at hour {peak_hour}:00 ({peak_count} events)",
        description=f"Most lock events occur at {peak_hour}:00 ({peak_count} of {total}, {100*peak_count//total}% of all events). This suggests a concentrated work schedule. {' '.join(f'Hour {r[0]}: {r[1]} events' for r in rows)}.",
        category="pattern",
        severity=0.3,
        specificity=default_specificity(f"Peak hour {peak_hour}:00, {peak_count} events"),
        surprise=0.4,
        query=sql,
        affected_tables=["RFILocks"],
        evidence=f"Peak: hour {peak_hour} ({100*peak_count//total}% of events)",
    )]


def _user_activity_hotspots(conn) -> list:
    """Find which users perform the most isolations."""
    sql = """SELECT u.FirstName || ' ' || u.LastName as Name, COUNT(rl.Id) as LockEvents
             FROM Users u
             JOIN RFILocks rl ON rl.UserId = u.Id
             GROUP BY u.Id
             ORDER BY LockEvents DESC
             LIMIT 3"""
    cursor = conn.execute(sql)
    rows = cursor.fetchall()
    if not rows:
        return []

    top_user, top_count = rows[0]
    cursor.execute("SELECT COUNT(*) FROM RFILocks")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT UserId) FROM RFILocks")
    active_users = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Users")
    total_users = cursor.fetchone()[0]

    return [Finding(
        title=f"{top_user} performs {100*top_count//total}% of all lock events",
        description=f"{top_user} has {top_count} lock events ({100*top_count//total}% of {total}) — significantly more than other users. Only {active_users} of {total_users} users have performed any lock events. This is a key-person dependency risk.",
        category="pattern",
        severity=0.6,
        specificity=default_specificity(f"{top_user}: {top_count}/{total} events ({100*top_count//total}%)"),
        surprise=0.6,
        query=sql,
        affected_tables=["Users", "RFILocks"],
        evidence=f"{top_user}: {100*top_count//total}% of all lock events",
    )]


def _rfi_state_distribution(conn) -> list:
    """Analyze distribution of RFI states."""
    sql = """SELECT RFIState, COUNT(*) as Count FROM RFIs GROUP BY RFIState ORDER BY RFIState"""
    cursor = conn.execute(sql)
    rows = cursor.fetchall()
    if not rows:
        return []

    cursor.execute("SELECT COUNT(*) FROM RFIs")
    total = cursor.fetchone()[0]

    # Find the most common state
    most_common_state, most_count = max(rows, key=lambda r: r[1])
    desc = f"State {most_common_state}"  # Simplified

    return [Finding(
        title=f"RFI state {most_common_state} is most common ({100*most_count//total}%)",
        description=f"Of {total} RFIs, {most_count} are in state {most_common_state} ({100*most_count//total}%). Distribution: {', '.join(f'State {r[0]}: {r[1]}' for r in rows)}. This concentration may indicate a bottleneck in the workflow.",
        category="pattern",
        severity=0.3,
        specificity=default_specificity(f"State {most_common_state}: {100*most_count//total}%"),
        surprise=0.3,
        query=sql,
        affected_tables=["RFIs"],
        evidence=f"Most common: state {most_common_state} ({100*most_count//total}%)",
    )]


def _common_workflow_paths(conn) -> list:
    """Find the most common RFI workflow paths from log types."""
    sql = """SELECT RFILogType, COUNT(*) as Count 
             FROM RFILogs 
             GROUP BY RFILogType 
             ORDER BY Count DESC 
             LIMIT 4"""
    cursor = conn.execute(sql)
    rows = cursor.fetchall()
    if not rows:
        return []

    cursor.execute("SELECT COUNT(*) FROM RFILogs")
    total = cursor.fetchone()[0]

    log_names = {1: "SignOff", 2: "Active", 3: "ActiveVerified", 4: "Complete", 5: "CompleteVerified", 6: "Rejected"}
    names = [f"{log_names.get(r[0], f'Type {r[0]}')} ({r[1]})" for r in rows]

    return [Finding(
        title=f"Most common RFI log type: {log_names.get(rows[0][0], 'Type '+str(rows[0][0]))} ({rows[0][1]} events)",
        description=f"Of {total} total RFI log entries, the distribution is: {', '.join(names)}. This reveals the dominant workflow path through the RFI lifecycle.",
        category="pattern",
        severity=0.2,
        specificity=default_specificity(f"Log types: {', '.join(names)}"),
        surprise=0.2,
        query=sql,
        affected_tables=["RFILogs"],
        evidence=f"Most common: {log_names.get(rows[0][0], str(rows[0][0]))} ({100*rows[0][1]//total}%)",
    )]
