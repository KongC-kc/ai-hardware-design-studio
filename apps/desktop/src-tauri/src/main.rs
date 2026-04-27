mod report_service;

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![report_service::read_report])
        .run(tauri::generate_context!())
        .expect("failed to run AI Hardware Design Studio");
}
