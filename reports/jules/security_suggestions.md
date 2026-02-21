# Security Suggestions

- Generated at: `2026-02-13T10:00:00Z`
- Category: `security`
- Task: `security-scan-and-fix`

## Implemented

- [SEC-007] Fixed Partial Read DoS vulnerability in LiveSocket by implementing non-blocking buffering (process_incoming_data).
  - files: `py_rme_canary/core/protocols/live_socket.py`, `py_rme_canary/core/protocols/live_server.py`, `py_rme_canary/core/protocols/live_peer.py`
  - evidence: Verified with reproduction test case `tests/reproduce_issue/test_live_socket_dos_partial.py` which now passes.

- [SEC-005] Fixed DoS vulnerability in LiveSocket where unlimited payload size could lead to OOM attacks.
  - files: `py_rme_canary/core/protocols/live_socket.py`
  - evidence: Verified with reproduction test case in `py_rme_canary/tests/unit/core/protocols/test_live_socket_security.py`

- [SEC-006] Fixed regression in ItemTypeDetector where door lookups were failing due to missing definitions.
  - files: `py_rme_canary/logic_layer/item_type_detector.py`
  - evidence: Verified with existing unit tests in `py_rme_canary/tests/unit/logic_layer/test_item_type_detector.py`

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

- [SEC-007] Implemented Rate Limiting and Map Request Size Limits for LiveServer to mitigate DoS attacks.
  - files: `py_rme_canary/core/protocols/live_server.py`, `py_rme_canary/core/protocols/live_peer.py`
  - evidence: Verified with `py_rme_canary/tests/unit/core/protocols/test_live_server_dos.py` (50 packets/second limit + oversized map request rejection).

- [SEC-008] Fixed Sandbox Escape vulnerability in ScriptEngine by blocking access to generator and frame attributes (gi_frame, f_back, etc).
  - files: `py_rme_canary/logic_layer/script_engine.py`
  - evidence: Verified with `py_rme_canary/tests/unit/logic_layer/test_script_engine_security.py`

- [SEC-009] Fixed Stored XSS vulnerability in ChatDialog by escaping HTML content in messages.
  - files: `py_rme_canary/vis_layer/ui/dialogs/chat_dialog.py`
  - evidence: Verified with `py_rme_canary/tests/unit/vis_layer/ui/test_chat_dialog_security.py`

## Suggested Next

- [CRITICAL] [SUG-SEC-001] Implement TLS encryption for LiveServer connections.
  - rationale: Passwords and map data are currently transmitted in plain text. TLS is required to prevent eavesdropping and MITM attacks.
  - links: https://docs.python.org/3/library/ssl.html
