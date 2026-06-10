"""Anomaly detection passes — finds data integrity issues, gaps, and outliers."""

from ..findings import Finding
from ..scoring import score_finding, default_severity, default_specificity


def run(conn) -> list:
    """Run all anomaly detection passes."""
    findings = []
    findings.extend(_orphaned_fks(conn))
    findings.extend(_date_logic_errors(conn))
    findings.extend(_never_used_isolation_points(conn))
    findings.extend(_zero_duration_jobs(conn))
    findings.extend(_inconsistent_states(conn))
    return [score_finding(f) for f in findings]


def _orphaned_fks(conn) -> list:
    """Check for isolation points with no equipment links."""
    sql = """SELECT COUNT(DISTINCT ip.Id) 
             FROM IsolationPoints ip 
             LEFT JOIN EquipmentIsolations ei ON ei.IsolationPointId = ip.Id 
             WHERE ei.Id IS NULL"""
    cursor = conn.execute(sql)
    count = cursor.fetchone()[0]

    if count == 0:
        return []

    detail_sql = """SELECT ip.Name FROM IsolationPoints ip 
                    LEFT JOIN EquipmentIsolations ei ON ei.IsolationPointId = ip.Id 
                    WHERE ei.Id IS NULL LIMIT 5"""
    cursor = conn.execute(detail_sql)
    names = [row[0] for row in cursor.fetchall()]

    cursor = conn.execute("SELECT COUNT(*) FROM IsolationPoints")
    total = cursor.fetchone()[0]

    return [Finding(
        title=f"{count} isolation points have no equipment links",
        description=f"{count} of {total} isolation points ({100*count//total}%) are orphaned — no equipment is linked to them. This may indicate incomplete data entry or retired assets. Orphaned: {', '.join(names)}.",
        category="anomaly",
        severity=default_severity(count, total),
        specificity=default_specificity(f"{count} isolation points: {', '.join(names)}"),
        surprise=0.3,
        query=detail_sql,
        affected_tables=["IsolationPoints", "EquipmentIsolations"],
        evidence=f"{count} orphaned isolation points ({100*count//total}% of total)",
    )]


def _date_logic_errors(conn) -> list:
    """Check for RFIs where expected end date is before expected start date."""
    sql = """SELECT COUNT(*) FROM RFIs 
             WHERE ExpectedEndDate < ExpectedStartDate 
             AND ExpectedEndDate IS NOT NULL 
             AND ExpectedStartDate IS NOT NULL"""
    cursor = conn.execute(sql)
    count = cursor.fetchone()[0]

    if count == 0:
        return []

    detail_sql = """SELECT RFINumber, ExpectedStartDate, ExpectedEndDate 
                    FROM RFIs 
                    WHERE ExpectedEndDate < ExpectedStartDate LIMIT 5"""
    cursor = conn.execute(detail_sql)
    rows = cursor.fetchall()

    cursor = conn.execute("SELECT COUNT(*) FROM RFIs WHERE ExpectedEndDate IS NOT NULL")
    total = cursor.fetchone()[0]

    examples = "; ".join([f"{r[0]}: {r[1][:10]} → {r[2][:10]}" for r in rows])

    return [Finding(
        title=f"{count} RFIs have inverted date ranges",
        description=f"{count} of {total} dated RFIs have ExpectedEndDate before ExpectedStartDate. This data integrity issue could affect scheduling reports and duration calculations. Examples: {examples}.",
        category="anomaly",
        severity=default_severity(count, total),
        specificity=default_specificity(f"{count} RFIs with inverted dates: {examples}"),
        surprise=0.5,
        query=detail_sql,
        affected_tables=["RFIs"],
        evidence=f"{count} date-inverted RFIs out of {total}",
    )]


def _never_used_isolation_points(conn) -> list:
    """Find isolation points that have never been used in any RFI isolation."""
    sql = """SELECT COUNT(*) FROM IsolationPoints ip
             LEFT JOIN RFIIsolations ri ON ri.IsolationPointId = ip.Id
             WHERE ri.Id IS NULL"""
    cursor = conn.execute(sql)
    count = cursor.fetchone()[0]

    if count == 0:
        return []

    detail_sql = """SELECT ip.Name FROM IsolationPoints ip
                    LEFT JOIN RFIIsolations ri ON ri.IsolationPointId = ip.Id
                    WHERE ri.Id IS NULL LIMIT 5"""
    cursor = conn.execute(detail_sql)
    names = [row[0] for row in cursor.fetchall()]

    cursor = conn.execute("SELECT COUNT(*) FROM IsolationPoints")
    total = cursor.fetchone()[0]

    return [Finding(
        title=f"{count} isolation points have never been used",
        description=f"{count} of {total} isolation points ({100*count//total}%) have never been referenced in any RFI isolation. These may be legacy points or safety assets awaiting first use. Unused: {', '.join(names)}.",
        category="anomaly",
        severity=default_severity(count, total) * 0.7,
        specificity=default_specificity(f"{count} unused points: {', '.join(names)}"),
        surprise=0.4,
        query=detail_sql,
        affected_tables=["IsolationPoints", "RFIIsolations"],
        evidence=f"{count} unused isolation points ({100*count//total}%)",
    )]


def _zero_duration_jobs(conn) -> list:
    """Find RFIJobs where all dates are identical (instant completion)."""
    sql = """SELECT COUNT(*) FROM RFIJobs 
             WHERE LinkingDate = WorkCompleteDate
             AND LinkingDate IS NOT NULL"""
    cursor = conn.execute(sql)
    count = cursor.fetchone()[0]

    if count == 0:
        return []

    cursor = conn.execute("SELECT COUNT(*) FROM RFIJobs WHERE WorkCompleteDate IS NOT NULL")
    total = cursor.fetchone()[0]

    return [Finding(
        title=f"{count} jobs completed instantly",
        description=f"{count} of {total} completed RFI jobs ({100*count//total}%) have identical start and completion dates. This may indicate batch data entry or placeholder records rather than actual work events.",
        category="anomaly",
        severity=default_severity(count, total) * 0.6,
        specificity=0.3,
        surprise=0.4,
        query=sql,
        affected_tables=["RFIJobs"],
        evidence=f"{count} zero-duration jobs out of {total}",
    )]


def _inconsistent_states(conn) -> list:
    """Check for RFIs in state > 0 with no associated logs."""
    sql = """SELECT COUNT(*) FROM RFIs r
             LEFT JOIN RFILogs l ON l.RFIId = r.Id
             WHERE l.Id IS NULL AND r.RFIState > 0"""
    cursor = conn.execute(sql)
    count = cursor.fetchone()[0]

    if count == 0:
        return []

    detail_sql = """SELECT r.RFINumber, r.RFIState FROM RFIs r
                    LEFT JOIN RFILogs l ON l.RFIId = r.Id
                    WHERE l.Id IS NULL AND r.RFIState > 0 LIMIT 5"""
    cursor = conn.execute(detail_sql)
    rfis = [f"{r[0]} (state {r[1]})" for r in cursor.fetchall()]

    cursor = conn.execute("SELECT COUNT(*) FROM RFIs WHERE RFIState > 0")
    total = cursor.fetchone()[0]

    return [Finding(
        title=f"{count} RFIs have no audit trail",
        description=f"{count} of {total} active RFIs have zero log entries. Without audit logs, there is no record of approvals, isolations, or status changes — a significant gap for compliance tracking. Affected: {', '.join(rfis)}.",
        category="anomaly",
        severity=default_severity(count, total),
        specificity=default_specificity(f"{count} RFIs: {', '.join(rfis)}"),
        surprise=0.6,
        query=detail_sql,
        affected_tables=["RFIs", "RFILogs"],
        evidence=f"{count} RFIs with no audit trail out of {total}",
    )]
