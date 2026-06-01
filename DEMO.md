# Demo Day Presentation Outline

> 15 minutes. Five segments. The dashboard and report pages are the slides.

## Structure

### Segment 1: Setup (2 min)

**Goal:** Everyone understands the problem in one sentence.

**Script:**
> "Every project manager faces the same question: which tasks are most likely to blow the deadline? I gave Forrest a 12-task project with uncertain durations and asked it to find the best way to hit a 28-day deadline."

**Show:** The scenario brief (one slide or just the `/scenarios/[id]/confirm` page).

**Key line:** "Without Forrest, a PM would guess based on gut feel. With Forrest, we run 10,000 simulations and let the data speak."

---

### Segment 2: Loop in Action (3 min)

**Goal:** Show what an experiment is. Make the loop tangible.

**Action:** Open the live run dashboard at `/scenarios/[id]/run`. If the live run is done, replay a completed run.

**Narrate while the dashboard runs:**
> "Each tick is one experiment. Claude reads the current best scenario and proposes a mutation — maybe it shifts a resource, or adds buffer to a task. Then we run 500 Monte Carlo simulations to score it. If it beats the current best, it becomes the new baseline. Otherwise it's discarded but we keep the lineage."

**Point out:**
- The iteration counter ticking up
- The best-score trajectory improving
- The acceptance/rejection indicators

---

### Segment 3: Findings (5 min)

**Goal:** Walk through all three findings. Show lineage behind #1.

**Action:** Open the report page at `/scenarios/[id]/report`.

**For each finding:**
1. Read the finding out loud
2. State the quantified improvement
3. Show which experiments led to it (lineage)

**For the featured finding (#1):**
> "This is the finding with the strongest lineage. Watch — Forrest discovered this at experiment #87, and it was confirmed by experiments #93, #101, and #156. The mutation was [specific change]. The impact was [quantified improvement]."

**Key line:** "This isn't generic advice. This is a specific, quantified insight that came from 10,000 simulations."

---

### Segment 4: What Surprised Me (3 min)

**Goal:** Honesty > polish. Show one win and one failure.

**Surprise:**
> "I expected [X] to be the bottleneck. Forrest found that [Y] actually dominates. The reason is [brief explanation]."

**What didn't work:**
> "I tried [Z] and it didn't help. The acceptance rate dropped to 5%, which told me the mutation space was too tight. I had to [adjustment]."

---

### Segment 5: Questions (2 min)

**Goal:** Open floor. Let the team react.

**Anticipated questions:**
- "How much did this run cost?" → ~$2-3 in API spend
- "Is this reproducible?" → Yes, second 200-experiment run confirmed
- "What would you do with more budget?" → Try supply-chain domain, or increase to 500 experiments
- "How does this compare to a human PM?" → A human would take weeks to explore this space; Forrest did it in an hour

---

## Backup Plan

If the live dashboard is flaky during the demo:

1. **Pre-saved screenshots** of the dashboard at key moments (iteration 1, 50, 100, 200)
2. **Pre-saved report page** with all three findings
3. **Screen recording** of a complete run (in case live demo fails entirely)

## Timing Rehearsal

| Segment | Script + Transition | Demo Action | Total |
|---------|-------------------|-------------|-------|
| Setup | 1 min | Show scenario page | 2 min |
| Loop | 1 min | Open dashboard, narrate | 3 min |
| Findings | 2 min | Open report, show lineage | 5 min |
| Surprise | 2 min | Talk through slides | 3 min |
| Questions | — | Open floor | 2 min |
| **Total** | | | **15 min** |
