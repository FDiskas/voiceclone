---
name: dev-environment
description: ALWAYS check if inside the dev container before running any command; if not, ask first. Toolchains live in .devcontainer
keywords:
  [
    devcontainer,
    docker,
    environment-check,
    before-running,
    confirm,
    ffmpeg,
    rust,
    tauri,
  ]
created: 2026-06-18
updated: 2026-06-18
---

**Constraint:** heavy toolchains (Rust, node_modules, Python venv, model weights) should live in the `.devcontainer/` Linux dev container, not on the host.

**Why:** User explicitly asked for a dev container with all deps.

**Rule (always):** Before running ANY tool/command, first determine whether the current environment is inside the dev container. If it is NOT in the container, do not run the command — ask the user to confirm first. The agent itself may be running inside the dev container, so never assume; always check.

**How to detect:** Inside the container `VOICECLONE_DEVCONTAINER=1` is set (via `.devcontainer/devcontainer.json` containerEnv). Fallbacks: `/.dockerenv` exists.

**How to apply:**

- Don't `docker build` / `devcontainer up` on the host unless the user asks — they expect to run it themselves.
- Rust is NOT installed on the host, so `pnpm desktop:dev` / `tauri dev` fail there with `cargo metadata ... No such file`. Use the container for anything Tauri/Rust.
- Caveats baked into `.devcontainer/README.md`: GUI window needs X11 forwarding; macOS `.app` / Windows `.exe` can't be cross-built from Linux. See [[frontend-package-manager]].
