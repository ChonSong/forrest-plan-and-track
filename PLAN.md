# Build Plan — Forrest Data Analysis Engine

> **Goal:** Transform the Forrest concept from a Claude-driven simulation loop into a working data analysis engine over the OneTag HMAS database — no API keys, no external services, just structured analysis.

## Overview

| Phase | Theme | Key Output |
|-------|-------|------------|
| 1 | Foundation | Clone, schema, seeded SQLite database |
| 2 | Redefine | FORREST-MODEL.md → Query→Analyze→Rank loop |
| 3 | Build engine | Analysis passes (anomalies, patterns, relations, stats) |
| 4 | Dashboard | Forrest Findings page in Streamlit |
| 5 | Ship | Updated docs, commit, push |

## Phase 1 — Foundation

**Goal:** Clone repo, create SQL database with seed data.

- Clone `ChonSong/forrest-plan-and-track`
- Convert Prisma schema to SQLite (103 tables, no relation fields)
- Write schema-aware seed script that auto-fills NOT NULL columns
- Populate: 50 RFIs, 40 jobs, 12 users, 30 padlocks, 256 RFI logs, 500 event logs
- Verify dashboard queries return data

**Key files created:**
- `prisma/schema.sqlite.sql` — SQLite DDL
- `scripts/seed_data.py` — Schema-aware seed script
- `data/onetag.db` — Seeded SQLite database (1.4 MB)

## Phase 2 — Redefine the Engine

**Goal:** Rewrite docs to describe a data analysis engine, not a Claude simulation.

- `FORREST-MODEL.md` — Query→Analyze→Rank loop, 4 finding categories, scoring model
- `SCENARIO.md` — OneTag HMAS domain: RFIs, isolation points, audits, work permits
- Restructured from "Monte Carlo + Claude" to "SQL + pandas + statistics"

## Phase 3 — Build the Engine

**Goal:** Working analysis package that produces findings.

- `engine/runner.py` — Auto-discovers passes, runs all, collects findings
- `engine/findings.py` — Finding dataclass with title, description, score, query
- `engine/scoring.py` — 0.5×severity + 0.3×specificity + 0.2×surprise
- `engine/passes/anomalies.py` — Orphaned FKs, date errors, silent RFIs
- `engine/passes/patterns.py` — Usage hotspots, peak periods, workflow paths
- `engine/passes/relations.py` — Area vs defects, vendor performance, role activity
- `engine/passes/stats.py` — Lock duration dist, utilization, workload balance

**Run:** `python -m engine.runner --top 5`

## Phase 4 — Dashboard Integration

**Goal:** Findings visible in the Streamlit dashboard.

- Added "🚀 Forrest Findings" page to sidebar + router
- Connects to local SQLite DB (not SQL Server)
- Buttons to run analysis, slider for N findings
- Each finding: severity badge, progress bars, SQL query disclosure
- Cached results with manual "Run Analysis" trigger

## Phase 5 — Ship

**Goal:** Repo is self-documenting, all changes pushed.

- `PROGRESS.md` — Full status board with metrics
- `README.md` — Updated mission, structure, how-to-run, success criteria
- All commits pushed to `ChonSong/forrest-plan-and-track`

## What We Didn't Do

- No Claude API integration (no key available)
- No Monte Carlo simulation (not applicable to static data)
- No Next.js web app (the engine is Python, not TypeScript)
- No Docker deployment (runs from CLI directly)

## Future Ideas

- **More analysis passes:** Check for duplicate users, similar isolation point names, temporal clustering
- **Export to CSV/notebook:** Findings as Jupyter notebook output
- **Schedule analysis:** Cron job runs analysis nightly, latest findings on dashboard
- **Cross-dataset analysis:** Compare two databases for differences
- **Prediction:** Use historical patterns to predict isolation duration outliers
