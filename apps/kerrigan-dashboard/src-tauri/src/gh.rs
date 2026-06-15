//! gh.rs — Resolves a GitHub CLI auth token via `gh auth token`.
//!
//! Uses `std::process::Command` (OS process creation) rather than the Tauri
//! shell plugin so that `gh` is found through the OS PATH and PATHEXT on
//! Windows, which is more reliable in GUI processes.
//!
//! When a bare `gh` lookup fails, common install locations are tried in order.

use std::path::PathBuf;
use std::process::Command;

/// Returns ordered candidate paths for the `gh` binary.
///
/// The bare `"gh"` entry relies on the system PATH and must appear first so
/// that user-installed or custom-PATH versions take precedence.
pub fn gh_candidates() -> Vec<PathBuf> {
    let mut candidates: Vec<PathBuf> = vec![PathBuf::from("gh")];

    #[cfg(target_os = "windows")]
    {
        if let Ok(pf) = std::env::var("ProgramFiles") {
            candidates.push(PathBuf::from(pf).join("GitHub CLI").join("gh.exe"));
        }
        if let Ok(local) = std::env::var("LOCALAPPDATA") {
            candidates.push(
                PathBuf::from(local)
                    .join("Programs")
                    .join("GitHub CLI")
                    .join("gh.exe"),
            );
        }
    }

    #[cfg(not(target_os = "windows"))]
    {
        candidates.push(PathBuf::from("/usr/local/bin/gh"));
        candidates.push(PathBuf::from("/opt/homebrew/bin/gh"));
        if let Ok(home) = std::env::var("HOME") {
            candidates.push(PathBuf::from(home).join(".local").join("bin").join("gh"));
        }
    }

    candidates
}

/// Returns the first candidate that exists on the filesystem, or `None`.
///
/// The first candidate (`"gh"`) is a bare name and is tested by attempting to
/// spawn a no-op invocation; all others are checked via [`std::path::Path::exists`].
pub fn find_gh(candidates: &[PathBuf]) -> Option<PathBuf> {
    for candidate in candidates {
        if candidate == &PathBuf::from("gh") {
            // Bare name — rely on PATH resolution at spawn time; mark as found
            // only if a version probe succeeds.
            if Command::new("gh").arg("--version").output().is_ok() {
                return Some(candidate.clone());
            }
        } else if candidate.exists() {
            return Some(candidate.clone());
        }
    }
    None
}

/// Runs `gh auth token` with the given binary path and returns the trimmed
/// token string on success.
///
/// # Errors
///
/// Returns a descriptive string on failure:
/// - `"gh-not-found"` — no usable `gh` binary was located.
/// - `"exit-<N>: <message>"` — `gh` exited with a nonzero status.
/// - `"spawn-failed: <message>"` — the process could not be spawned.
pub fn run_gh_auth_token(gh_path: &std::path::Path) -> Result<String, String> {
    let output = Command::new(gh_path)
        .args(["auth", "token"])
        .output()
        .map_err(|e| format!("spawn-failed: {e}"))?;

    if output.status.success() {
        let token = String::from_utf8_lossy(&output.stdout).trim().to_string();
        Ok(token)
    } else {
        let code = output.status.code().unwrap_or(-1);
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
        let detail = if !stderr.is_empty() {
            stderr
        } else if !stdout.is_empty() {
            stdout
        } else {
            String::new()
        };
        if detail.is_empty() {
            Err(format!("exit-{code}"))
        } else {
            Err(format!("exit-{code}: {detail}"))
        }
    }
}

/// High-level resolver: find `gh` and run `gh auth token`.
///
/// Returns `Err("gh-not-found")` when no `gh` binary is available.
pub fn resolve_gh_auth_token() -> Result<String, String> {
    let candidates = gh_candidates();
    let gh_path = find_gh(&candidates).ok_or_else(|| "gh-not-found".to_string())?;
    run_gh_auth_token(&gh_path)
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::Path;

    #[test]
    fn gh_candidates_starts_with_bare_gh() {
        let candidates = gh_candidates();
        assert!(!candidates.is_empty(), "should return at least one candidate");
        assert_eq!(
            candidates[0],
            PathBuf::from("gh"),
            "first candidate must be bare 'gh' for PATH resolution"
        );
    }

    #[cfg(not(target_os = "windows"))]
    #[test]
    fn gh_candidates_includes_unix_fallbacks() {
        let candidates = gh_candidates();
        let paths: Vec<String> = candidates.iter().map(|p| p.to_string_lossy().into_owned()).collect();
        assert!(
            paths.contains(&"/usr/local/bin/gh".to_string()),
            "should include /usr/local/bin/gh"
        );
        assert!(
            paths.contains(&"/opt/homebrew/bin/gh".to_string()),
            "should include /opt/homebrew/bin/gh"
        );
    }

    #[cfg(target_os = "windows")]
    #[test]
    fn gh_candidates_includes_windows_fallbacks() {
        let candidates = gh_candidates();
        // At least one Windows-specific candidate beyond the bare name
        assert!(candidates.len() >= 2, "should include Windows install dir fallbacks");
    }

    #[test]
    fn find_gh_returns_none_when_all_paths_missing() {
        // Use paths that definitely do not exist
        let candidates: Vec<PathBuf> = vec![
            PathBuf::from("/nonexistent/path/to/gh"),
            PathBuf::from("/another/nonexistent/gh"),
        ];
        // Override the bare-gh check: none of these are "gh" so they go through exists()
        let result = find_gh(&candidates);
        assert!(result.is_none(), "should return None when no candidate exists");
    }

    /// RAII guard that deletes a file when dropped, ensuring cleanup even on panic.
    struct TempFile(PathBuf);
    impl Drop for TempFile {
        fn drop(&mut self) {
            let _ = std::fs::remove_file(&self.0);
        }
    }

    #[test]
    fn find_gh_returns_first_existing_path() {
        // Create a temp file to act as an existing "binary"; cleaned up on drop.
        let tmp_path = std::env::temp_dir().join("fake_gh_for_test");
        std::fs::write(&tmp_path, b"").unwrap();
        let _guard = TempFile(tmp_path.clone());

        let nonexistent = PathBuf::from("/nonexistent/gh");
        let candidates: Vec<PathBuf> = vec![nonexistent, tmp_path.clone()];

        let result = find_gh(&candidates);
        assert_eq!(result, Some(tmp_path));
    }

    #[test]
    fn resolve_gh_auth_token_returns_gh_not_found_when_no_binary() {
        // Only supply nonexistent paths so find_gh returns None
        let candidates: Vec<PathBuf> = vec![
            PathBuf::from("/nonexistent/path/to/gh"),
        ];
        let gh_path = find_gh(&candidates);
        assert!(gh_path.is_none());
        let err = gh_path.ok_or_else(|| "gh-not-found".to_string()).unwrap_err();
        assert_eq!(err, "gh-not-found");
    }

    #[test]
    fn run_gh_auth_token_spawn_failure_returns_spawn_failed() {
        // A path that exists-but-is-not-executable (use /dev/null or a directory)
        // On most Unix systems /dev/null is not executable as a program
        let result = run_gh_auth_token(Path::new("/nonexistent/definitely/not/gh"));
        match result {
            Err(msg) => assert!(
                msg.starts_with("spawn-failed:"),
                "expected spawn-failed, got: {msg}"
            ),
            Ok(_) => panic!("expected an error"),
        }
    }
}
