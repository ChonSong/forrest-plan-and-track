# Daily Standup: Day 0 — 2026-06-01

## What I Shipped
- Created planning repo `ChonSong/forrest-plan-and-track` with full structure
- Wrote README, PLAN, FORREST-MODEL, SCENARIO, DEMO, PROGRESS files
- Created Mermaid diagrams (engine loop, data model, timeline)
- Created HTML visualizations (engine loop, data model, timeline)
- Created experiment log template, daily log template
- Created notes templates (code-tour, gotchas, tuning-log, three-things)

## What's Next
- Push repo to GitHub (ChonSong/forrest-plan-and-track)
- Confirm Forrest engine repo URL (org name)
- Request Anthropic API key from #forrest-eng

## What's Blocked
- **Forrest repo URL:** Unknown org name. Need to confirm before Day 1 setup.
- **Anthropic API key:** Need to request from #forrest-eng team channel.

---

## Notes

### Environment Check Results
- Node.js: v22.22.3 ✅ (need v20+)
- npm: v10.9.8 ✅
- git: v2.47.3 ✅
- Forrest repo: Not cloned yet — waiting for URL

### Initial Suspicions (Three Things to Watch)
1. **Next.js 16 API changes** — the mission doc explicitly warns about this. Pattern-matching from older Next projects will break.
2. **Prisma SQLite concurrency** — the engine writes experiment results while the dashboard polls. Potential for read-after-write inconsistencies.
3. **Mutation space design** — the difference between a great demo and a flat line. Too generous = everything accepted. Too tight = nothing moves.

### Key Decisions Made
| Decision | Rationale |
|----------|-----------|
| Domain: Project scheduling | Most legible, naturally stochastic |
| Repo: Public | Transparent, shareable |
| Diagrams: Mermaid + HTML | Native Markdown + rich visuals |
| Experiment log: Full detail | Reproducibility and learning |

### Questions for the Team
1. What's the `<org>` in `git@github.com:<org>/forrest.git`?
2. How do I request a sandbox Anthropic API key?
3. Is there a real manager for the Week 1 review, or self-managed?
