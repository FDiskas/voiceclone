// Plays a sequence of WAV chunks gaplessly. Each decoded chunk is scheduled to
// start exactly when the previous one ends, so sentence-by-sentence streaming
// sounds continuous.
export class StreamingAudioPlayer {
  private readonly context: AudioContext;
  private nextStartTime = 0;
  private pending = Promise.resolve();

  constructor() {
    this.context = new AudioContext();
  }

  async enqueue(wav: ArrayBuffer): Promise<void> {
    // Chain decodes so chunks play in arrival order even if decode times vary.
    this.pending = this.pending.then(async () => {
      const buffer = await this.context.decodeAudioData(wav);
      const source = this.context.createBufferSource();
      source.buffer = buffer;
      source.connect(this.context.destination);

      const now = this.context.currentTime;
      const startAt = Math.max(now, this.nextStartTime);
      source.start(startAt);
      this.nextStartTime = startAt + buffer.duration;
    });
    return this.pending;
  }

  async close(): Promise<void> {
    await this.pending;
    await this.context.close();
  }
}
