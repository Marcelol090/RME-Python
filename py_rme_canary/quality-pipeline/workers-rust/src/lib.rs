// Quality Pipeline Rust Worker - v3.0
// PyO3 FFI for gradual Python→Rust migration

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

/// Analysis result for single file
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct AnalysisResult {
    #[pyo3(get, set)]
    pub file: String,

    #[pyo3(get, set)]
    pub issues: Vec<Issue>,

    #[pyo3(get, set)]
    pub complexity: u32,

    #[pyo3(get, set)]
    pub duration_ms: u64,
}

#[pymethods]
impl AnalysisResult {
    #[new]
    fn new(file: String, issues: Vec<Issue>, complexity: u32, duration_ms: u64) -> Self {
        Self {
            file,
            issues,
            complexity,
            duration_ms,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "AnalysisResult(file='{}', issues={}, complexity={})",
            self.file,
            self.issues.len(),
            self.complexity
        )
    }
}

/// Individual code issue
#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct Issue {
    #[pyo3(get, set)]
    pub line: usize,

    #[pyo3(get, set)]
    pub column: usize,

    #[pyo3(get, set)]
    pub severity: String,

    #[pyo3(get, set)]
    pub message: String,

    #[pyo3(get, set)]
    pub rule_id: String,
}

#[pymethods]
impl Issue {
    #[new]
    fn new(line: usize, column: usize, severity: String, message: String, rule_id: String) -> Self {
        Self {
            line,
            column,
            severity,
            message,
            rule_id,
        }
    }
}

/// Fast file scanner (10-100x faster than Python glob)
#[pyfunction]
fn scan_python_files(root_path: String, exclude_patterns: Vec<String>) -> PyResult<Vec<String>> {
    let root = Path::new(&root_path);

    let files: Vec<String> = WalkDir::new(root)
        .follow_links(false)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| {
            let path = e.path();

            // Check if file is .py
            if !path.extension().map_or(false, |ext| ext == "py") {
                return false;
            }

            // Check exclusion patterns
            let path_str = path.to_string_lossy();
            for pattern in &exclude_patterns {
                if path_str.contains(pattern) {
                    return false;
                }
            }

            true
        })
        .map(|e| e.path().to_string_lossy().into_owned())
        .collect();

    Ok(files)
}

/// Parallel file hash computation (for cache invalidation)
#[pyfunction]
fn hash_files(file_paths: Vec<String>) -> PyResult<HashMap<String, String>> {
    use sha2::{Digest, Sha256};

    let hashes: HashMap<String, String> = file_paths
        .par_iter()
        .filter_map(|path| {
            let content = fs::read(path).ok()?;
            let mut hasher = Sha256::new();
            hasher.update(&content);
            let hash = format!("{:x}", hasher.finalize());
            Some((path.clone(), hash))
        })
        .collect();

    Ok(hashes)
}

/// Fast complexity analyzer (simplified Radon)
#[pyfunction]
fn analyze_complexity(source: String) -> PyResult<u32> {
    // Simplified complexity metric:
    // Count control flow keywords
    let keywords = [
        "if", "elif", "else", "for", "while",
        "try", "except", "finally", "with", "match", "case"
    ];

    let mut complexity = 1; // Base complexity

    for keyword in &keywords {
        let count = source.matches(keyword).count();
        complexity += count as u32;
    }

    Ok(complexity)
}

/// Batch analysis (parallel processing)
#[pyfunction]
fn analyze_files_batch(
    file_paths: Vec<String>,
    max_workers: Option<usize>
) -> PyResult<Vec<AnalysisResult>> {
    use std::time::Instant;

    // Configure thread pool
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(max_workers.unwrap_or_else(num_cpus::get))
        .build()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;

    let results: Vec<AnalysisResult> = pool.install(|| {
        file_paths
            .par_iter()
            .filter_map(|path| {
                let start = Instant::now();

                // Read file
                let source = fs::read_to_string(path).ok()?;

                // Analyze
                let complexity = analyze_complexity(source.clone()).ok()?;

                // Detect issues (simplified)
                let issues = detect_issues(&source, path);

                let duration_ms = start.elapsed().as_millis() as u64;

                Some(AnalysisResult {
                    file: path.clone(),
                    issues,
                    complexity,
                    duration_ms,
                })
            })
            .collect()
    });

    Ok(results)
}

/// Simple issue detection (proof-of-concept)
fn detect_issues(source: &str, file_path: &str) -> Vec<Issue> {
    let mut issues = Vec::new();

    for (line_num, line) in source.lines().enumerate() {
        // Detect bare except
        if line.trim() == "except:" {
            issues.push(Issue {
                line: line_num + 1,
                column: line.find("except:").unwrap_or(0),
                severity: "warning".to_string(),
                message: "Bare 'except:' clause - specify exception type".to_string(),
                rule_id: "E722".to_string(),
            });
        }

        // Detect mutable defaults (simplified)
        if line.contains("def ") && line.contains("=[]") {
            issues.push(Issue {
                line: line_num + 1,
                column: line.find("=[]").unwrap_or(0),
                severity: "error".to_string(),
                message: "Mutable default argument".to_string(),
                rule_id: "B006".to_string(),
            });
        }

        // Detect print statements
        if line.contains("print(") && !line.trim_start().starts_with('#') {
            issues.push(Issue {
                line: line_num + 1,
                column: line.find("print(").unwrap_or(0),
                severity: "info".to_string(),
                message: "Use logging instead of print()".to_string(),
                rule_id: "T201".to_string(),
            });
        }
    }

    issues
}

/// Cache key generator (deterministic)
#[pyfunction]
fn generate_cache_key(file_path: String, config_hash: String) -> PyResult<String> {
    use sha2::{Digest, Sha256};

    let input = format!("{}:{}", file_path, config_hash);
    let mut hasher = Sha256::new();
    hasher.update(input.as_bytes());
    let hash = format!("{:x}", hasher.finalize());

    Ok(hash[..16].to_string())
}

/// Python module definition
#[pymodule]
fn quality_worker_rust(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(scan_python_files, m)?)?;
    m.add_function(wrap_pyfunction!(hash_files, m)?)?;
    m.add_function(wrap_pyfunction!(analyze_complexity, m)?)?;
    m.add_function(wrap_pyfunction!(analyze_files_batch, m)?)?;
    m.add_function(wrap_pyfunction!(generate_cache_key, m)?)?;

    m.add_class::<AnalysisResult>()?;
    m.add_class::<Issue>()?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_complexity_simple() {
        let source = "def foo():\n    if x:\n        return 1".to_string();
        let complexity = analyze_complexity(source).unwrap();
        assert_eq!(complexity, 2); // Base 1 + if 1
    }

    #[test]
    fn test_detect_bare_except() {
        let source = "try:\n    pass\nexcept:\n    pass";
        let issues = detect_issues(source, "test.py");
        assert_eq!(issues.len(), 1);
        assert_eq!(issues[0].rule_id, "E722");
    }
}
