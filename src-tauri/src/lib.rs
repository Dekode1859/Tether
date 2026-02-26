use log::{info, error};
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use std::process::Command;
use tauri::{Manager, WindowEvent, Emitter};
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut};

mod process_manager;

#[derive(Default)]
struct AppState {
    engine_pid: Mutex<Option<u32>>,
    is_recording: Mutex<bool>,
}

fn get_engine_path() -> String {
    let base = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()))
        .unwrap_or_default();
    
    let engine_path = base.join("tether-engine.exe");
    
    if engine_path.exists() {
        engine_path.to_string_lossy().to_string()
    } else {
        "tether-engine.exe".to_string()
    }
}

#[tauri::command]
fn show_main_window(app: tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.set_focus();
    }
}

#[tauri::command]
fn hide_main_window(app: tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.hide();
    }
}

#[tauri::command]
fn show_widget_window(app: tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("widget") {
        let _ = window.show();
        let _ = window.set_focus();
    }
}

#[tauri::command]
fn hide_widget_window(app: tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("widget") {
        let _ = window.hide();
    }
}

#[tauri::command]
async fn start_spool(app: tauri::AppHandle, state: tauri::State<'_, AppState>) -> Result<(), String> {
    info!("Starting spool (recording)");
    
    let mut is_recording = state.is_recording.lock().map_err(|e| e.to_string())?;
    *is_recording = true;
    
    // Show widget window
    if let Some(window) = app.get_webview_window("widget") {
        let _ = window.show();
    }
    
    // Spawn engine with --spool
    let engine_path = get_engine_path();
    info!("Spawning engine: {}", engine_path);
    
    let mut cmd = Command::new(&engine_path);
    cmd.arg("--spool");
    
    match cmd.spawn() {
        Ok(child) => {
            let pid = child.id();
            info!("Engine spawned with PID: {}", pid);
            let mut engine_pid = state.engine_pid.lock().map_err(|e| e.to_string())?;
            *engine_pid = Some(pid);
            
            // Emit event to frontend
            let _ = app.emit("engine-started", pid);
            Ok(())
        }
        Err(e) => {
            error!("Failed to spawn engine: {}", e);
            let mut is_recording = state.is_recording.lock().map_err(|e| e.to_string())?;
            *is_recording = false;
            Err(format!("Failed to start recording: {}", e))
        }
    }
}

#[tauri::command]
async fn stop_spool(app: tauri::AppHandle, state: tauri::State<'_, AppState>) -> Result<(), String> {
    info!("Stopping spool");
    
    let mut is_recording = state.is_recording.lock().map_err(|e| e.to_string())?;
    *is_recording = false;
    
    // Hide widget window
    if let Some(window) = app.get_webview_window("widget") {
        let _ = window.hide();
    }
    
    // Kill engine process
    let engine_pid = state.engine_pid.lock().map_err(|e| e.to_string())?;
    if let Some(pid) = *engine_pid {
        process_manager::kill_process(pid);
    }
    
    let _ = app.emit("engine-stopped", ());
    Ok(())
}

#[tauri::command]
async fn run_weave(app: tauri::AppHandle, _state: tauri::State<'_, AppState>) -> Result<String, String> {
    info!("Running weave");
    
    let engine_path = get_engine_path();
    
    let output = Command::new(&engine_path)
        .arg("--weave")
        .output()
        .map_err(|e| format!("Failed to run weave: {}", e))?;
    
    if output.status.success() {
        let result = String::from_utf8_lossy(&output.stdout).to_string();
        let _ = app.emit("weave-complete", &result);
        Ok(result)
    } else {
        let err = String::from_utf8_lossy(&output.stderr).to_string();
        error!("Weave failed: {}", err);
        Err(err)
    }
}

#[tauri::command]
async fn run_ask(app: tauri::AppHandle, query: String, _state: tauri::State<'_, AppState>) -> Result<String, String> {
    info!("Running ask: {}", query);
    
    let engine_path = get_engine_path();
    
    let output = Command::new(&engine_path)
        .arg("--ask")
        .arg(&query)
        .output()
        .map_err(|e| format!("Failed to run ask: {}", e))?;
    
    if output.status.success() {
        let result = String::from_utf8_lossy(&output.stdout).to_string();
        let _ = app.emit("ask-complete", &result);
        Ok(result)
    } else {
        let err = String::from_utf8_lossy(&output.stderr).to_string();
        error!("Ask failed: {}", err);
        Err(err)
    }
}

#[tauri::command]
fn get_engine_status() -> Result<process_manager::EngineStatus, String> {
    process_manager::read_status_file()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::new()
            .target(tauri_plugin_log::Target::new(
                tauri_plugin_log::TargetKind::LogDir { file_name: Some("tether".into()) }
            ))
            .build())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![
            show_main_window,
            hide_main_window,
            show_widget_window,
            hide_widget_window,
            start_spool,
            stop_spool,
            run_weave,
            run_ask,
            get_engine_status
        ])
        .setup(|app| {
            info!("Tether starting up");
            
            // Alt+Space to toggle main window
            let alt_space = Shortcut::new(None, Code::Space);
            app.global_shortcut().on_shortcut(alt_space, move |_app, _shortcut, _event| {
                if let Some(window) = _app.get_webview_window("main") {
                    if window.is_visible().unwrap_or(false) {
                        let _ = window.hide();
                    } else {
                        let _ = window.show();
                        let _ = window.set_focus();
                    }
                }
            })?;
            
            // Ctrl+Shift+Space to start/stop recording
            let ctrl_shift_space = Shortcut::new(Some(Modifiers::CONTROL | Modifiers::SHIFT), Code::Space);
            let app_handle2 = app.handle().clone();
            app.global_shortcut().on_shortcut(ctrl_shift_space, move |_app, _shortcut, _event| {
                info!("Ctrl+Shift+Space pressed");
                let _ = app_handle2.emit("hotkey-recording-toggle", ());
            })?;
            
            info!("Global shortcuts registered");
            
            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { api, .. } = event {
                if window.label() == "main" {
                    // Hide instead of close for main window
                    let _ = window.hide();
                    api.prevent_close();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
