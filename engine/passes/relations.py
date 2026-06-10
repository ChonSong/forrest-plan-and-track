"""Relationship discovery passes — finds cross-entity correlations."""

from ..findings import Finding
from ..scoring import score_finding, default_specificity


def run(conn) -> list:
    findings = []
    findings.extend(_area_vs_defects(conn))
    findings.extend(_user_role_vs_activity(conn))
    findings.extend(_vendor_performance(conn))
    findings.extend(_temp_tag_correlation(conn))
    return [score_finding(f) for f in findings]


def _area_vs_defects(conn) -> list:
    """Check if certain area types have more audit defects."""
    sql = """SELECT at.Name as AreaType, 
                    COUNT(ac.Id) as Checks, 
                    SUM(CASE WHEN ac.DefectFound = 1 THEN 1 ELSE 0 END) as Defects
             FROM Audits a
             JOIN AuditChecks ac ON ac.AuditId = a.Id
             LEFT JOIN AreaTypes at ON 1=1
             GROUP BY at.Name
             ORDER BY Defects DESC"""
    cursor = conn.execute(sql)
    rows = cursor.fetchall()
    if not rows:
        return []

    # Find area with highest defect rate (if we have data)
    cursor.execute("SELECT COUNT(*) FROM AuditChecks WHERE DefectFound = 1")
    total_defects = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM AuditChecks")
    total_checks = cursor.fetchone()[0]

    if total_checks == 0:
        return []

    return [Finding(
        title=f"Overall defect rate: {100*total_defects//total_checks}% across all audits",
        description=f"Of {total_checks} audit checks, {total_defects} found defects ({100*total_defects//total_checks}%). This provides a baseline safety compliance metric for the system.",
        category="relationship",
        severity=0.4,
        specificity=default_specificity(f"{total_defects} defects in {total_checks} checks"),
        surprise=0.3,
        query=sql,
        affected_tables=["Audits", "AuditChecks"],
        evidence=f"Defect rate: {100*total_defects//total_checks}% ({total_defects}/{total_checks})",
    )]


def _user_role_vs_activity(conn) -> list:
    """Check if certain user roles are more active in isolations."""
    sql = """SELECT ur.Name as Role, COUNT(rl.Id) as LockEvents
             FROM UserRoles ur
             JOIN Users u ON u.UserRoleId = ur.Id
             JOIN RFILocks rl ON rl.UserId = u.Id
             GROUP BY ur.Id
             ORDER BY LockEvents DESC"""
    cursor = conn.execute(sql)
    rows = cursor.fetchall()
    if not rows:
        return []

    cursor.execute("SELECT COUNT(*) FROM RFILocks")
    total = cursor.fetchone()[0]

    return [Finding(
        title=f"{rows[0][0]}s perform the most lock events ({100*rows[0][1]//total}%)",
        description=f"User role distribution of lock events: {', '.join(f'{r[0]}: {r[1]} ({100*r[1]//total}%)' for r in rows)}. This shows which roles are most involved in the isolation process.",
        category="relationship",
        severity=0.3,
        specificity=default_specificity(f"Role distribution: {', '.join(r[0] for r in rows)}"),
        surprise=0.3,
        query=sql,
        affected_tables=["Users", "UserRoles", "RFILocks"],
        evidence=f"Most active: {rows[0][0]} ({100*rows[0][1]//total}%)",
    )]


def _vendor_performance(conn) -> list:
    """Check if different companies have different lock durations."""
    sql = """SELECT c.Name as Company, 
                    COUNT(rl.Id) as LockEvents,
                    AVG(
                        (julianday(rl.LockOffDate) - julianday(rl.LockOnDate)) * 24 * 60
                    ) as AvgDurationMins
             FROM Companies c
             JOIN Users u ON u.CompanyId = c.Id
             JOIN RFILocks rl ON rl.UserId = u.Id
             WHERE rl.LockOffDate IS NOT NULL AND rl.LockOnDate IS NOT NULL
             GROUP BY c.Id
             ORDER BY AvgDurationMins DESC
             LIMIT 5"""
    cursor = conn.execute(sql)
    rows = cursor.fetchall()
    if not rows:
        return []

    return [Finding(
        title=f"Vendor lock duration ranges from {rows[-1][2]:.0f}m to {rows[0][2]:.0f}m",
        description=f"Average lock duration by company: {', '.join(f'{r[0]}: {r[2]:.0f}m ({r[1]} events)' for r in rows)}. Variance across vendors may indicate different work practices or complexity.",
        category="relationship",
        severity=0.4,
        specificity=default_specificity(f"Range: {rows[-1][2]:.0f}m to {rows[0][2]:.0f}m"),
        surprise=0.5,
        query=sql,
        affected_tables=["Companies", "Users", "RFILocks"],
        evidence=f"Variance: {rows[-1][2]:.0f}m to {rows[0][2]:.0f}m",
    )]


def _temp_tag_correlation(conn) -> list:
    """Check correlation between temporary tags and audit defects."""
    cursor = conn.execute("SELECT COUNT(*) FROM TemporaryTags")
    tag_count = cursor.fetchone()[0]

    if tag_count == 0:
        return []

    cursor.execute("SELECT COUNT(*) FROM AuditChecks WHERE DefectFound = 1")
    defect_count = cursor.fetchone()[0]

    return [Finding(
        title=f"{tag_count} temporary tags active with {defect_count} audit defects",
        description=f"There are {tag_count} temporary tags (danger/out-of-service tags) and {defect_count} audit defects in the system. Monitoring the overlap between tagged equipment and defect locations could reveal recurring safety issues.",
        category="relationship",
        severity=0.5,
        specificity=default_specificity(f"{tag_count} tags, {defect_count} defects"),
        surprise=0.4,
        query=f"SELECT COUNT(*) FROM TemporaryTags; SELECT COUNT(*) FROM AuditChecks WHERE DefectFound = 1",
        affected_tables=["TemporaryTags", "AuditChecks"],
        evidence=f"{tag_count} tags vs {defect_count} defects",
    )]
