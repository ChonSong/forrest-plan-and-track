# Forrest Plan & Track

> **Mission:** Prove that Forrest — an autonomous Monte Carlo optimization engine — can find non-obvious, actionable insights on a scenario nobody on the team has touched. Two weeks. 200 experiments. Three findings. One 15-minute share-out.

## The Promise

Your plan runs once. Forrest runs it 10,000 times.

## North Star

At the end of two weeks, a non-technical viewer should be able to read your three findings and say *"that's actually useful — I'd act on that."* Plain language beats clever modelling.

## Repo Structure

```
forrest-plan-and-track/
├── README.md              ← You are here
├── PLAN.md                ← Full 14-day plan with daily tasks
├── FORREST-MODEL.md       ← Mental model of the engine (read before coding)
├── SCENARIO.md            ← Demo scenario brief (project scheduling)
├── DEMO.md                ← Demo day presentation outline
├── PROGRESS.md            ← Running status board (update daily)
├── diagrams/
│   ├── engine-loop.html   ← Interactive engine loop visualization
│   ├── data-model.html    ← 4-entity data model
│   └── timeline.html      ← 14-day Gantt-style timeline
├── experiments/
│   ├── TEMPLATE.md        ← Copy for each run
│   ├── run-001-smoke.md   ← Day 2: 50-experiment smoke test
│   ├── run-002-tuning-1.md
│   ├── run-003-tuning-2.md
│   ├── run-004-tuning-3.md
│   ├── run-005-dress.md
│   ├── run-006-final-1.md ← Day 8: First 200-experiment run
│   └── run-007-final-2.md ← Day 10: Confidence check
├── daily-logs/
│   ├── TEMPLATE.md        ← Daily standup log template
│   ├── day-00.md
│   ├── day-01.md
│   └── ...
│   └── day-14.md
└── notes/
    ├── code-tour.md       ← Notes from reading the codebase
    ├── gotchas.md         ← Things that have bitten
    ├── tuning-log.md      ← What you changed and why
    └── three-things.md    ← Week 1 review prep (fragile things, unknowns, assumptions)
```

## Status

| Phase | Target | Status |
|-------|--------|--------|
| Day 0: Read & prep | Notebook ready | ⬜ Not started |
| Day 1: Environment | Forrest running locally | ⬜ Not started |
| Day 2: Smoke test | 50-experiment run complete | ⬜ Not started |
| Day 3: Scenario brief | Brief written & approved | ⬜ Not started |
| Day 4-7: Tuning | 4 tuning runs, story emerging | ⬜ Not started |
| Day 8-10: Final runs | 2× 200-experiment runs | ⬜ Not started |
| Day 11-13: Polish | Presentation rehearsed | ⬜ Not started |
| Day 14: Demo day | 15-min share-out | ⬜ Not started |

## Key Resources

- **Forrest engine repo:** `git@github.com:<TBD>/forrest.git` *(org name pending)*
- **API key:** Request from #forrest-eng *(sandbox key with per-day spend cap)*
- **Budget:** $50 for two weeks
- **In-repo docs:** `AGENTS.md` (Next.js 16 deltas), `README.md`, `/security` page

## Success Criteria

| Level | Criteria |
|-------|----------|
| **Baseline** | It runs. One scenario, one full run, three findings rendered. No crashes. |
| **Target** | It tells a story. Findings are specific, quantified, legible. Improvement vs baseline is non-trivial and explained. |
| **Stretch** | It changes how we think. A finding surprises the team enough to spark a follow-up. |
| **Bonus** | Left tooling behind. A PR, seed scenario, tuning notebook, or docs improvement. |

---

*This repo is the single source of truth for the two-week mission. Update PROGRESS.md daily. Log every experiment. Write findings in plain language.*
