---
name: release-versioning
description: single version source is frontend/package.json; tauri.conf.json version points at ../package.json so pnpm version patch drives the built app version + git tag
keywords: [version, release, pnpm, tauri, package.json, git-tag, patch, bump]
created: 2026-06-19
updated: 2026-06-19
---

**Fact / Rule:** App version is owned by `frontend/package.json`. `frontend/src-tauri/tauri.conf.json` `version` is set to `"../package.json"`, so Tauri reads the version from package.json. `Cargo.toml` version is ignored for app versioning (Tauri only falls back to it when no `version` is set in config).

**Why:** Previously tauri.conf.json + Cargo.toml were stuck at `0.1.0` while package.json was bumped to 1.1.x — the built desktop app showed the wrong version. Pointing Tauri at package.json makes one bump propagate everywhere.

**How to apply:** Release = run `pnpm version patch` from `frontend/` (bumps package.json, commits `x.y.z`, tags `vx.y.z`), then `git push --follow-tags`. Requires a CLEAN git working tree or it aborts ("Git working directory not clean") — commit/stash first.

See [[tauri-packaging-gotchas]], [[frontend-package-manager]].
