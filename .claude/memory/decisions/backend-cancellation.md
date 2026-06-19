---
name: backend-cancellation
description: Synchronous synth/transcribe endpoints support cooperative cancellation on client disconnect; whole-synthesis now loops per-sentence to enable it
keywords: cancel, cancellation, abort, disconnect, stop, synthesis, transcription, gpu, threadpool, cooperative
created: 2026-06-19
updated: 2026-06-19
---

**Decision:** A CPU/GPU-bound request can be cancelled when the client aborts. Worker threads can't be killed, so cancellation is **cooperative**: `app/cancellation.py` holds a `threading.Event`-backed `CancellationToken` + `raise_if_cancelled`; `app/api/cancellation.py:run_cancelling_on_disconnect` runs the blocking work in the threadpool while polling `request.is_disconnected()`, flipping the token on disconnect. Cancelled requests return HTTP 499.

**Why:** FastAPI sync endpoints offload to a threadpool; a client abort doesn't stop the work, so the model/GPU stayed pinned until it finished and the result was discarded. The frontend already aborts via `AbortController` ([[model-management]] era), but only freed the UI.

**How to apply:**
- Loop boundaries are the only cancellation points. Transcription checks between faster-whisper segments (work is lazy there). Synthesis checks between sentences in `SynthesisService._render`.
- **Whole `/speech` now renders sentence-by-sentence and concatenates** (was a single `model.generate()` on the full text) — done specifically so it can stop between sentences. This matches what `/speech/stream` already did, so output is consistent. Don't "optimize" it back to one generate call without restoring cancellation.
- Streaming synthesis needs no token: Starlette stops pulling the sync generator on disconnect, so the engine pauses at the next sentence on its own.
- See OOM context in [[mps-memory-synthesis]] — freeing the engine promptly matters on Apple Silicon.
