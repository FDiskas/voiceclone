import { LANGUAGES } from "../constants/languages";
import { ManagedModels } from "./ManagedModels";

const GITHUB_URL = "https://github.com/FDiskas/voiceclone";

interface Props {
  defaultLanguage: string;
  onChangeDefaultLanguage: (code: string) => void;
}

// Settings: manage downloaded models, set the default profile language, and
// learn what the app does.
export function Settings({ defaultLanguage, onChangeDefaultLanguage }: Props) {
  return (
    <div className="settings">
      <ManagedModels />

      <div className="card">
        <h2>Default language</h2>
        <p className="muted">Preselected when you create a new voice profile.</p>
        <label>
          Language
          <select
            value={defaultLanguage}
            onChange={(e) => onChangeDefaultLanguage(e.target.value)}
          >
            {LANGUAGES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="card">
        <h2>About</h2>
        <p>
          VoiceClone clones a voice from a short reference recording, then speaks any text you type
          in that voice — no per-voice training. Record or upload a sample, optionally edit the
          transcript, and synthesize speech you can play and download.
        </p>
        <p className="muted">
          Powered by the zero-shot OmniVoice TTS model, with optional Whisper transcription.
        </p>
        <a className="link" href={GITHUB_URL} target="_blank" rel="noreferrer">
          View the project on GitHub ↗
        </a>
      </div>
    </div>
  );
}
