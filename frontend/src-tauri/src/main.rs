// Prevents an extra console window on Windows in release.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::Mutex;

use tauri::{Emitter, Manager, RunEvent, WindowEvent};
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

/// Holds the running backend sidecar so we can terminate it on exit.
struct Backend(Mutex<Option<CommandChild>>);

/// Human-readable description of why the backend failed to start.
/// Stored in app state and emitted to the frontend once the window is ready.
struct SpawnError(Mutex<Option<String>>);

fn try_spawn_backend(app: &tauri::AppHandle) -> Result<CommandChild, String> {
    // The packaged app ships the real OmniVoice engine, so default the sidecar
    // to it (and to Whisper for transcription). A developer can still override
    // either by exporting the var before launching `tauri dev`.
    let engine =
        std::env::var("VOICECLONE_ENGINE").unwrap_or_else(|_| "omnivoice".into());
    let transcriber =
        std::env::var("VOICECLONE_TRANSCRIBER").unwrap_or_else(|_| "whisper".into());

    let sidecar = app
        .shell()
        .sidecar("voiceclone-backend")
        .map_err(|e| {
            format!(
                "Backend binary not found. Run build_sidecar.sh first.\nDetail: {e}"
            )
        })?;

    let (_rx, child) = sidecar
        .env("VOICECLONE_ENGINE", engine)
        .env("VOICECLONE_TRANSCRIBER", transcriber)
        .spawn()
        .map_err(|e| format!("Failed to start backend process: {e}"))?;

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
        .manage(SpawnError(Mutex::new(None)))
        .setup(|app| {
            let handle = app.handle().clone();
            match try_spawn_backend(&handle) {
                Ok(child) => {
                    app.state::<Backend>().0.lock().unwrap().replace(child);
                }
                Err(msg) => {
                    // Window still opens — the frontend health-poll will time
                    // out and show the status bar error. We also emit an event
                    // so the frontend can surface the specific failure reason.
                    eprintln!("[VoiceClone] Backend spawn error: {msg}");
                    *app.state::<SpawnError>().0.lock().unwrap() = Some(msg.clone());

                    // Emit after a short delay so the window's JS listener has
                    // time to register before the event fires.
                    let handle2 = handle.clone();
                    std::thread::spawn(move || {
                        std::thread::sleep(std::time::Duration::from_millis(800));
                        handle2.emit("backend:spawn-error", msg).ok();
                    });
                }
            }
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
            if let RunEvent::ExitRequested { .. } = event {
                kill_backend(app);
            }
        });
}
