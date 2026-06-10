# Forrest Plan & Track

> **Mission:** Transform Forrest from a Claude-driven simulation concept into a working data analysis engine over the OneTag HMAS database. No API keys. No external services. Just structured analysis over real industrial data.

## The Promise

Your schema loads once. Forrest runs it in 0.1 seconds. Three findings emerge.

## North Star

A non-technical viewer should be able to read the three findings and say *"that's actually useful — I'd act on that."* Plain language beats clever modelling.

## Repo Structure

```
forrest-plan-and-track/
├── README.md              ← You are here
├── PLAN.md                ← Full plan (updated for data analysis)
├── FORREST-MODEL.md       ← Engine: Query→Analyze→Rank loop
├── SCENARIO.md            ← OneTag HMAS domain description
├── DEMO.md                ← Demo day presentation outline
├── PROGRESS.md            ← Running status board
├── data/
│   └── onetag.db          ← SQLite database (seeded sample data)
├── engine/
│   ├── runner.py          ← Main entry point
│   ├── findings.py        ← Finding data model
│   ├── scoring.py         ← Finding scoring
│   └── passes/
│       ├── anomalies.py   ← Data integrity checks
│       ├── patterns.py    ← Usage pattern recognition
│       ├── relations.py   ← Cross-entity correlations
│       └── stats.py       ← Statistical distributions
├── streamlit_onetag/
│   └── app.py             ← Dashboard with "🚀 Forrest Findings" page
├── prisma/
│   ├── schema.prisma      ← Full OneTag data model
│   └── schema.sqlite.sql  ← SQLite CREATE TABLE statements
├── scripts/
│   └── seed_data.py       ← Database seed script
├── diagrams/              ← Mermaid + HTML visualizations
├── experiments/           ← Experiment log templates
├── daily-logs/            ← Daily standup templates
└── notes/                 ← Analysis notes and gotchas
```

## Status

| Phase | Status |
|-------|--------|
| Foundation (schema + seed data) | ✅ Complete |
| Engine concept rewrite | ✅ Complete |
| Analysis engine (4 pass categories) | ✅ Complete |
| Dashboard integration (Findings page) | ✅ Complete |
| Documentation | ✅ Complete |

## How to Run

```bash
# 1. Seed the database
python scripts/seed_data.py

# 2. Run the analysis engine (CLI)
python -m engine.runner --top 5
python -m engine.runner --top 3 --json

# 3. Launch the dashboard
# (requires SQL Server connection for existing pages,
#  findings page uses local SQLite)
cd streamlit_onetag && streamlit run app.py
```


## Success Criteria

| Level | Criteria |
|-------|----------|
| **Baseline** | Analysis runs without errors. At least one finding generated. |
| **Target** | 3+ non-trivial findings per run. Findings are specific, quantified, and legible. |
| **Stretch** | A finding reveals something genuinely unexpected about the data model or domain. |

---

*This repo is the single source of truth for the Forrest/HMAS project.*
