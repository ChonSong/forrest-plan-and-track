# Experiment Run: [RUN NAME]

> **Date:** YYYY-MM-DD
> **Day:** Day N
> **Type:** [Smoke / Tuning / Dress / Final]
> **Scenario:** [Scenario name]

## Configuration

| Parameter | Value |
|-----------|-------|
| maxExperiments | |
| simsPerExpt | |
| mutationSpace | |
| objective | |
| constraints | |

## Results

| Metric | Value |
|--------|-------|
| Total experiments | |
| Accepted | |
| Rejected | |
| Acceptance rate | |
| Baseline score | |
| Best score | |
| Improvement | |
| Run duration | |
| API cost (est.) | |

## Best-Score Trajectory

> Paste or describe the score-over-iteration chart.

```
Iteration:  1   50   100   150   200
Score:      X    X     X     X     X
```

## Findings

### Finding 1 (Rank #1)
> [Plain-language finding]

**Quantified impact:** [Specific number]
**Lineage:** Experiments #[X, Y, Z] led to this finding.
**Mutation:** [What changed]

### Finding 2 (Rank #2)
> [Plain-language finding]

**Quantified impact:** [Specific number]
**Lineage:** Experiments #[X, Y, Z] led to this finding.

### Finding 3 (Rank #3)
> [Plain-language finding]

**Quantified impact:** [Specific number]
**Lineage:** Experiments #[X, Y, Z] led to this finding.

## Analysis

### What Worked
- [What improved the score]
- [Which mutations were accepted]

### What Didn't Work
- [What was rejected]
- [What looked promising but failed]

### Acceptance Rate Diagnosis
- [ ] 10-40%: Healthy
- [ ] >40%: Mutation space too generous — tighten
- [ ] <10%: Too tight or noisy objective — loosen or sharpen

### Next Steps
- [What to change for the next run]
- [What to keep]
- [What to investigate]

## Raw Data

> Link to Prisma Studio export or attach key tables if needed.
