# HMAS → Forrest Bridge: Technical Specification

## Overview
Extract real operational data from the OneTag HMAS Sydney database and structure it
as a Forrest scenario. The scenario optimizes RFI isolation sequencing to minimize
deadline risk.

## Data Flow

```
OneTag_Sydney (SQL Server)
  │
  ├── Area duration distributions (176 areas, 438K+ lock events)
  │     → Triangular(min, mode, max) per area
  │     → Stochastic simulation input
  │
  ├── RFI-job-isolation hierarchy (3,020 RFIs, 14,168 isolations)
  │     → Dependency graph for sequencing
  │     → Seed scenario definition
  │
  ├── Worker-lock assignments (47,779 events, 3,884 workers)
  │     → Resource allocation constraints
  │     → Productivity distributions
  │
  └── Vendor-job relationships (181 vendors, 9,718 jobs)
        → Vendor capacity constraints
        → Cost/quality tradeoffs
```

## Output Files

| File | Format | Description |
|------|--------|-------------|
| `scenario_seed.json` | JSON | Forrest scenario definition |
| `area_distributions.json` | JSON | Triangular params per area (176 areas) |
| `rfi_batch.json` | JSON | Top 20 RFIs with isolation graphs |
| `worker_productivity.json` | JSON | Worker speed distributions |
| `vendor_capacity.json` | JSON | Vendor job capacity data |

## Key Stats for Reference

- **131,849 lock events** in area 4-100-0-E alone (mode=76min, mean=253min)
- **176 isolation areas** with sufficient duration data
- **Top 5 areas** handle 45% of all isolations
- **2,471 completed RFIs** (state=11) for baseline comparison
- **Mean lock duration:** 200-400 minutes depending on area
- **Max recorded:** ~10,000 minutes (7 days) — likely multi-day jobs
