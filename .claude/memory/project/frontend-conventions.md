---
name: frontend-conventions
description: Frontend nav is view-state (no router); default profile language is a client-side localStorage pref
keywords: frontend, react, settings, navigation, localStorage, default-language, preferences, view
created: 2026-06-19
updated: 2026-06-19
---

**Fact:** The frontend has no router. `App.tsx` switches between views with a `view` state (`"studio" | "settings"`) and a header `.nav` tab group; the inactive view is unmounted.

**Fact:** User preferences (e.g. the default language preselected in CreateProfile) live client-side in `localStorage`, not the backend — single-user desktop app. See `hooks/useDefaultLanguage.ts` (key `voiceclone.defaultLanguage`). The preference is lifted into `App` and passed to both `CreateProfile` and `Settings` so there's one source of truth in-session.

**Fact:** Shared option lists live in `src/constants/` (e.g. `languages.ts` exports `LANGUAGES` + `DEFAULT_LANGUAGE`), not duplicated per component.

**How to apply:** Add a new page = new `View` value + tab + conditional render. Add a new user preference = a `localStorage`-backed hook lifted into `App`, surfaced in `Settings`.
