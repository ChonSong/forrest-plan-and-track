# Demo Scenario: Critical Path Under Uncertainty

> Project scheduling — the most legible, stochastic, surprising domain for an intern demo.

## One-Sentence Problem

**A 12-task project has uncertain durations — which task's uncertainty matters most for on-time delivery?**

## Why This Scenario

| Trait | Assessment |
|-------|-----------|
| **Legible** | ✅ Every PM, engineer, and stakeholder understands "some tasks take longer than expected." One sentence, no jargon. |
| **Stochastic** | ✅ Task durations are inherently uncertain. Monte Carlo simulation is the natural tool — not a forced fit. |
| **Surprising** | ✅ Forrest may find that the critical path isn't what the Gantt chart says, or that adding resources to the "obvious" bottleneck doesn't help, or that one specific task's variance dominates all others. |
| **Safe** | ✅ Fully synthetic data. No NDA, no customer data, no external feeds. |

## Scenario Parameters

### Project: "Website Redaunch"

A simplified but realistic 12-task project with dependencies.

```
Task  Duration (days)  Dependencies  Resources
────  ───────────────  ────────────  ─────────
T1    3-5-7            -             1 dev
T2    2-3-5            -             1 dev
T3    1-2-3            T1            1 designer
T4    4-6-10           T1, T2        2 devs
T5    2-3-4            T2            1 dev
T6    1-2-4            T3, T4        1 designer
T7    3-4-6            T4            2 devs
T8    2-3-5            T5            1 dev
T9    1-2-3            T6, T7        1 QA
T10   2-4-6            T7, T8        1 QA
T11   1-1-2            T9, T10       1 PM
T12   1-2-3            T11           1 dev
```

*Duration format: min-mode-max (PERT-style triangular distribution)*

### Dependency DAG

```
T1 ──┬── T3 ──┬── T6 ──┬── T9 ──┬── T11 ── T12
     │        │        │        │
T2 ──┴── T4 ──┘        │        │
     │        │        │        │
     └── T5 ──┴── T8 ──┴── T10 ─┘
              │
              └── T7 ─────────────┘
```

### Constraints

| Constraint | Type | Value |
|-----------|------|-------|
| Deadline | **Hard** | 28 days |
| Max concurrent devs | **Hard** | 3 |
| Max concurrent designers | **Hard** | 2 |
| Max concurrent QA | **Hard** | 2 |
| Prefer fewer resource switches | Soft | Minimize handoffs |

### Objective

**Minimize probability of missing the 28-day deadline.**

(Forrest minimizes by default, so the objective function should be: `P(makespan > 28)` — the probability of failure. Lower is better.)

### Mutation Space

Forrest can mutate:

| Variable | Range | Notes |
|----------|-------|-------|
| Task duration estimates | ±20% of current min/mode/max | The core uncertainty |
| Resource allocation | 1-3 devs per dev task | More resources = faster but higher cost |
| Task parallelism | Relax non-critical dependencies | Can T5 start before T2 finishes? |
| Buffer insertion | 0-3 days on critical path tasks | Explicit contingency |

### What "Success" Looks Like

A non-technical viewer reads the three findings and says:

> *"So the bottleneck isn't the longest task — it's the task with the most uncertain duration on the critical path. And adding a second developer to T4 only helps if we also reduce T7's variance. That's actually useful — I'd act on that."*

### What Would Surprise Us

- The critical path shifts depending on which tasks are delayed (non-static critical path)
- Adding resources to the longest task doesn't help because variance elsewhere dominates
- The optimal strategy is to add buffer to one specific task, not spread contingency evenly
- A non-critical task becomes critical in >30% of simulations (near-critical path)

## Forrest Configuration

```json
{
  "maxExperiments": 200,
  "simsPerExpt": 500,
  "objective": "minimize P(makespan > 28 days)",
  "mutationSpace": {
    "taskDurations": "±20% triangular",
    "resourceAllocation": "1-3 devs per task",
    "dependencyRelaxation": "boolean per non-critical dep",
    "bufferInsertion": "0-3 days on critical path"
  },
  "constraints": {
    "deadline": "28 days (hard)",
    "maxConcurrentDevs": 3,
    "maxConcurrentDesigners": 2,
    "maxConcurrentQA": 2
  }
}
```

## Seed Data Source

All numbers are synthetic, inspired by publicly available project management case studies (PMI PMBOK examples, open-source project post-mortems). No real customer data used.

## Approval Status

- [ ] Brief reviewed by manager/team
- [ ] Scenario entered into Forrest
- [ ] First tuning run launched
