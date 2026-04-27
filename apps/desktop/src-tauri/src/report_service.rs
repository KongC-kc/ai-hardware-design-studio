use serde::Serialize;
use serde_json::Value;
use std::fs;
use std::path::{Component, Path, PathBuf};

#[derive(Debug, Serialize, PartialEq)]
pub struct ReportReadResult {
    pub success: bool,
    pub kind: String,
    pub path: Option<String>,
    pub data: Option<Value>,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
}

#[tauri::command]
pub fn read_report(project_path: String, kind: String) -> ReportReadResult {
    read_report_file(project_path, kind)
}

pub fn read_report_file(project_path: String, kind: String) -> ReportReadResult {
    let filename = match filename_for_kind(&kind) {
        Ok(filename) => filename,
        Err(error) => return empty_result(kind, None, vec![error], vec![]),
    };

    let trimmed_project_path = project_path.trim();
    if trimmed_project_path.is_empty() {
        return empty_result(kind, None, vec!["Project path must not be empty.".to_string()], vec![]);
    }

    let project_root = PathBuf::from(trimmed_project_path);
    if contains_parent_dir(&project_root) {
        return empty_result(
            kind,
            None,
            vec!["Project path must not contain '..' path traversal.".to_string()],
            vec![],
        );
    }
    if !project_root.exists() {
        return empty_result(
            kind,
            None,
            vec![format!("Project path not found: {}", project_root.display())],
            vec![],
        );
    }
    if !project_root.is_dir() {
        return empty_result(
            kind,
            None,
            vec![format!("Project path is not a directory: {}", project_root.display())],
            vec![],
        );
    }

    let reports_dir = project_root.join("reports");
    let report_path = reports_dir.join(filename);
    let report_path_text = path_to_string(&report_path);

    if !report_path.exists() {
        return empty_result(
            kind,
            Some(report_path_text),
            vec![format!("Report file not found: {}", report_path.display())],
            vec![],
        );
    }
    if !report_path.is_file() {
        return empty_result(
            kind,
            Some(report_path_text),
            vec![format!("Report path is not a file: {}", report_path.display())],
            vec![],
        );
    }
    if let Err(error) = validate_existing_report_path(&project_root, &reports_dir, &report_path) {
        return empty_result(kind, Some(report_path_text), vec![error], vec![]);
    }

    let report_text = match fs::read_to_string(&report_path) {
        Ok(text) => text,
        Err(error) => {
            return empty_result(
                kind,
                Some(report_path_text),
                vec![format!("Failed to read report file: {error}")],
                vec![],
            )
        }
    };
    let data = match serde_json::from_str::<Value>(&report_text) {
        Ok(data) => data,
        Err(error) => {
            return empty_result(
                kind,
                Some(report_path_text),
                vec![format!("Failed to parse report JSON: {error}")],
                vec![],
            )
        }
    };

    ReportReadResult {
        success: true,
        kind,
        path: Some(report_path_text),
        data: Some(data),
        errors: vec![],
        warnings: vec![],
    }
}

fn filename_for_kind(kind: &str) -> Result<&'static str, String> {
    if kind.contains('/') || kind.contains('\\') || kind.contains("..") {
        return Err("Report kind must not contain path separators or '..'.".to_string());
    }

    match kind {
        "erc_diagnostics" => Ok("erc_diagnostics.json"),
        "erc_explanation" => Ok("erc_explanation.json"),
        "generation_report" => Ok("generation_report.json"),
        _ => Err(format!("Unsupported report kind: {kind}")),
    }
}

fn validate_existing_report_path(
    project_root: &Path,
    reports_dir: &Path,
    report_path: &Path,
) -> Result<(), String> {
    let canonical_project = canonicalize_path(project_root, "project path")?;
    let canonical_reports = canonicalize_path(reports_dir, "reports directory")?;
    let canonical_report = canonicalize_path(report_path, "report path")?;

    if !canonical_reports.starts_with(&canonical_project) {
        return Err(format!(
            "Reports directory resolves outside project path: {}",
            canonical_reports.display()
        ));
    }
    if !canonical_report.starts_with(&canonical_reports) {
        return Err(format!(
            "Report path resolves outside reports directory: {}",
            canonical_report.display()
        ));
    }

    Ok(())
}

fn canonicalize_path(path: &Path, label: &str) -> Result<PathBuf, String> {
    fs::canonicalize(path).map_err(|error| format!("Failed to canonicalize {label}: {error}"))
}

fn contains_parent_dir(path: &Path) -> bool {
    path.components().any(|component| matches!(component, Component::ParentDir))
}

fn empty_result(
    kind: String,
    path: Option<String>,
    errors: Vec<String>,
    warnings: Vec<String>,
) -> ReportReadResult {
    ReportReadResult {
        success: false,
        kind,
        path,
        data: None,
        errors,
        warnings,
    }
}

fn path_to_string(path: &Path) -> String {
    path.to_string_lossy().to_string()
}

#[cfg(test)]
mod tests {
    use super::read_report_file;
    use serde_json::json;
    use std::fs;
    use std::path::{Path, PathBuf};
    use std::time::{SystemTime, UNIX_EPOCH};

    fn create_temp_project() -> PathBuf {
        let suffix = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system time should be after epoch")
            .as_nanos();
        let project_path = std::env::temp_dir().join(format!("ai-hw-report-service-{suffix}"));
        fs::create_dir_all(project_path.join("reports")).expect("reports directory should be created");
        project_path
    }

    fn write_json(path: &Path, value: serde_json::Value) {
        fs::write(path, serde_json::to_string_pretty(&value).expect("json should serialize"))
            .expect("json file should be written");
    }

    #[test]
    fn reads_whitelisted_erc_diagnostics_report() {
        let project_path = create_temp_project();
        write_json(
            &project_path.join("reports").join("erc_diagnostics.json"),
            json!({
                "success": true,
                "mode": "parse_erc_diagnostics",
                "summary": {"error_count": 0, "warning_count": 0, "info_count": 0},
                "diagnostics": []
            }),
        );

        let result = read_report_file(project_path.to_string_lossy().to_string(), "erc_diagnostics".to_string());

        assert!(result.success, "{:?}", result.errors);
        assert_eq!(result.kind, "erc_diagnostics");
        let path = result.path.expect("path should be present");
        assert!(
            path.ends_with("reports\\erc_diagnostics.json")
                || path.ends_with("reports/erc_diagnostics.json")
        );
        assert_eq!(
            result.data.expect("data should be present")["mode"],
            json!("parse_erc_diagnostics")
        );
    }

    #[test]
    fn reads_whitelisted_generation_report() {
        let project_path = create_temp_project();
        write_json(
            &project_path.join("reports").join("generation_report.json"),
            json!({"success": true, "mode": "generate_kicad_artifacts", "written_files": []}),
        );

        let result = read_report_file(project_path.to_string_lossy().to_string(), "generation_report".to_string());

        assert!(result.success, "{:?}", result.errors);
        assert_eq!(result.kind, "generation_report");
        assert_eq!(
            result.data.expect("data should be present")["mode"],
            json!("generate_kicad_artifacts")
        );
    }

    #[test]
    fn reads_whitelisted_erc_explanation_report() {
        let project_path = create_temp_project();
        write_json(
            &project_path.join("reports").join("erc_explanation.json"),
            json!({"success": true, "mode": "explain_erc_report", "explanations": []}),
        );

        let result = read_report_file(project_path.to_string_lossy().to_string(), "erc_explanation".to_string());

        assert!(result.success, "{:?}", result.errors);
        assert_eq!(result.kind, "erc_explanation");
        let path = result.path.expect("path should be present");
        assert!(
            path.ends_with("reports\\erc_explanation.json")
                || path.ends_with("reports/erc_explanation.json")
        );
        assert_eq!(
            result.data.expect("data should be present")["mode"],
            json!("explain_erc_report")
        );
    }

    #[test]
    fn missing_report_returns_structured_empty_state() {
        let project_path = create_temp_project();

        let result = read_report_file(project_path.to_string_lossy().to_string(), "erc_diagnostics".to_string());

        assert!(!result.success);
        assert_eq!(result.kind, "erc_diagnostics");
        assert!(result.path.is_some());
        assert!(result.data.is_none());
        assert!(result.errors.join(" ").contains("not found"));
    }

    #[test]
    fn rejects_unknown_kind() {
        let project_path = create_temp_project();

        let result = read_report_file(project_path.to_string_lossy().to_string(), "raw_log".to_string());

        assert!(!result.success);
        assert!(result.path.is_none());
        assert!(result.errors.join(" ").contains("Unsupported report kind"));
    }

    #[test]
    fn rejects_kind_with_path_segments() {
        let project_path = create_temp_project();

        let result = read_report_file(
            project_path.to_string_lossy().to_string(),
            "../erc_diagnostics".to_string(),
        );

        assert!(!result.success);
        assert!(result.path.is_none());
        assert!(result.errors.join(" ").contains("must not contain path"));
    }

    #[test]
    fn rejects_project_path_traversal() {
        let result = read_report_file("project/../secret".to_string(), "erc_diagnostics".to_string());

        assert!(!result.success);
        assert!(result.path.is_none());
        assert!(result.errors.join(" ").contains("must not contain '..'"));
    }
}
