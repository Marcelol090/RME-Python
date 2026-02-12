# Security Suggestions

- Generated at: `2026-02-11T12:00:00Z`
- Category: `security`
- Task: `security-scan-and-fix`

## Implemented

- [SEC-001] Fixed timing attack vulnerability in LiveServer password comparison using secrets.compare_digest.
  - files: `py_rme_canary/core/protocols/live_server.py`
  - evidence: Verified with unit tests in `py_rme_canary/tests/unit/core/protocols/test_live_server_security.py`

- [SEC-002] Verified usage of defusedxml for safe XML parsing to prevent XXE attacks.
  - files: `py_rme_canary/core/io/xml/safe.py`, `py_rme_canary/core/io/lua_creature_import.py`

- [SEC-003] Verified ScriptEngine sandbox implementation blocking dangerous AST nodes.
  - files: `py_rme_canary/logic_layer/script_engine.py`

- [SEC-004] Fixed authentication bypass vulnerability where unauthenticated clients could send messages and updates.
  - files: `py_rme_canary/core/protocols/live_server.py`, `py_rme_canary/core/protocols/live_peer.py`
  - evidence: Verified with reproduction test case in `py_rme_canary/tests/unit/core/protocols/test_live_server_auth_bypass.py`

## Suggested Next

- [CRITICAL] [SUG-SEC-001] Implement TLS encryption for LiveServer connections.
  - rationale: Passwords and map data are currently transmitted in plain text. TLS is required to prevent eavesdropping and MITM attacks.
  - links: https://docs.python.org/3/library/ssl.html

- [HIGH] [SUG-SEC-002] Implement Rate Limiting for LiveServer.
  - rationale: Lack of rate limiting exposes the server to DoS attacks. Implement token bucket or leaky bucket algorithm per IP.
