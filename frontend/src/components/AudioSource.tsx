import { useEffect, useState } from "react";

import { useRecorder } from "../hooks/useRecorder";

interface Props {
  onChange: (blob: Blob | null) => void;
}

// Lets the user provide a reference voice by recording or uploading a file.
// Emits the selected audio blob (or null) to the parent.
export function AudioSource({ onChange }: Props) {
  const recorder = useRecorder();
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const emit = (blob: Blob | null) => {
    setPreviewUrl(blob ? URL.createObjectURL(blob) : null);
    onChange(blob);
  };

  useEffect(() => {
    if (recorder.blob) emit(recorder.blob);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recorder.blob]);

  return (
    <div className="audio-source">
      <div className="row">
        {recorder.isRecording ? (
          <button type="button" className="danger" onClick={recorder.stop}>
            ◼ Stop recording
          </button>
        ) : (
          <button type="button" onClick={() => void recorder.start()}>
            ● Record
          </button>
        )}

        <span className="muted">or</span>

        <label className="file-label">
          Upload audio
          <input
            type="file"
            accept="audio/*"
            onChange={(e) => emit(e.target.files?.[0] ?? null)}
          />
        </label>
      </div>

      {recorder.error && <p className="error">{recorder.error}</p>}
      {previewUrl && <audio controls src={previewUrl} />}
    </div>
  );
}
