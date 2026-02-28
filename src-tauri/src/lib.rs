use log::{info, error, warn};
use std::sync::Mutex;
use std::process::Command;
use tauri::{Manager, WindowEvent, Emitter};
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

mod process_manager;

const CREATE_NO_WINDOW: u32 = 0x08000000;

fn hide_console(cmd: &mut Command) {
    #[cfg(target_os = "windows")]
    {
        cmd.creation_flags(CREATE_NO_WINDOW);
    }
}

#[derive(Default)]
struct AppState {
    engine_pid: Mutex<Option<u32>>,
    is_recording: Mutex<bool>,
}

fn get_python_path() -> String {
    // Get the directory where the exe is located
    let base = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()))
        .unwrap_or_else(|| std::env::current_dir().unwrap_or_default());
    
    info!("Looking for python in exe directory: {:?}", base);
    
    // Try python-runtime/Scripts/python.exe first (Windows)
    let python_path = base.join("python-runtime").join("Scripts").join("python.exe");
    
    if python_path.exists() {
        info!("Found python at: {:?}", python_path);
        return python_path.to_string_lossy().to_string();
    }
    
    // Fallback to python-runtime/python.exe (Unix)
    let fallback = base.join("python-runtime").join("python.exe");
    if fallback.exists() {
        info!("Found python at fallback: {:?}", fallback);
        return fallback.to_string_lossy().to_string();
    }
    
    // Final fallback to system python
    warn!("Python not found in exe directory, using system python");
    "python".to_string()
}

fn get_engine_dir() -> String {
    // Get the directory where the exe is located
    let base = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|p| p.to_path_buf()))
        .unwrap_or_else(|| std::env::current_dir().unwrap_or_default());
    
    info!("Looking for engine in exe directory: {:?}", base);
    
    let engine_dir = base.join("engine");
    
    if engine_dir.exists() {
        info!("Found engine at: {:?}", engine_dir);
        return engine_dir.to_string_lossy().to_string();
    }
    
    // Fallback to current directory
    warn!("Engine not found, using current directory");
    "engine".to_string()
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
        // Position widget at far right center of primary monitor
        if let Ok(monitor) = window.primary_monitor() {
            if let Some(monitor) = monitor {
                let monitor_size = monitor.size();
                let window_size = window.outer_size().unwrap_or(tauri::PhysicalSize::new(200, 60));
                
                // Calculate x to be at far right, y to be vertically centered
                let x = monitor_size.width.saturating_sub(window_size.width + 20); // 20px from right edge
                let y = (monitor_size.height.saturating_sub(window_size.height)) / 2;
                
                let _ = window.set_position(tauri::PhysicalPosition::new(x as i32, y as i32));
            }
        }
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
async fn start_spool(app: tauri::AppHandle, state: tauri::State<'_, AppState>) -> Result<String, String> {
    info!("Starting spool (recording)");
    
    let mut is_recording = state.is_recording.lock().map_err(|e| e.to_string())?;
    *is_recording = true;
    
    // Show widget window
    if let Some(window) = app.get_webview_window("widget") {
        let _ = window.show();
    }
    
    // Spawn engine with --spool-start in background
    let python_path = get_python_path();
    let engine_dir = get_engine_dir();
    info!("Spawning engine: {} -m engine --spool-start", python_path);
    info!("Engine dir: {}", engine_dir);
    
    let mut cmd = Command::new(&python_path);
    cmd.arg("-m").arg("engine").arg("--spool-start");
    cmd.current_dir(&engine_dir);
    hide_console(&mut cmd);
    
    match cmd.spawn() {
        Ok(child) => {
            let pid = child.id();
            info!("Engine spawned with PID: {}", pid);
            let mut engine_pid = state.engine_pid.lock().map_err(|e| e.to_string())?;
            *engine_pid = Some(pid);
            
            // Emit event to frontend
            let _ = app.emit("engine-started", pid);
            Ok(format!("Recording started with PID: {}", pid))
        }
        Err(e) => {
            error!("Failed to spawn engine: {}", e);
            *is_recording = false;
            Err(format!("Failed to start recording: {}", e))
        }
    }
}

#[tauri::command]
async fn stop_spool(app: tauri::AppHandle, state: tauri::State<'_, AppState>) -> Result<String, String> {
    info!("Stopping spool");
    
    // Get the PID
    let mut engine_pid = state.engine_pid.lock().map_err(|e| e.to_string())?;
    let pid = engine_pid.ok_or("No recording process found")?;
    
    // Send SIGINT to gracefully stop recording (Python will catch this and save audio)
    #[cfg(target_os = "windows")]
    {
        let _ = Command::new("taskkill")
            .args(["/PID", &pid.to_string()])
            .spawn();
    }
    
    // Wait a moment for the process to handle the signal and save audio
    std::thread::sleep(std::time::Duration::from_millis(500));
    
    // Now force kill if still running
    #[cfg(target_os = "windows")]
    {
        let _ = Command::new("taskkill")
            .args(["/F", "/PID", &pid.to_string()])
            .spawn();
    }
    
    // Hide widget window
    if let Some(window) = app.get_webview_window("widget") {
        let _ = window.hide();
    }
    
    let mut is_recording = state.is_recording.lock().map_err(|e| e.to_string())?;
    *is_recording = false;
    *engine_pid = None;
    
    let _ = app.emit("engine-stopped", ());
    
    Ok("Recording stopped".to_string())
}

#[tauri::command]
async fn transcribe_spool(app: tauri::AppHandle, audio_path: String) -> Result<String, String> {
    info!("Transcribing spool: {}", audio_path);
    
    let python_path = get_python_path();
    let engine_dir = get_engine_dir();
    
    let mut cmd = Command::new(&python_path);
    cmd.arg("-m").arg("engine").arg("--spool-transcribe").arg(&audio_path);
    cmd.current_dir(&engine_dir);
    hide_console(&mut cmd);
    
    match cmd.output() {
        Ok(output) => {
            let stdout = String::from_utf8_lossy(&output.stdout).to_string();
            let stderr = String::from_utf8_lossy(&output.stderr).to_string();
            
            info!("Transcribe stdout: {}", stdout);
            if !stderr.is_empty() {
                info!("Transcribe stderr: {}", stderr);
            }
            
            // Extract transcription from stdout (format: TRANSCRIPTION:...)
            let transcription = stdout
                .lines()
                .find(|l| l.starts_with("TRANSCRIPTION:"))
                .map(|l| l.trim_start_matches("TRANSCRIPTION:").to_string());
            
            if let Some(text) = transcription {
                info!("Transcription complete: {}", text);
                let _ = app.emit("transcription-complete", &text);
                Ok(text)
            } else {
                Ok("Transcription complete (no text)".to_string())
            }
        }
        Err(e) => {
            error!("Failed to transcribe: {}", e);
            Err(format!("Failed to transcribe: {}", e))
        }
    }
}

#[tauri::command]
async fn run_weave(app: tauri::AppHandle, _state: tauri::State<'_, AppState>) -> Result<String, String> {
    info!("Running weave");
    
    let python_path = get_python_path();
    let engine_dir = get_engine_dir();
    
    let mut cmd = Command::new(&python_path);
    cmd.arg("-m").arg("engine").arg("--weave");
    cmd.current_dir(&engine_dir);
    hide_console(&mut cmd);
    
    let output = cmd.output()
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
    
    let python_path = get_python_path();
    let engine_dir = get_engine_dir();
    
    let mut cmd = Command::new(&python_path);
    cmd.arg("-m").arg("engine").arg("--ask");
    cmd.arg(&query);
    cmd.current_dir(&engine_dir);
    hide_console(&mut cmd);
    
    let output = cmd.output()
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
async fn check_mic(app: tauri::AppHandle) -> Result<String, String> {
    info!("Checking microphone");
    
    let python_path = get_python_path();
    let engine_dir = get_engine_dir();
    
    let mut cmd = Command::new(&python_path);
    cmd.arg("-m").arg("engine").arg("--check-mic");
    cmd.current_dir(&engine_dir);
    hide_console(&mut cmd);
    
    let output = cmd.output()
        .map_err(|e| format!("Failed to check mic: {}", e))?;
    
    if output.status.success() {
        let result = String::from_utf8_lossy(&output.stdout).to_string();
        Ok(result)
    } else {
        let err = String::from_utf8_lossy(&output.stderr).to_string();
        error!("Check mic failed: {}", err);
        Err(err)
    }
}

#[tauri::command]
async fn check_ollama(app: tauri::AppHandle) -> Result<String, String> {
    info!("Checking Ollama");
    
    let python_path = get_python_path();
    let engine_dir = get_engine_dir();
    
    let mut cmd = Command::new(&python_path);
    cmd.arg("-m").arg("engine").arg("--check-ollama");
    cmd.current_dir(&engine_dir);
    hide_console(&mut cmd);
    
    let output = cmd.output()
        .map_err(|e| format!("Failed to check ollama: {}", e))?;
    
    if output.status.success() {
        let result = String::from_utf8_lossy(&output.stdout).to_string();
        Ok(result)
    } else {
        let err = String::from_utf8_lossy(&output.stderr).to_string();
        error!("Check ollama failed: {}", err);
        Err(err)
    }
}

#[tauri::command]
async fn install_ollama(app: tauri::AppHandle) -> Result<String, String> {
    info!("Installing Ollama");
    
    let python_path = get_python_path();
    let engine_dir = get_engine_dir();
    
    let mut cmd = Command::new(&python_path);
    cmd.arg("-m").arg("engine").arg("--install-ollama");
    cmd.current_dir(&engine_dir);
    hide_console(&mut cmd);
    
    let output = cmd.output()
        .map_err(|e| format!("Failed to install ollama: {}", e))?;
    
    if output.status.success() {
        let result = String::from_utf8_lossy(&output.stdout).to_string();
        Ok(result)
    } else {
        let err = String::from_utf8_lossy(&output.stderr).to_string();
        error!("Install ollama failed: {}", err);
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
            transcribe_spool,
            run_weave,
            run_ask,
            check_mic,
            check_ollama,
            install_ollama,
            get_engine_status
        ])
        .setup(|app| {
            info!("Tether starting up");
            
            // Log startup paths for debugging
            if let Ok(exe_path) = std::env::current_exe() {
                info!("Exe path: {:?}", exe_path);
                if let Some(parent) = exe_path.parent() {
                    info!("Exe parent dir: {:?}", parent);
                    
                    // Check for bundled resources in exe directory
                    let bundled_python = parent.join("python-runtime").join("Scripts").join("python.exe");
                    let bundled_engine = parent.join("engine");
                    
                    info!("Bundled python exists: {}", bundled_python.exists());
                    info!("Bundled engine exists: {}", bundled_engine.exists());
                }
            }
            
            // Check resource directory
            if let Ok(resource_dir) = app.path().resource_dir() {
                info!("Resource dir: {:?}", resource_dir);
                let resource_python = resource_dir.join("python-runtime").join("Scripts").join("python.exe");
                let resource_engine = resource_dir.join("engine");
                
                info!("Resource python exists: {}", resource_python.exists());
                info!("Resource engine exists: {}", resource_engine.exists());
                
                // If resources missing in both locations, warn
                let exe_parent = std::env::current_exe()
                    .ok()
                    .and_then(|p| p.parent().map(|p| p.to_path_buf()));
                    
                let has_python = exe_parent.as_ref()
                    .map(|p| p.join("python-runtime").join("Scripts").join("python.exe").exists())
                    .unwrap_or(false) || resource_python.exists();
                    
                let has_engine = exe_parent.as_ref()
                    .map(|p| p.join("engine").exists())
                    .unwrap_or(false) || resource_engine.exists();
                
                if !has_python || !has_engine {
                    warn!("MISSING RESOURCES: python={}, engine={}", has_python, has_engine);
                    if !has_python {
                        error!("Python runtime not found! App may not function correctly.");
                    }
                    if !has_engine {
                        error!("Engine folder not found! App may not function correctly.");
                    }
                }
            }
            
            // Ctrl+Alt+Space to toggle main window (toggle on press, not hold)
            let ctrl_alt_space = Shortcut::new(Some(Modifiers::CONTROL | Modifiers::ALT), Code::Space);
            let app_handle1 = app.handle().clone();
            if let Err(e) = app.global_shortcut().on_shortcut(ctrl_alt_space, move |_app, _shortcut, _event| {
                // Only toggle on initial key press, not on hold or release
                if _event.state() == ShortcutState::Pressed {
                    if let Some(window) = _app.get_webview_window("main") {
                        let is_visible = window.is_visible().unwrap_or(false);
                        if is_visible {
                            let _ = window.hide();
                        } else {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                }
            }) {
                warn!("Failed to register Ctrl+Alt+Space hotkey (may already be registered): {}", e);
            }
            
            // Ctrl+Shift+Space to start/stop recording (toggle on press, not hold)
            let ctrl_shift_space = Shortcut::new(Some(Modifiers::CONTROL | Modifiers::SHIFT), Code::Space);
            let app_handle2 = app.handle().clone();
            if let Err(e) = app.global_shortcut().on_shortcut(ctrl_shift_space, move |_app, _shortcut, _event| {
                // Only trigger on initial key press, not on hold or release
                if _event.state() == ShortcutState::Pressed {
                    info!("Ctrl+Shift+Space pressed");
                    let _ = app_handle2.emit("hotkey-recording-toggle", ());
                }
            }) {
                warn!("Failed to register Ctrl+Shift+Space hotkey (may already be registered): {}", e);
            }
            
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
