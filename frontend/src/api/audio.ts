// Decodes any audio blob the WebView can handle (webm/opus from MediaRecorder,
// uploaded mp3/m4a/ogg/wav) and re-encodes it as a 24 kHz mono 16-bit PCM WAV —
// entirely in the WebView. This keeps the backend ffmpeg-free: it only ever
// receives plain PCM WAV. Decoding/resampling happens here, where the platform
// codecs already live.

const TARGET_SAMPLE_RATE = 24_000;

/**
 * Convert an audio blob to a 24 kHz mono 16-bit PCM WAV blob.
 * Throws if the WebView can't decode the input (caller should fall back to
 * sending the original bytes — the backend can still decode common formats).
 */
export async function convertToWav(blob: Blob): Promise<Blob> {
  const arrayBuffer = await blob.arrayBuffer();

  // Decode with the platform codecs the WebView already ships.
  const decodeCtx = new AudioContext();
  let decoded: AudioBuffer;
  try {
    decoded = await decodeCtx.decodeAudioData(arrayBuffer);
  } finally {
    await decodeCtx.close();
  }

  // Downmix to mono and resample to 24 kHz via an offline render.
  const frameCount = Math.max(1, Math.ceil(decoded.duration * TARGET_SAMPLE_RATE));
  const offline = new OfflineAudioContext(1, frameCount, TARGET_SAMPLE_RATE);
  const source = offline.createBufferSource();
  source.buffer = decoded;
  source.connect(offline.destination);
  source.start();
  const rendered = await offline.startRendering();

  return encodeWav(rendered.getChannelData(0), TARGET_SAMPLE_RATE);
}

/**
 * Duration of an audio blob in seconds, using the platform codecs the WebView
 * already ships. We decode rather than reading `HTMLAudioElement.duration`
 * because MediaRecorder's webm/opus output reports `Infinity` there until the
 * clip is seeked to the end — decoding is reliable for both recordings and
 * uploads. Throws if the WebView can't decode the input.
 */
export async function audioDurationSeconds(blob: Blob): Promise<number> {
  const arrayBuffer = await blob.arrayBuffer();
  const ctx = new AudioContext();
  try {
    const decoded = await ctx.decodeAudioData(arrayBuffer);
    return decoded.duration;
  } finally {
    await ctx.close();
  }
}

/** Serialize mono float samples as a 16-bit PCM WAV blob. */
function encodeWav(samples: Float32Array, sampleRate: number): Blob {
  const bytesPerSample = 2;
  const dataLength = samples.length * bytesPerSample;
  const buffer = new ArrayBuffer(44 + dataLength);
  const view = new DataView(buffer);

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + dataLength, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true); // fmt chunk size
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // mono
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * bytesPerSample, true); // byte rate
  view.setUint16(32, bytesPerSample, true); // block align
  view.setUint16(34, 16, true); // bits per sample
  writeString(view, 36, "data");
  view.setUint32(40, dataLength, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    offset += bytesPerSample;
  }

  return new Blob([buffer], { type: "audio/wav" });
}

function writeString(view: DataView, offset: number, str: string): void {
  for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
}

const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

/**
 * Save a blob to disk under `filename`.
 *
 * In the Tauri desktop shell, WKWebView ignores programmatic `<a download>`
 * clicks, so we open a native Save dialog and write the bytes via the
 * `save_file` command. In a plain browser we fall back to the anchor click.
 * Returns true if the file was saved, false if the user cancelled the dialog.
 */
export async function saveBlob(blob: Blob, filename: string): Promise<boolean> {
  if (isTauri) {
    const { save } = await import("@tauri-apps/plugin-dialog");
    const { invoke } = await import("@tauri-apps/api/core");
    const path = await save({
      defaultPath: filename,
      filters: [{ name: "Audio", extensions: ["wav"] }],
    });
    if (!path) return false; // user cancelled
    const contents = new Uint8Array(await blob.arrayBuffer());
    await invoke("save_file", { path, contents: Array.from(contents) });
    return true;
  }

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  // Revoke after the click has been dispatched.
  setTimeout(() => URL.revokeObjectURL(url), 0);
  return true;
}

/**
 * Concatenate streamed per-sentence WAV chunks (all identical 24 kHz mono
 * 16-bit PCM from the backend) into one downloadable WAV — by splicing the raw
 * `data` payloads under a single header, so no decode/resample loss.
 */
export function concatWavChunks(chunks: ArrayBuffer[]): Blob | null {
  const parsed = chunks.map(parseWav).filter((p): p is ParsedWav => p !== null);
  if (parsed.length === 0) return null;

  const { sampleRate, channels, bitsPerSample } = parsed[0];
  const totalDataLength = parsed.reduce((sum, p) => sum + p.data.byteLength, 0);

  const bytesPerSample = bitsPerSample / 8;
  const blockAlign = channels * bytesPerSample;
  const buffer = new ArrayBuffer(44 + totalDataLength);
  const view = new DataView(buffer);

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + totalDataLength, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, channels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * blockAlign, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);
  writeString(view, 36, "data");
  view.setUint32(40, totalDataLength, true);

  const out = new Uint8Array(buffer);
  let offset = 44;
  for (const p of parsed) {
    out.set(p.data, offset);
    offset += p.data.byteLength;
  }

  return new Blob([buffer], { type: "audio/wav" });
}

interface ParsedWav {
  sampleRate: number;
  channels: number;
  bitsPerSample: number;
  data: Uint8Array;
}

/** Walk a WAV's RIFF chunks to extract fmt params + the data payload. */
function parseWav(buf: ArrayBuffer): ParsedWav | null {
  const view = new DataView(buf);
  if (buf.byteLength < 12) return null;

  let sampleRate = 24_000;
  let channels = 1;
  let bitsPerSample = 16;
  let data: Uint8Array | null = null;

  let offset = 12; // skip "RIFF"<size>"WAVE"
  while (offset + 8 <= view.byteLength) {
    const id = String.fromCharCode(
      view.getUint8(offset),
      view.getUint8(offset + 1),
      view.getUint8(offset + 2),
      view.getUint8(offset + 3),
    );
    const size = view.getUint32(offset + 4, true);
    const body = offset + 8;
    if (id === "fmt ") {
      channels = view.getUint16(body + 2, true);
      sampleRate = view.getUint32(body + 4, true);
      bitsPerSample = view.getUint16(body + 14, true);
    } else if (id === "data") {
      data = new Uint8Array(buf, body, Math.min(size, view.byteLength - body));
    }
    offset = body + size + (size % 2); // chunks are word-aligned
  }

  return data ? { sampleRate, channels, bitsPerSample, data } : null;
}

/**
 * Best-effort conversion for upload: returns a WAV blob + filename, or falls
 * back to the original bytes if this WebView can't decode the input (e.g. an
 * uncommon upload format on WebKitGTK). The backend decodes either via
 * libsndfile.
 */
export async function toUploadAudio(
  blob: Blob,
): Promise<{ data: Blob; filename: string }> {
  try {
    return { data: await convertToWav(blob), filename: "recording.wav" };
  } catch {
    return { data: blob, filename: "recording.bin" };
  }
}
