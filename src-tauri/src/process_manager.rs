use log::{info, error, warn};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::process::Command;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct EngineStatus {
    pub pid: Option<u32>,
    pub status: String,
    pub task: Option<String>,
    pub started_at: Option<String>,
}

impl Default for EngineStatus {
    fn default() -> Self {
        Self {
            pid: None,
            status: "idle".to_string(),
            task: None,
            started_at: None,
        }
    }
}

fn get_status_file_path() -> PathBuf {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    home.join(".tether").join("engine_status.json")
}

pub fn read_status_file() -> Result<EngineStatus, String> {
    let path = get_status_file_path();
    
    if !path.exists() {
        return Ok(EngineStatus::default());
    }
    
    let content = fs::read_to_string(&path)
        .map_err(|e| format!("Failed to read status file: {}", e))?;
    
    let status: EngineStatus = serde_json::from_str(&content)
        .map_err(|e| format!("Failed to parse status file: {}", e))?;
    
    Ok(status)
}

pub fn write_status_file(status: &EngineStatus) -> Result<(), String> {
    let path = get_status_file_path();
    
    // Ensure directory exists
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|e| format!("Failed to create .tether directory: {}", e))?;
    }
    
    let content = serde_json::to_string_pretty(status)
        .map_err(|e| format!("Failed to serialize status: {}", e))?;
    
    fs::write(&path, content)
        .map_err(|e| format!("Failed to write status file: {}", e))?;
    
    Ok(())
}

pub fn update_status(status: &str, task: Option<&str>) -> Result<EngineStatus, String> {
    let mut current = read_status_file().unwrap_or_default();
    current.status = status.to_string();
    current.task = task.map(|s| s.to_string());
    
    if status == "busy" || status == "recording" {
        current.started_at = Some(chrono_lite_now());
    } else {
        current.started_at = None;
    }
    
    write_status_file(&current)?;
    Ok(current)
}

fn chrono_lite_now() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let duration = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default();
    let secs = duration.as_secs();
    
    // Simple timestamp: YYYY-MM-DD HH:MM:SS
    let days = secs / 86400;
    let remaining = secs % 86400;
    let hours = remaining / 3600;
    let minutes = (remaining % 3600) / 60;
    let seconds = remaining % 60;
    
    // Calculate year, month, day (simplified)
    let mut year = 1970;
    let mut remaining_days = days as i64;
    
    while remaining_days >= 365 {
        let leap = if year % 4 == 0 && (year % 100 != 0 || year % 400 == 0) { 366 } else { 365 };
        if remaining_days >= leap {
            remaining_days -= leap;
            year += 1;
        } else {
            break;
        }
    }
    
    let is_leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
    let days_in_months = if is_leap {
        [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    } else {
        [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    };
    
    let mut month = 1;
    for days_in_month in days_in_months.iter() {
        if remaining_days < *days_in_month as i64 {
            break;
        }
        remaining_days -= *days_in_month as i64;
        month += 1;
    }
    
    let day = remaining_days + 1;
    
    format!("{:04}-{:02}-{:02} {:02}:{:02}:{:02}", 
            year, month, day, hours, minutes, seconds)
}

pub fn is_process_running(pid: u32) -> bool {
    // On Windows, use tasklist to check if process exists
    let output = Command::new("tasklist")
        .args(["/FI", &format!("PID eq {}", pid), "/NH"])
        .output();
    
    match output {
        Ok(out) => {
            let result = String::from_utf8_lossy(&out.stdout);
            // If process exists, tasklist will return a line with the PID
            !result.is_empty() && !result.contains("INFO: No tasks")
        }
        Err(_) => false,
    }
}

pub fn kill_process(pid: u32) -> bool {
    info!("Attempting to kill process {}", pid);
    
    // First try graceful kill (CTRL_BREAK_EVENT equivalent)
    let graceful = Command::new("taskkill")
        .args(["/PID", &pid.to_string()])
        .spawn();
    
    if graceful.is_ok() {
        // Wait up to 15 seconds for graceful shutdown
        std::thread::sleep(std::time::Duration::from_secs(15));
        
        // Check if still running
        if !is_process_running(pid) {
            info!("Process {} terminated gracefully", pid);
            return true;
        }
        
        warn!("Process {} still running after graceful kill, forcing...", pid);
    }
    
    // Force kill
    let force = Command::new("taskkill")
        .args(["/F", "/PID", &pid.to_string()])
        .spawn();
    
    if force.is_ok() {
        std::thread::sleep(std::time::Duration::from_millis(500));
        
        if !is_process_running(pid) {
            info!("Process {} force killed", pid);
            
            // Update status file
            let _ = write_status_file(&EngineStatus::default());
            
            return true;
        }
    }
    
    error!("Failed to kill process {}", pid);
    false
}
