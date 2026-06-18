---
name: frontend-package-manager
description: frontend uses pnpm (not npm) — npm 11 fails to install @tauri-apps/cli
keywords: [pnpm, npm, tauri, package-manager, frontend, install]
created: 2026-06-18
updated: 2026-06-18
---

**Rule:** Use **pnpm** for the `frontend/` workspace, not npm.

**Why:** npm 11.4.2 fails to install `@tauri-apps/cli@2.11.x` with
`EUNSUPPORTEDPROTOCOL Unsupported URL Type "workspace:"` (a known npm/Tauri
packaging issue). pnpm 10 resolves it cleanly, and pnpm is what the Tauri docs
recommend. User explicitly requested pnpm.

**How to apply:**

- Install: `pnpm install`; dev: `pnpm dev`; build: `pnpm build`.
- Desktop: `pnpm desktop:dev` / `pnpm desktop:build` (wrap `tauri`).
- `package.json` pins `pnpm.onlyBuiltDependencies: ["esbuild"]` so esbuild's
  postinstall runs without the interactive `pnpm approve-builds` prompt.
- Tauri config `beforeDevCommand`/`beforeBuildCommand` call `pnpm dev`/`pnpm build`.
- Commit `pnpm-lock.yaml`; don't reintroduce `package-lock.json`. See [[stack-choices]].
