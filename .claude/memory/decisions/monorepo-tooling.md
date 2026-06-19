---
name: monorepo-tooling
description: repo is a pnpm workspace (root coordinator + frontend as only JS package); Turborepo deliberately rejected; backend is Python, not a pnpm package
keywords: [monorepo, pnpm, workspace, turborepo, root, package.json, concurrently, dev-launcher]
created: 2026-06-19
updated: 2026-06-19
---

**Fact / Rule:** Root `package.json` (private, version `0.0.0`) + `pnpm-workspace.yaml` make this a pnpm workspace. `frontend/` is the ONLY JS workspace package. `backend/` is Python (uvicorn/FastAPI) and is NOT a pnpm package — it's launched from root scripts via `cd backend && uvicorn ...`. Root `dev` uses `concurrently` to run backend+frontend together; `desktop:*` and `build` proxy to the frontend package via `pnpm --filter voiceclone-frontend`.

**Why:** User asked whether to adopt Turborepo. Rejected: Turbo's value is caching/orchestrating many JS/TS packages, but there's only one JS package — the slow builds are Python (PyInstaller) and Rust (Tauri), which Turbo can't cache. pnpm workspace gives the one-command DX without the overhead.

**How to apply:** App version still lives in `frontend/package.json` (root stays `0.0.0`); release flow unchanged — see [[release-versioning]]. After pulling these changes, run `pnpm install` from repo ROOT (inside the dev container) to relocate deps to the workspace. Do NOT add Turborepo.

See [[frontend-package-manager]], [[dev-environment]].
