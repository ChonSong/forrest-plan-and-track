# 14-Day Plan — Forrest Internship Mission

> Maximal quality. Speed not important. Ask relentlessly. Document everything.

## Overview

| Day | Theme | Key Output |
|-----|-------|------------|
| 0 | Read & prep | Notebook ready, environment checked |
| 1 | Environment setup | Forrest running locally |
| 2 | Code tour + smoke test | 50-experiment run complete |
| 3 | Scenario selection | One-page brief written |
| 4 | Tuning run #1 | First tuning run analyzed |
| 5 | Tuning run #2 | Findings improving |
| 6 | Tuning run #3 + lock | Scenario locked, dress rehearsal |
| 7 | Week 1 review | Manager review, weekly note |
| 8 | Final run #1 | 200 experiments × 500 sims |
| 9 | Analyze + story build | Three findings sharp, lineage clear |
| 10 | Final run #2 | Confidence check |
| 11-12 | Polish + bonus | Presentation rehearsed, bonus artifacts |
| 13 | Dry run | Full rehearsal, no surprises |
| 14 | **Demo day** | 15-minute share-out |

---

## Day 0 — Read Before Your First Standup

**Goal:** Read everything. Notebook open. No code.

### Tasks

- [ ] Read the full mission doc end-to-end
- [ ] Check prerequisites: `node -v` (need 20+), `npm -v`, `git --version`
- [ ] Check for existing Forrest repo clone anywhere on the machine
- [ ] Write down 3 things you already suspect will be tricky
- [ ] Create `daily-logs/day-00.md` with initial thoughts

### Questions to Answer

1. What's the actual `<org>` in the Forrest repo URL? *(Follow up if unknown)*
2. Do we have an Anthropic API key? *(Request from #forrest-eng if not)*
3. Solo or team? Adapt standup/review process accordingly.

### Recommended Answers

- **Repo URL:** Unknown — plan around it, fill in when confirmed. Don't block Day 1 planning on this.
- **API key:** None available yet. Budget $0 for Day 0-1, plan to request when setup begins.
- **Team:** Hybrid — some channels real (#forrest-eng for API key requests), some self-managed (daily standups become self-check-ins).

---

## Day 1 — Environment Setup + First Code Tour

**Goal:** Forrest runs locally. Landing page loads. Dev environment solid.

### Prerequisites Check
```bash
node -v    # Need v20+ ✓ (v22.22.3 confirmed)
npm -v     # ✓ (v10.9.8 confirmed)
git --version  # ✓ (v2.47.3 confirmed)
```

### Tasks — Part A: Setup (~2 hours)

- [ ] Clone Forrest repo: `git clone git@github.com:<TBD>/forrest.git`
- [ ] `cd forrest && npm install` (Next 16, React 19, Prisma 7)
- [ ] Wire API key: `echo "ANTHROPIC_API_KEY=sk-ant-..." > .env`
- [ ] Generate Prisma client: `npx prisma generate && npx prisma migrate dev`
- [ ] Start dev server: `npm run dev`
- [ ] Open `http://localhost:3000` — verify landing page + hero ticker
- [ ] Open Prisma Studio: `npx prisma studio` — confirm 4 empty tables
- [ ] Test scenario create flow at `/scenarios/new`
- [ ] Verify Claude call succeeds on setup page (no 401)

### Tasks — Part B: First Code Read (~2 hours)

Read in this order:

1. **`AGENTS.md`** — 5 min. Next.js 16 deltas. Mandatory.
2. **`prisma/schema.prisma`** — the 4-model data model.
3. **`src/lib/engine.ts`** — the autonomous loop. **Read this twice.** This is the product.
4. **`src/app/scenarios/[id]/run/run-dashboard.tsx`** — frontend polling.
5. **`src/app/scenarios/[id]/report/page.tsx`** — findings rendering.

### Keep a Notebook — Track Three Things

As you read, maintain a running list:
- **(a)** Things you don't understand
- **(b)** Things that look fragile
- **(c)** Assumptions baked into the engine

This list is your Week 1 review deliverable.

### End-of-Day Checklist

- [ ] Landing page loads with live ticker
- [ ] Prisma Studio shows 4 empty tables (Scenario, Run, Experiment, Finding)
- [ ] Scenario create flow works
- [ ] Claude call on setup page doesn't 401
- [ ] All 5 key source files read and annotated
- [ ] Notebook list started
- [ ] `daily-logs/day-01.md` written

---

## Day 2 — Code Tour (Finish) + First Smoke Run

**Goal:** Understand the engine. Run 50 experiments end-to-end.

### Tasks — Part A: Finish Code Tour (~1.5 hours)

- [ ] Read `src/lib/actions.ts` — server actions
- [ ] Read `src/lib/db.ts` — Prisma client singleton
- [ ] Read `README.md` and `package.json` for context
- [ ] Update notebook with any new (a)/(b)/(c) items

### Tasks — Part B: Smoke Run (~30 min active + ~10 min wait)

From the landing page:

1. Click "Start a free run"
2. Paste seed scenario from `docs/seeds/project-schedule.md` (or write a simple one)
3. Pick "Project Scheduling" domain
4. On setup page, accept AI-proposed mutation space and objective unchanged
5. On confirm, set `maxExperiments = 50`
6. Launch and watch the run dashboard
7. When complete, open report page and read the three findings

**If anything fails, fix it now.** The whole arc rests on the loop running cleanly.

### Common Failures

| Symptom | Fix |
|---------|-----|
| `PrismaClientInitializationError` | Run `npx prisma generate` |
| Claude 401 | Check `.env` for typos, or wrong workspace key |
| Hero ticker blank | Hard refresh; ticker hydrates on mount |
| Run stuck "running" after crash | Mark failed in Prisma Studio, don't retry |

### End-of-Day Checklist

- [ ] All source files read and annotated
- [ ] 50-experiment smoke run completed
- [ ] Report page shows 3 findings
- [ ] Screenshots of dashboard + report saved
- [ ] No crashes during live demo
- [ ] `daily-logs/day-02.md` written
- [ ] `experiments/run-001-smoke.md` written

---

## Day 3 — Choose Your Demo Scenario + Write Brief

**Goal:** One-page scenario brief. Scenario entered into Forrest.

### Recommended Scenario: Critical Path Under Uncertainty

**Why this demos well:**
- ✅ **Legible:** "Some tasks take longer than expected — which ones hurt the deadline most?"
- ✅ **Stochastic:** Task durations are inherently uncertain
- ✅ **Surprising:** Forrest may find the critical path isn't what the Gantt chart says, or that adding resources to the "obvious" bottleneck doesn't help
- ✅ **Safe:** Uses synthetic data, no NDA issues

### Scenario Brief Template

```
1. PROBLEM (1 sentence):
   A 12-task project has uncertain durations — which task's uncertainty
   matters most for on-time delivery?

2. VARIABLES:
   - Task durations as ranges (min/mode/max for PERT-style)
   - Task dependencies as DAG
   - Resource assignments per task

3. CONSTRAINTS:
   - Hard: Deadline = X days
   - Soft: Prefer lower cost, fewer resource switches

4. OBJECTIVE:
   Minimize probability of missing deadline
   (or minimize expected makespan)

5. WHY IT MATTERS:
   Every PM faces this. The answer changes how you allocate contingency.
```

### Tasks

- [ ] Brainstorm 3 candidate scenarios, evaluate against 3 traits (legible, stochastic, surprising)
- [ ] Pick one. Write the one-page brief in `SCENARIO.md`
- [ ] Build the scenario JSON: mutationSpace, objective, seed data
- [ ] Enter scenario into Forrest via the UI
- [ ] Launch first tuning run: 50 experiments, simsPerExpt=200
- [ ] While it runs, read Forrest's `/security` page
- [ ] `daily-logs/day-03.md` written

---

## Day 4 — Tuning Run #1 (Analyze + Adjust)

**Goal:** Understand what the engine found. Diagnose and adjust.

### Diagnostic Framework

| Metric | Healthy | Problem |
|--------|---------|---------|
| Acceptance rate | 10-40% | >40% = mutation space too generous; <10% = too tight or noisy |
| Best-score trajectory | Monotonic improvement, diminishing returns | Flat line = no signal |
| Findings quality | Specific, quantified, non-obvious | Generic = experiments not differentiated |

### Tasks

- [ ] Run #1 complete. Open report. Read findings. Screenshot.
- [ ] Check acceptance rate
- [ ] Analyze best-score trajectory
- [ ] Read findings out loud — specific or generic?
- [ ] **Adjust levers:**
  - Tighten `mutationSpace` to variables that matter
  - Sharpen `objective` (Forrest minimizes by default)
  - Convert soft constraints to hard where appropriate
- [ ] Launch Tuning Run #2: 50 experiments, simsPerExpt=200
- [ ] Begin `notes/tuning-log.md` — what you changed and why
- [ ] `daily-logs/day-04.md` written
- [ ] `experiments/run-002-tuning-1.md` written

---

## Day 5 — Tuning Run #2 + Iterate

**Goal:** Findings are getting specific. Story is emerging.

### Tasks

- [ ] Run #2 complete. Read report. Compare to Run #1.
- [ ] Check acceptance rate trajectory
- [ ] Dive into experiment lineage: Which mutations accepted? Which were close calls?
- [ ] Make targeted adjustments
- [ ] Launch Tuning Run #3: 50 experiments, simsPerExpt=200
- [ ] Draft weekly note for #forrest-eng: "What surprised me, what I got stuck on"
- [ ] `daily-logs/day-05.md` written
- [ ] `experiments/run-003-tuning-2.md` written

---

## Day 6 — Tuning Run #3 + Final Scenario Lock

**Goal:** Scenario is tuned. Lock it. Prepare for 200-experiment final run.

### Tasks

- [ ] Run #3 complete. Report review.
- [ ] Compare all three runs. Is the story converging?
- [ ] Final tuning pass. Lock mutationSpace, objective, constraints.
- [ ] Launch Tuning Run #4 (dress rehearsal): 50 experiments, simsPerExpt=500
- [ ] Document scenario parameters for reproducibility → save to `notes/scenario-params.md`
- [ ] Update `notes/three-things.md` — answers to (a)/(b)/(c)
- [ ] `daily-logs/day-06.md` written
- [ ] `experiments/run-004-tuning-3.md` written

---

## Day 7 — Week 1 Review + Weekly Note

**Goal:** Week 1 complete. Manager review. Story is solid.

### Tasks

- [ ] Run #4 (dress rehearsal) complete. Is the story presentation-ready?
- [ ] End-of-week-1 review with manager (or self-review). Bring `notes/three-things.md`.
- [ ] Finalize weekly note: "What surprised me, what I got stuck on." Post to #forrest-eng.
- [ ] Plan Week 2: Final run + prep.
- [ ] `daily-logs/day-07.md` written
- [ ] `experiments/run-005-dress.md` written

### Week 1 Budget Check

| Run | Expts | Sims/Expt | Est. Cost |
|-----|-------|-----------|-----------|
| Smoke | 50 | 500 | ~$0.40 |
| Tuning 1-3 | 50 ea | 200 ea | ~$0.15 ea |
| Dress | 50 | 500 | ~$0.40 |
| **Total** | | | **~$1.25** |

Remaining budget: ~$48.75

---

## Day 8 — Final 200-Experiment Run #1

**Goal:** Full statistical power. 200 experiments × 500 sims.

### Tasks

- [ ] Launch final run: 200 experiments, 500 sims each
- [ ] Dashboard confirmed polling correctly
- [ ] Run takes ~45-60 min. Use time to structure the share-out.
- [ ] Run completes. Open report. Read all three findings. Read them out loud.
- [ ] Screenshot dashboard + report for presentation
- [ ] `daily-logs/day-08.md` written
- [ ] `experiments/run-006-final-1.md` written

---

## Day 9 — Analyze Final Run + Build the Story

**Goal:** Three findings are sharp. Lineage is clear. You know what surprised you.

### Tasks

- [ ] Deep-dive: experiment lineage, acceptance rate, best-score trajectory, which mutations mattered
- [ ] Identify the one finding with the strongest lineage to feature
- [ ] Identify "surprised me" and "didn't work" talking points
- [ ] Draft the 15-minute share-out structure (see `DEMO.md`)
- [ ] Peer review: do findings survive a "so what?" test?
- [ ] `daily-logs/day-09.md` written

---

## Day 10 — Second 200-Experiment Run (Confidence Check)

**Goal:** Confirm findings are robust, not a fluke.

### Tasks

- [ ] Launch second 200-experiment run with identical parameters
- [ ] While running: review and polish share-out
- [ ] Run completes. Compare findings to Run #1. Consistent?
- [ ] If not consistent → investigate why (noisy objective? too-tight acceptance?)
- [ ] `daily-logs/day-10.md` written
- [ ] `experiments/run-007-final-2.md` written

---

## Days 11-12 — Polish the Demo + Bonus Work

**Goal:** Presentation is rehearsed. Bonus artifacts created.

### Tasks

- [ ] Rehearse the 15-minute share-out. Time it. Cut anything that doesn't land.
- [ ] Clean up scenario parameters, tuning notes, lessons learned → `notes/handoff.md`
- [ ] **BONUS:** Pick one:
  - [ ] Seed scenario PR to Forrest repo
  - [ ] Tuning notebook for next intern
  - [ ] Engine bugfix PR
  - [ ] Docs improvement
- [ ] Take screenshots of everything for the demo. Prepare replay path in case live dashboard is flaky.
- [ ] `daily-logs/day-11.md` and `daily-logs/day-12.md` written

---

## Day 13 — Dry Run

**Goal:** Full rehearsal. No surprises.

### Tasks

- [ ] Full dry run of the share-out. Open live report page. Walk through all five segments.
- [ ] Fix anything unclear or rushed.
- [ ] Verify all screenshots/assets load correctly.
- [ ] `daily-logs/day-13.md` written

---

## Day 14 — Demo Day

**Goal:** Present. Ship.

### Share-Out Structure (15 minutes)

| Segment | Time | Content |
|---------|------|---------|
| **Setup** | 2 min | One-sentence scenario. State the baseline. |
| **Loop in action** | 3 min | Open live dashboard or replay. Explain what an experiment is. |
| **Findings** | 5 min | Walk through all three findings. Show lineage behind #1. Quantify improvement. |
| **Surprise** | 3 min | One thing Forrest found you didn't expect. One thing that didn't work. |
| **Questions** | 2 min | Open floor. |

**Slides are optional.** The dashboard and report pages are the slides.

### End-of-Mission Checklist

- [ ] Demo delivered
- [ ] Three findings presented in plain language
- [ ] Lineage shown for at least one finding
- [ ] Surprise + failure shared honestly
- [ ] All experiment logs complete
- [ ] `daily-logs/day-14.md` written
- [ ] `PROGRESS.md` updated to "Complete"
