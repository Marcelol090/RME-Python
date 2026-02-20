# Security Suggestions

## Implemented

### JULES-SEC-001: Block frame traversal in ScriptEngine sandbox
- **Summary**: The `ScriptEngine` sandbox was vulnerable to stack traversal attacks via generator/coroutine frame objects (`gi_frame`, `cr_frame`, etc.). This allowed scripts to escape the sandbox and access the real `__builtins__` or global scope.
- **Fix**: Added `gi_frame`, `cr_frame`, `ag_frame`, `f_back`, `f_globals`, `f_locals`, `f_builtins`, `f_code` to the `ScriptSecurityChecker` blacklist.
- **Files**: `py_rme_canary/logic_layer/script_engine.py`

## Suggested Next Steps

### JULES-SEC-002: LiveServer password sent in plaintext
- **Severity**: HIGH
- **Summary**: The `LiveServer` protocol transmits passwords in plaintext (or basic encoding). Without SSL/TLS, this is vulnerable to interception on untrusted networks.
- **Rationale**: Implementing SSL/TLS encryption for the `LiveSocket` connection would mitigate this.

### JULES-SEC-003: Review Hardcoded Secrets in Tests
- **Severity**: LOW
- **Summary**: Some test files may contain hardcoded credentials or tokens. While not a production risk, they should be cleaned up or rotated if they were ever real.
