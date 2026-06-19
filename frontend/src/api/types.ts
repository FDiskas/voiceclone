export interface Profile {
  id: string;
  name: string;
  language: string;
  transcript: string;
  created_at: string;
}

export interface CreateProfileInput {
  name: string;
  language: string;
  audio: Blob;
  // Optional: when blank the backend auto-transcribes the reference audio.
  transcript?: string;
}

export interface SynthesizeInput {
  text: string;
  speed: number;
}

export type EngineState = "idle" | "downloading" | "loading" | "ready" | "error";

export interface EngineStatus {
  state: EngineState;
  message: string;
  // 0..1 when the download/load size is known, otherwise null (indeterminate).
  progress: number | null;
  // Populated when state === "error".
  detail: string | null;
}

// A downloadable model (voice engine, transcriber) and its on-disk footprint.
export interface ManagedModel {
  key: string;
  label: string;
  repo_id: string;
  downloaded: boolean;
  path: string | null;
  size_bytes: number;
}

export interface DeletedModel {
  key: string;
  repo_id: string;
  found: boolean;
  freed_bytes: number;
}
