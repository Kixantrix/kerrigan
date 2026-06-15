mod gh;

#[tauri::command]
fn shell_ready() -> bool {
    true
}

#[tauri::command]
fn gh_auth_token() -> Result<String, String> {
    gh::resolve_gh_auth_token()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![shell_ready, gh_auth_token])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
