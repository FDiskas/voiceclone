---
name: model-management
description: Managed-model abstraction (voice+whisper), opt-in download, /api/models endpoints, byte-level HF progress
keywords: models, delete, download, warmup, huggingface, cache, registry, ManagedModel, settings, progress
created: 2026-06-19
updated: 2026-06-19
---

**Decision:** Downloadable weights are a generic "managed model" capability, not engine-specific.

- `app/models/`: `ManagedModel` protocol (`model_key`, `model_info() -> ModelInfo`, `delete_model() -> DeletedModel`), `ModelRegistry` (keyed view), and `huggingface_cache.py` (the ONE place that scans/purges the HF cache — `describe(repo_id)`, `purge(repo_id)`; defensive, returns "not downloaded"/no-op if hub absent).
- Both `OmniVoiceEngine` (key `voice`) and `WhisperTranscriber` (key `transcription`, repo `Systran/faster-whisper-{size}`) implement it. Fake impls don't.
- API: `GET /api/models` (list w/ real cache path + size), `DELETE /api/models/{key}` (404 on unknown). Replaced the old engine-only `DELETE /api/engine/model` and the `manageable` flag on `/api/engine/status` (both removed). Registry wired in `dependencies.get_model_registry()`.

**Why:** User asked delete to cover Whisper too and to show each model's real path. Generalizing avoided duplicating the cache scan/purge in two adapters and keeps the engine layer free of cache I/O.

**Opt-in download:** model is NOT warmed at startup (`main.py` lifespan removed). Engine rests `idle`; UI shows a "Download voice model" button (ModelStatusBanner) that POSTs `/api/engine/warmup`, then polls. `idle` is a resting state — polling only continues on downloading/loading.

**Byte-level progress:** `hf_progress.py` patches `huggingface_hub.utils.tqdm.tqdm.update` in place (lazy imports defeat per-module patching). snapshot_download runs a "Fetching N files" count bar AND a `unit="B"` byte bar — the tracker prefers byte bars when present (else falls back to file counts) so % isn't pinned near 0 during the big weights file. Extras pin `huggingface_hub>=0.34` for the aggregate byte bar.

See [[ffmpeg-not-avconv]], [[mps-memory-synthesis]].
