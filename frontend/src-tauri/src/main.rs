// Prevents an extra console window on Windows in release.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::fs::{self, OpenOptions};
use std::io::Write;
use std::sync::Mutex;

use tauri::{Emitter, Manager, RunEvent, WindowEvent};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
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

    let (rx, child) = sidecar
        .env("VOICECLONE_ENGINE", engine)
        .env("VOICECLONE_TRANSCRIBER", transcriber)
        .spawn()
        .map_err(|e| format!("Failed to start backend process: {e}"))?;

    // Resolve the log file path: <app log dir>/backend.log
    let log_path = app
        .path()
        .app_log_dir()
        .map_err(|e| format!("Could not resolve log directory: {e}"))?
        .join("backend.log");

    // Ensure the directory exists.
    if let Some(parent) = log_path.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("Could not create log directory: {e}"))?;
    }

    // Emit the log path to the frontend so it can offer an "Open logs" link.
    let path_str = log_path.to_string_lossy().to_string();
    let handle = app.clone();
    let emit_path = path_str.clone();

    // Spawn a thread that drains stdout/stderr and appends to the log file.
    std::thread::spawn(move || {
        let mut rx = rx;

        let mut file = match OpenOptions::new()
            .create(true)
            .append(true)
            .open(&log_path)
        {
            Ok(f) => f,
            Err(e) => {
                eprintln!("[VoiceClone] Could not open log file: {e}");
                return;
            }
        };

        // Emit the log path once the file is open.
        handle.emit("backend:log-path", &emit_path).ok();

        while let Some(event) = rx.blocking_recv() {
            let line = match event {
                CommandEvent::Stdout(bytes) | CommandEvent::Stderr(bytes) => {
                    String::from_utf8_lossy(&bytes).into_owned()
                }
                CommandEvent::Error(msg) => format!("[sidecar error] {msg}"),
                CommandEvent::Terminated(status) => {
                    format!(
                        "[backend exited] code={:?} signal={:?}",
                        status.code, status.signal
                    )
                }
                _ => continue,
            };
            let _ = writeln!(file, "{line}");
            // Also echo to host stderr so `tauri dev` shows backend output.
            eprint!("[backend] {line}");
        }
    });

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
