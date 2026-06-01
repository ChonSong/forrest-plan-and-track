# Mental Model of Forrest

> Read this before touching any code. This is the product.

## What Forrest Is

Forrest is a **long-running autonomous loop** over a user-described scenario. Each iteration is one experiment. The loop runs 200 times (paid) or 50 times (free), and at the end, three plain-language findings are extracted.

## The Loop

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│   │ PROPOSE  │───▶│ SIMULATE │───▶│  SCORE   │         │
│   │          │    │          │    │          │         │
│   │ Claude   │    │ 500 MC   │    │ Aggregate│         │
│   │ reads    │    │ sims per │    │ stats →  │         │
│   │ current  │    │ expt     │    │ score    │         │
│   │ best &   │    │          │    │          │         │
│   │ proposes │    │          │    │          │         │
│   │ mutation │    │          │    │          │         │
│   └──────────┘    └──────────┘    └────┬─────┘         │
│                                        │                │
│                                        ▼                │
│                               ┌──────────────┐         │
│                               │ COMMIT OR    │         │
│                               │ DISCARD      │         │
│                               │              │         │
│                               │ Score beats  │         │
│                               │ current best │         │
│                               │ → new        │         │
│                               │ baseline     │         │
│                               │              │         │
│                               │ Otherwise →  │         │
│                               │ discard but  │         │
│                               │ keep lineage │         │
│                               └──────┬───────┘         │
│                                      │                  │
│                                      ▼                  │
│                               ┌──────────────┐         │
│                               │   REPEAT     │         │
│                               │   200 times  │         │
│                               └──────────────┘         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## The Four Entities

| Entity | What It Is | You'll Touch It When... |
|--------|-----------|------------------------|
| **Scenario** | The user's problem: description, mutation space, objective | Authoring a new demo |
| **Run** | One execution of the loop. Holds baseline + best score | Kicking off / monitoring runs |
| **Experiment** | One iteration. Hypothesis, mutation JSON, score, accepted? | Debugging why a run drifted |
| **Finding** | One of the top three plain-language insights at the end | Reviewing report output |

## Data Model (Prisma)

```
┌──────────────┐       ┌──────────────┐
│   Scenario   │       │     Run      │
│──────────────│       │──────────────│
│ id           │──1:N──│ id           │
│ description  │       │ scenarioId   │
│ mutationSpace│       │ baseline     │
│ objective    │       │ bestScore    │
│ createdAt    │       │ status       │
└──────────────┘       │ maxExperiments│
                       └──────┬───────┘
                              │
                              │ 1:N
                              ▼
                       ┌──────────────┐       ┌──────────────┐
                       │  Experiment  │       │   Finding    │
                       │──────────────│       │──────────────│
                       │ id           │       │ id           │
                       │ runId        │       │ runId        │
                       │ hypothesis   │       │ content      │
                       │ mutation     │       │ rank         │
                       │ score        │       │ lineageRef   │
                       │ accepted     │       └──────────────┘
                       │ iteration    │
                       └──────────────┘
```

## Key Files

| File | What It Does | Read When |
|------|-------------|-----------|
| `prisma/schema.prisma` | 4 models: Scenario, Run, Experiment, Finding | Day 1 — data model |
| `src/lib/engine.ts` | **THE Loop.** Propose → Simulate → Score → Commit | Day 1 — read twice |
| `src/lib/actions.ts` | Server actions: createScenario, structure, launch | Day 2 |
| `src/lib/db.ts` | Prisma client singleton | Day 2 |
| `src/app/scenarios/new/page.tsx` | Create flow | Day 1 |
| `src/app/scenarios/[id]/setup/page.tsx` | AI-assisted structuring | Day 1 |
| `src/app/scenarios/[id]/confirm/page.tsx` | Pre-launch review | Day 2 |
| `src/app/scenarios/[id]/run/page.tsx` | Live dashboard | Day 1 |
| `src/app/scenarios/[id]/report/page.tsx` | Findings + lineage | Day 1 |
| `AGENTS.md` | Next.js 16 deltas. **Mandatory read.** | Day 1 — first thing |

## Engine Quirks (Known Before You Hit Them)

1. **The loop runs server-side.** Closing the browser tab does NOT stop a run. Use the pause control on the dashboard.
2. **Stuck runs:** If a run gets stuck in "running" after a crash, mark it failed directly in Prisma Studio. Don't retry — duplicate active runs make the dashboard misbehave.
3. **Findings are AI-generated.** If they read generic, the cause is almost always the input experiments, not the finding-extraction prompt.
4. **Forrest minimizes by default.** Make sure your objective is signed correctly.
5. **Soft constraints introduce noise.** Convert anything you really care about to a hard constraint.

## Next.js 16 Heads Up

This is not the Next.js you may know. APIs, conventions, and defaults have moved. Don't trust pattern-matching from older Next projects. Check `AGENTS.md` when something looks off, and ask before reaching for a workaround.

## The Product Story

> Your plan runs once. Forrest runs it 10,000 times.

The value proposition: you describe a problem once, and Forrest autonomously explores the space through Monte Carlo simulation, finding non-obvious optimizations that a human would take weeks to discover. The three findings at the end are the distilled insight — plain language, actionable, surprising.
