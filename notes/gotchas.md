# Gotchas Log

> Things that have bitten. Update as you discover them.

## Security & Data
- **Never commit `.env`** — The repo's `.gitignore` covers it. Don't add exceptions.
- **Treat all scenario data as Claude-prompt-visible** — No real customer records.
- **Local SQLite DB** is yours. Don't share it. Delete before any public screen recording.

## Engine Gotchas
| Gotcha | Symptom | Fix |
|--------|---------|-----|
| Server-side loop | Closing browser doesn't stop a run | Use pause control on dashboard |
| Stuck "running" state | Run crashed but status didn't update | Mark failed in Prisma Studio directly |
| Generic findings | Findings read as motherhood & apple pie | Fix the experiments, not the prompt |
| Concurrent run conflicts | Dashboard misbehaving | Only one active run at a time |

## Setup Gotchas
| Gotcha | Symptom | Fix |
|--------|---------|-----|
| Forgot `prisma generate` | `PrismaClientInitializationError` | Run `npx prisma generate` after pulling |
| Wrong API key workspace | Claude 401 | Verify `.env` key matches correct workspace |
| Hero ticker blank | Landing page loads but no animation | Hard refresh; ticker hydrates on mount |

## Next.js 16 Gotchas
| Gotcha | Notes |
|--------|-------|
| [To be filled] | |

## Discovery Log
> Date-stamped discoveries

### YYYY-MM-DD
- [Discovery]
