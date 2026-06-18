---
name: mps-memory-synthesis
description: OmniVoice synthesis on Apple Silicon crashed the whole OS via MPS unified-memory exhaustion. Fixes — float16 on mps, empty_cache between sentences, serialize generation, cap MPS watermark. Knobs to tune perf/quality.
keywords: [mps, omnivoice, synthesis, oom, memory, crash, float16, empty_cache, watermark, apple-silicon, num_step, performance]
created: 2026-06-19
updated: 2026-06-19
---

**Incident (2026-06-19):** synthesizing text crashed macOS and forced a restart. Backend log: `MPS backend out of memory (MPS allocated: 6.05 GiB, other allocations: 36.33 GiB, max allowed: 42.43 GiB)`. The caught OOM didn't crash the app — the *unified-memory* pressure (~42 GiB committed) starved macOS into a panic.

**Root causes:** (1) model ran in **float32 on MPS** (`resolved_dtype` only used fp16 for CUDA) — double the memory; (2) **no device-cache release between sentences**, so a multi-sentence stream accumulated the "other allocations: 36 GiB"; (3) **generation not serialized** — concurrent requests stack working sets.

**Fixes (all in place):**
- [backend/app/config.py](backend/app/config.py) `resolved_dtype` → **float16 on `mps`** too (not just cuda). Biggest lever. Override with `VOICECLONE_DTYPE=float32` if fp16 causes unsupported-op/quality issues on MPS.
- [backend/app/engine/omnivoice_engine.py](backend/app/engine/omnivoice_engine.py): `synthesize` runs under `torch.inference_mode()`, holds `_infer_lock` (one pass at a time), and `_release_device_memory()` calls `torch.mps.empty_cache()` (or cuda) in `finally` after every sentence.
- MPS watermark cap: `mps_high_watermark_ratio` setting (default **0.8**) → set as `PYTORCH_MPS_HIGH_WATERMARK_RATIO` before the allocator inits, so an oversized synthesis raises a clean OOM instead of crashing the OS. NEVER set it to 0.0 (the log's suggestion) — that disables the cap and is what enables the system crash.

**Perf/quality knobs (env, `VOICECLONE_` prefix):** `num_step` (default 32; lower = faster + less memory, lower quality), `dtype`, `device`, `mps_high_watermark_ratio`.

**Still open:** streaming endpoint sends 200 before synthesis, so a mid-stream OOM can't become an error response (`response already started`). Not addressed — memory fixes should prevent the OOM. See [[tauri-backend-lifecycle]], [[ffmpeg-not-avconv]].
