# Progress Board

> Update this file daily. Single source of truth for mission status.

## Status: 🟡 In Progress

**Current phase:** Day 0 — Planning & repo setup
**Started:** 2026-06-01
**Target completion:** 2026-06-14

## Phase Tracker

| # | Phase | Days | Status | Notes |
|---|-------|------|--------|-------|
| 0 | Read & prep | Day 0 | 🔵 Complete | Plan repo created |
| 1 | Environment setup | Day 1 | ⬜ Not started | Blocked: repo URL, API key |
| 2 | Code tour + smoke test | Day 2 | ⬜ Not started | |
| 3 | Scenario selection | Day 3 | ⬜ Not started | |
| 4-7 | Tuning & iteration | Day 4-7 | ⬜ Not started | |
| 8-10 | Final runs | Day 8-10 | ⬜ Not started | |
| 11-13 | Polish & rehearse | Day 11-13 | ⬜ Not started | |
| 14 | Demo day | Day 14 | ⬜ Not started | |

## Blockers

| Blocker | Status | Action Needed |
|---------|--------|--------------|
| Forrest repo URL (`<org>`) | 🔴 Blocking Day 1 | Confirm org name |
| Anthropic API key | 🔴 Blocking Day 1 | Request from #forrest-eng |
| Team channels (Slack) | 🟡 Partial | Hybrid mode — some real, some self-managed |

## Experiment Log Summary

| Run | Day | Expts | Sims/Expt | Status | Cost | Key Finding |
|-----|-----|-------|-----------|--------|------|-------------|
| 001 | 2 | 50 | 500 | ⬜ | — | Smoke test |
| 002 | 4 | 50 | 200 | ⬜ | — | Tuning #1 |
| 003 | 5 | 50 | 200 | ⬜ | — | Tuning #2 |
| 004 | 6 | 50 | 200 | ⬜ | — | Tuning #3 |
| 005 | 7 | 50 | 500 | ⬜ | — | Dress rehearsal |
| 006 | 8 | 200 | 500 | ⬜ | — | Final #1 |
| 007 | 10 | 200 | 500 | ⬜ | — | Final #2 |

**Total estimated cost:** ~$8-12 (well within $50 budget)

## Key Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-01 | Domain: Project scheduling (critical path) | Most legible, naturally stochastic, surprising findings possible |
| 2026-06-01 | Repo: `ChonSong/forrest-plan-and-track` (public) | Transparency, shareable |
| 2026-06-01 | Diagrams: Mermaid + HTML | Native Markdown rendering + rich visuals |
| 2026-06-01 | Experiment log: Full (scores, findings, lineage) | Maximum reproducibility and learning |

## Week 1 Review Prep

### Three Things Notebook

#### (a) Things I Don't Understand
- [ ] How does the engine decide which mutation to propose next? (Random? Heuristic? LLM-driven?)
- [ ] What's the acceptance tolerance? (How much better must a score be to commit?)
- [ ] How are findings extracted from the experiment log? (Dedicated Claude call? Template?)

#### (b) Things That Look Fragile
- [ ] The loop runs server-side — what happens if the dev server restarts mid-run?
- [ ] Prisma SQLite — concurrent access from dashboard polling + engine writes?
- [ ] Claude API rate limits during a 200-experiment run?

#### (c) Assumptions Baked Into the Engine
- [ ] Forrest minimizes by default — objectives must be signed correctly
- [ ] Soft constraints introduce noise — hard constraints preferred
- [ ] Mutation space design directly controls acceptance rate
- [ ] Findings quality is a function of experiment diversity, not the extraction prompt
