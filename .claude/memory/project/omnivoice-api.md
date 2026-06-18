---
name: omnivoice-api
description: k2-fsa/OmniVoice real API — zero-shot, generate(text, ref_audio, ref_text), 24kHz output, no language arg
keywords: [omnivoice, tts, api, generate, zero-shot, voice-cloning]
created: 2026-06-18
updated: 2026-06-18
---

**Fact:** OmniVoice (https://github.com/k2-fsa/OmniVoice) is a zero-shot multilingual TTS / voice-cloning model.

- Install: `pip install omnivoice` (+ matching torch/torchaudio).
- Load: `OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=..., dtype=...)`.
- Synthesize: `model.generate(text=..., ref_audio="ref.wav", ref_text="...", num_step=32, speed=1.0, duration=None)` → list of numpy arrays, shape (T,), **24 kHz**. Write with `soundfile.write(out, audio[0], 24000)`.
- `ref_text` is optional (auto-transcribes via Whisper). Best ref audio: 3–10 s.

**Why it shapes design:** It's zero-shot — there is NO separate "train/enroll profile" step. A "voice profile" in our app = stored {reference audio + transcript + language + name}. Synthesis re-clones each call from that stored reference.

**How to apply:**

- There is **no language parameter** on generate(); language is inferred from input text. We keep `language` only as profile metadata for UI + as context for the user's ref_text.
- Wrap OmniVoice behind a `VoiceEngine` interface (DIP) so a `FakeEngine` runs in tests/dev without downloading the model. The real adapter is the only place that imports `omnivoice`.
- On Mac (no CUDA) auto-select device mps/cpu and float32 on cpu. Browser recordings are webm/opus → convert to wav via ffmpeg before passing to OmniVoice.

**Streaming:** base `generate()` has NO documented `stream=` flag — it returns the full array. "Streaming" in this app = app-level **sentence chunking**: split text, synthesize each sentence, stream chunks as `[uint32 BE length][wav]` frames (endpoint `/speech/stream`); frontend plays them gaplessly via Web Audio. Don't fabricate a native streaming call.

**Transcription:** profile transcript is optional; if blank, auto-transcribe the reference via a `Transcriber` (faster-whisper adapter, `fake` default), selected by `VOICECLONE_TRANSCRIBER`. Also `POST /api/transcribe` for the UI auto-fill button.
