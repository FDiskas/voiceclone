import type {
  CreateProfileInput,
  DeletedModel,
  EngineStatus,
  Profile,
  SynthesizeInput,
} from "./types";
import { toUploadAudio } from "./audio";

// Resolve where the API lives:
//  - VITE_API_BASE wins if set (explicit override).
//  - Inside the Tauri desktop shell the UI is served over a custom protocol,
//    so relative URLs won't reach the backend — target the sidecar directly.
//  - Otherwise use same-origin relative URLs (Vite proxy in dev).
export const API_BASE = resolveApiBase();

function resolveApiBase(): string {
  if (import.meta.env.VITE_API_BASE) return import.meta.env.VITE_API_BASE;
  if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
    return "http://127.0.0.1:8000";
  }
  return "";
}

class ApiError extends Error {}

async function readError(response: Response): Promise<never> {
  let detail = `Request failed (${response.status})`;
  try {
    const body = await response.json();
    if (body?.detail) detail = body.detail;
  } catch {
    // non-JSON body; keep the default message
  }
  throw new ApiError(detail);
}

// Readiness of the voice engine. On first desktop launch the model downloads
// from Hugging Face, so the UI polls this to show a progress indicator.
export async function getEngineStatus(): Promise<EngineStatus> {
  const response = await fetch(`${API_BASE}/api/engine/status`);
  if (!response.ok) await readError(response);
  return response.json();
}

// Deletes the downloaded model from the local cache. It re-downloads on the
// next warm-up (next launch, or the next synthesis).
export async function deleteEngineModel(): Promise<DeletedModel> {
  const response = await fetch(`${API_BASE}/api/engine/model`, { method: "DELETE" });
  if (!response.ok) await readError(response);
  return response.json();
}

export async function listProfiles(): Promise<Profile[]> {
  const response = await fetch(`${API_BASE}/api/profiles`);
  if (!response.ok) await readError(response);
  return response.json();
}

export async function createProfile(input: CreateProfileInput): Promise<Profile> {
  const { data, filename } = await toUploadAudio(input.audio);
  const form = new FormData();
  form.append("name", input.name);
  form.append("language", input.language);
  form.append("audio", data, filename);
  if (input.transcript?.trim()) form.append("transcript", input.transcript);

  const response = await fetch(`${API_BASE}/api/profiles`, { method: "POST", body: form });
  if (!response.ok) await readError(response);
  return response.json();
}

// Downloads the profile's stored reference audio (24 kHz mono wav).
export async function fetchProfileAudio(id: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/api/profiles/${id}/audio`);
  if (!response.ok) await readError(response);
  return response.blob();
}

export async function deleteProfile(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/profiles/${id}`, { method: "DELETE" });
  if (!response.ok) await readError(response);
}

export async function synthesize(id: string, input: SynthesizeInput): Promise<Blob> {
  const response = await fetch(`${API_BASE}/api/profiles/${id}/speech`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) await readError(response);
  return response.blob();
}

// Streams one WAV chunk per sentence. `onChunk` fires as each chunk arrives so
// the first sentence can play while the rest are still being synthesized.
export async function synthesizeStream(
  id: string,
  input: SynthesizeInput,
  onChunk: (wav: ArrayBuffer) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/profiles/${id}/speech/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok || !response.body) await readError(response);

  const reader = response.body!.getReader();
  const parser = new FrameParser(onChunk);
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    if (value) parser.push(value);
  }
}

// Reassembles the [uint32 big-endian length][wav bytes] wire format produced
// by the streaming endpoint, emitting each complete WAV chunk.
class FrameParser {
  private buffer: Uint8Array = new Uint8Array(0);

  constructor(private readonly onChunk: (wav: ArrayBuffer) => void) {}

  push(bytes: Uint8Array): void {
    this.buffer = concat(this.buffer, bytes);
    for (;;) {
      if (this.buffer.byteLength < 4) return;
      const length = new DataView(this.buffer.buffer, this.buffer.byteOffset, 4).getUint32(0);
      if (this.buffer.byteLength < 4 + length) return;
      this.onChunk(copyRange(this.buffer, 4, 4 + length));
      this.buffer = copyFrom(this.buffer, 4 + length);
    }
  }
}

function concat(a: Uint8Array, b: Uint8Array): Uint8Array {
  const out = new Uint8Array(a.byteLength + b.byteLength);
  out.set(a, 0);
  out.set(b, a.byteLength);
  return out;
}

function copyRange(src: Uint8Array, start: number, end: number): ArrayBuffer {
  const out = new Uint8Array(end - start);
  out.set(src.subarray(start, end));
  return out.buffer;
}

function copyFrom(src: Uint8Array, start: number): Uint8Array {
  const out = new Uint8Array(src.byteLength - start);
  out.set(src.subarray(start));
  return out;
}

export async function transcribe(audio: Blob, language?: string): Promise<string> {
  const { data, filename } = await toUploadAudio(audio);
  const form = new FormData();
  form.append("audio", data, filename);
  if (language) form.append("language", language);

  const response = await fetch(`${API_BASE}/api/transcribe`, { method: "POST", body: form });
  if (!response.ok) await readError(response);
  const body = await response.json();
  return body.text as string;
}
