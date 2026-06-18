---
name: macos-unsigned-quarantine
description: macOS app is shipped UNSIGNED; quarantine can't be stripped in CI (added client-side on download); users must run xattr or use "Open Anyway".
keywords: macos, codesign, notarization, quarantine, gatekeeper, xattr, unsigned, tauri, release, dmg
created: 2026-06-19
updated: 2026-06-19
---

**Fact / Rule:** No Apple Developer ID cert available — the macOS build ships unsigned. The `com.apple.quarantine` attribute is NOT present in the CI build artifact; it is stamped by the user's browser on download. Therefore quarantine CANNOT be removed in GitHub Actions — any CI-side `xattr -dr` is meaningless.

**Why:** Quarantine is applied client-side (LSFileQuarantineEnabled) when the DMG is downloaded from the internet, not at build time. Only an Apple Developer ID signature + notarization ($99/yr) lets Gatekeeper trust the app server-side. User has no signing capability.

**How to apply:**
- Don't attempt to strip quarantine in the workflow — it's a no-op.
- The release.yml is already wired for signing via optional `APPLE_*` / `WINDOWS_CERTIFICATE` secrets (omitted-when-empty pattern) — populating them is the only real fix.
- Until then, users must run `xattr -dr com.apple.quarantine /Applications/VoiceClone.app` once, OR System Settings → Privacy & Security → "Open Anyway". On macOS Sequoia 15+, right-click→Open no longer bypasses for unsigned apps.
- Ad-hoc signing in CI doesn't bypass Gatekeeper but is needed for Apple Silicon to run the binary at all; Tauri does this by default.
- Surface the xattr instruction in the GitHub release body.

Related: [[tauri-backend-lifecycle]], [[stack-choices]]
