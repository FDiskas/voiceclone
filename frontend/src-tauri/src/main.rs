// Prevents an extra console window on Windows in release.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::Mutex;

use tauri::{Manager, RunEvent, WindowEvent};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

/// Holds the running backend sidecar so we can terminate it on exit.
struct Backend(Mutex<Option<CommandChild>>);

fn spawn_backend(app: &tauri::AppHandle) -> Result<CommandChild, tauri::Error> {
    // The packaged app ships the real OmniVoice engine, so default the sidecar
    // to it (and to Whisper for transcription). A developer can still override
    // either by exporting the var before launching `tauri dev`.
    let engine = std::env::var("VOICECLONE_ENGINE").unwrap_or_else(|_| "omnivoice".into());
    let transcriber = std::env::var("VOICECLONE_TRANSCRIBER").unwrap_or_else(|_| "whisper".into());

    let (_rx, child) = app
        .shell()
        .sidecar("voiceclone-backend")
        .expect("failed to create sidecar command")
        .env("VOICECLONE_ENGINE", engine)
        .env("VOICECLONE_TRANSCRIBER", transcriber)
        .spawn()
        .expect("failed to spawn backend sidecar");
    Ok(child)
}

fn kill_backend(app: &tauri::AppHandle) {
    if let Some(child) = app.state::<Backend>().0.lock().unwrap().take() {
        let _ = child.kill();
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(Backend(Mutex::new(None)))
        .setup(|app| {
            let handle = app.handle().clone();
            let child = spawn_backend(&handle)?;
            app.state::<Backend>().0.lock().unwrap().replace(child);
            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, WindowEvent::Destroyed) {
                kill_backend(window.app_handle());
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building VoiceClone")
        .run(|app, event| {
            // Belt-and-suspenders: also stop the backend when the app exits.
            if let RunEvent::ExitRequested { .. } = event {
                kill_backend(app);
            }
        });
}
