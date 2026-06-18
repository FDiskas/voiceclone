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
