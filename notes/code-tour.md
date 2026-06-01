# Code Tour Notes

> Day 1-2: Read before you write. Annotate everything.

## Reading Order

1. ✅ `AGENTS.md` — Next.js 16 deltas
2. ✅ `prisma/schema.prisma` — 4-model data model
3. ✅ `src/lib/engine.ts` — THE Loop (read twice)
4. ✅ `src/app/scenarios/[id]/run/run-dashboard.tsx` — frontend polling
5. ✅ `src/app/scenarios/[id]/report/page.tsx` — findings rendering
6. ✅ `src/lib/actions.ts` — server actions
7. ✅ `src/lib/db.ts` — Prisma singleton
8. ✅ `README.md` + `package.json`

## Notes by File

### AGENTS.md
> Key Next.js 16 deltas:
> - [Note 1]
> - [Note 2]

### prisma/schema.prisma
> Data model observations:
> - [Note 1]
> - [Note 2]

### src/lib/engine.ts
> The Loop:
> - [How propose works]
> - [How simulate works]
> - [How score works]
> - [How commit/discard works]
> - [Stopping conditions]

### run-dashboard.tsx
> Polling mechanism:
> - [How the frontend gets updates]
> - [What happens on pause/stop]

### report/page.tsx
> Findings rendering:
> - [How findings are displayed]
> - [Lineage visualization]

## Three Things List

### (a) Things I Don't Understand
1. [Question 1]
2. [Question 2]

### (b) Things That Look Fragile
1. [Fragility 1]
2. [Fragility 2]

### (c) Assumptions Baked Into the Engine
1. [Assumption 1]
2. [Assumption 2]
