# Scenario: OneTag HMAS Sydney

> **HMAS** — Health, Safety, Environmental, Asset Management system for industrial safety.

## One-Sentence Problem

**A complex industrial safety system (80+ tables, 248 relationships) tracks isolations, permits, audits, and work orders — which patterns and anomalies in this data reveal hidden safety risks or operational inefficiencies?**

## Why This Scenario

| Trait | Assessment |
|-------|-----------|
| **Real** | ✅ Derived from a 2.5GB production SQL Server backup. Real schema, realistic data. |
| **Rich** | ✅ 80+ tables covering isolations, RFIs, work permits, audits, lockout/tagout, temporary tags, user management. |
| **Analyzable** | ✅ The data model naturally produces interesting queries: FK gaps, date anomalies, utilization patterns. |
| **Safe** | ✅ Fully anonymized seed data. No PII. No production records. |
| **No API key needed** | ✅ Everything runs locally on SQLite. No LLM calls, no external services. |

## Domain Overview

The OneTag system manages **isolation of hazardous energy** in industrial environments (offshore platforms, refineries, chemical plants). Key processes:

### 1. RFI Lifecycle (Request for Isolation)
```
Request → Develop → Isolate → Work → Remove Isolation → Close
```
Each RFI can have multiple isolation points, jobs, locks, and log entries.

### 2. Isolation Management
Equipment has physical isolation points (breakers, valves, blinds). Each isolation point can be locked/tagged with padlocks. The system tracks which points are isolated, by whom, and when.

### 3. Work Permits
Hot work, cold work, confined space, working at height — each requires a permit linked to RFIs and jobs.

### 4. Audits & Inspections
Safety audits check isolation points for compliance. Defects can be reported and tracked.

### 5. Temporary Tags
Danger tags and out-of-service tags attached to equipment during maintenance.

## Key Entities (The "Big 6")

| Entity | What It Is | Volume |
|--------|-----------|--------|
| **RFIs** | Requests for Isolation — the core work request | 50 |
| **IsolationPoints** | Physical points where energy is isolated (valves, breakers) | 10 |
| **Jobs** | Work orders linked to RFIs | 40 |
| **Users** | Operators, supervisors, safety officers | 12 |
| **Audits** | Safety inspection events | 15 |
| **WorkPermits** | Authorizations for hazardous work | 25 |

## Interesting Analysis Questions

### Anomaly Detection
- Are there isolation points that are never used? (Underutilized asset)
- Are there RFIs with isolation dates before the RFI creation date? (Data integrity)
- Are there orphaned FK references? (Missing data)
- Are there jobs completed before they were started? (Date logic errors)
- What's the distribution of lock durations? (Outlier detection)

### Pattern Recognition
- Which isolation points are used most frequently? (Hot spots)
- What's the peak hour/day for isolation activity? (Workload patterns)
- Which users perform the most isolations? (Key person dependency)
- What's the most common RFI workflow path? (Process analysis)

### Relationship Discovery
- Do high-risk areas have more audit defects? (Risk correlation)
- Is there a relationship between isolation duration and audit findings? (Process quality)
- Do certain companies/vendors have longer lock durations? (Vendor performance)
- Is there a correlation between temporary tags and audit defects? (Safety indicators)

### Statistical Analysis
- Distribution of RFI duration (expected vs actual)
- Isolation point utilization rates
- Audit defect rates by area type
- Work permit state distribution

## Data Model

The full Prisma schema is at `prisma/schema.prisma` (80+ models). The SQLite database at `data/onetag.db` contains seeded sample data.

Key relationships:

```
Groups ──┬── Systems ── Equipment ── IsolationPoints
          └── Areas ──── IsolationPoints
          
RFIs ──┬── RFIIsolations ── IsolationPoints
       ├── RFIJobs ──────── Jobs
       ├── RFILocks ─────── PadLocks
       └── RFILogs

Audits ──── AuditChecks
RFIs ──── WorkPermits
IsolationPoints ── TemporaryTags
```

## Success Criteria

| Level | Criteria |
|-------|----------|
| **Baseline** | Analysis runs without errors. At least one finding generated. |
| **Target** | 3+ non-trivial findings per run. Findings are specific, quantified, and legible. |
| **Stretch** | A finding reveals something genuinely unexpected about the data model or domain. |
