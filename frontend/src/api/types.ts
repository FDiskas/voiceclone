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
