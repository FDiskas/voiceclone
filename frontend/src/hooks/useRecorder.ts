import { useCallback, useRef, useState } from "react";

interface Recorder {
  isRecording: boolean;
  blob: Blob | null;
  error: string | null;
  start: () => Promise<void>;
  stop: () => void;
  reset: () => void;
}

// Wraps MediaRecorder so components don't deal with streams/chunks directly.
export function useRecorder(): Recorder {
  const [isRecording, setIsRecording] = useState(false);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const start = useCallback(async () => {
    setError(null);
    setBlob(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        setBlob(new Blob(chunksRef.current, { type: recorder.mimeType }));
        stream.getTracks().forEach((track) => track.stop());
      };

      recorder.start();
      recorderRef.current = recorder;
      setIsRecording(true);
    } catch {
      setError("Microphone access was denied or is unavailable.");
    }
  }, []);

  const stop = useCallback(() => {
    recorderRef.current?.stop();
    recorderRef.current = null;
    setIsRecording(false);
  }, []);

  const reset = useCallback(() => {
    setBlob(null);
    setError(null);
  }, []);

  return { isRecording, blob, error, start, stop, reset };
}
