# Forrest — Data Analysis Engine

> Read this before touching any code. This is the product.

## What Forrest Is

Forrest is a **structured data analysis engine** that runs analysis passes over the OneTag HMAS database, scores each finding by anomaly severity or statistical significance, and surfaces the top findings in plain language.

Each "experiment" is one analysis pass. The loop runs N passes, and at the end, the top findings are extracted for the dashboard to display.

No LLM API keys needed. No external services. Everything runs locally on the seeded SQLite database.

## The Loop

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│   ┌──────────┐    ┌───────────┐    ┌──────────┐         │
│   │  QUERY   │───▶│  ANALYZE  │───▶│   RANK   │         │
│   │          │    │           │    │          │         │
│   │ SQL /    │    │ pandas /  │    │ Score by │         │
│   │ pandas   │    │ stats     │    │ anomaly  │         │
│   │ fetch    │    │ compute   │    │ severity │         │
│   │ data     │    │ metric    │    │          │         │
│   └──────────┘    └───────────┘    └────┬─────┘         │
│                                         │               │
│                                         ▼               │
│                                ┌──────────────┐        │
│                                │  FINDING OR   │        │
│                                │  DISCARD      │        │
│                                │              │        │
│                                │ Metric beats │        │
│                                │ threshold →  │        │
│                                │ log finding  │        │
│                                │              │        │
│                                │ Otherwise →  │        │
│                                │ keep for     │        │
│                                │ context      │        │
│                                └──────┬───────┘        │
│                                       │                 │
│                                       ▼                 │
│                                ┌──────────────┐        │
│                                │   REPEAT     │        │
│                                │  N analysis  │        │
│                                │   passes     │        │
│                                └──────────────┘        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Analysis Pass Categories

| Category | What It Looks For | Example Finding |
|----------|------------------|-----------------|
| **Anomalies** | Orphaned FK values, date logic errors, missing data | "15 RFIs have isolation points applied before the RFI was created" |
| **Patterns** | Usage trends, peak periods, most common actions | "Valve PV-101 is the most-isolated point: 23 RFIs in 6 months" |
| **Relationships** | Cross-entity correlations | "High-risk areas have 3x more audit defects than standard areas" |
| **Statistics** | Distributions, percentiles, outlier detection | "95th percentile lock duration is 8h — 3 outliers exceed 24h" |

## Finding Format

Each finding is a structured object:

```
{
  title: "string — one-line summary",
  description: "string — 2-3 sentence plain-language explanation",
  score: float — 0.0 to 1.0 (anomaly severity / significance),
  category: "anomaly" | "pattern" | "relationship" | "statistic",
  query: "SQL that produced this finding",
  affected_tables: ["table1", "table2"],
  evidence: "chart title or metric value"
}
```

## The Four Entities

| Entity | What It Is | You'll Touch It When... |
|--------|-----------|------------------------|
| **Scenario** | The OneTag HMAS domain — the database schema + domain context | Understanding the data model |
| **Run** | One execution of all analysis passes | Kicking off / monitoring analysis |
| **Experiment** | One analysis pass. Query, metric, score | Debugging why a pass returned weak findings |
| **Finding** | One of the top N surfaced insights | Reviewing dashboard output |

## Scoring Model

Findings are scored on three dimensions:

1. **Severity (0-1):** How anomalous or impactful is this? (Borken FK = 0.9, minor trend = 0.2)
2. **Specificity (0-1):** How precise is the evidence? ("Valve PV-101" = 0.9, "Some valves" = 0.3)
3. **Surprise (0-1):** Would a human expect this? (Unexpected correlation = 0.8, obvious = 0.1)

**Final score = 0.5 × Severity + 0.3 × Specificity + 0.2 × Surprise**

Passes whose score exceeds the threshold (0.4) graduate to findings.

## Key Files

| File | What It Does | 
|------|-------------|
| `prisma/schema.prisma` | Complete OneTag data model (80+ tables) |
| `data/onetag.db` | SQLite database with seeded sample data |
| `engine/passes/anomalies.py` | Anomaly detection passes |
| `engine/passes/patterns.py` | Pattern recognition passes |
| `engine/passes/relations.py` | Cross-entity correlation passes |
| `engine/passes/stats.py` | Statistical analysis passes |
| `engine/runner.py` | Main loop: run all passes, collect findings |
| `engine/scoring.py` | Score each finding on severity, specificity, surprise |
| `streamlit_onetag/app.py` | Dashboard — findings + data exploration |

## The Product Story

> One command runs all analysis. N passes run, 3 findings emerge.

The value proposition: you describe the database schema once, and Forrest autonomously explores the data through structured analysis passes, finding non-obvious patterns and anomalies that a human would take days to discover manually. The top findings are surfaced in the dashboard — plain language, actionable, surprising.
