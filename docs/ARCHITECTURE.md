# OBLISK Architecture

> ⚠️ **Accuracy Notice**
> Architecture descriptions below reflect the design vision. The
> **Implementation Status** table is the authoritative record of what is
> currently shipped vs. planned. All ✅ Implemented claims are backed by
> passing unit tests. 🔶 Partial means the feature exists but is incomplete
> or untested. 🔲 Planned means the feature is not yet implemented.

---

## Implementation Status

> Last updated: 2026-02-24

| Component | Feature | Status | Notes |
|-----------|---------|--------|-------|
| **Vault** | Key-value store API (store/retrieve/delete/list) | ✅ Implemented | Fully tested |
| **Vault** | AES-256-GCM encryption (per-call random nonce) | ✅ Implemented | `vault/crypto.py` — replaces base64 stub |
| **Vault** | PBKDF2-HMAC-SHA256 key derivation (600k iter) | ✅ Implemented | `derive_key()` in `vault/crypto.py` |
| **Vault** | Key rotation (`rotate_key()`) | ✅ Implemented | Re-encrypts all secrets under new key |
| **Vault** | Persistent JSON storage | ✅ Implemented | Encrypted blobs; JSON file backend |
| **Vault** | GCM tamper detection | ✅ Implemented | `InvalidTag` raised on any corruption |
| **Agents** | Agent lifecycle (start/stop/pause/resume) | ✅ Implemented | Fully tested |
| **Agents** | `execute_task()` returning result dict | ✅ Implemented | Fully tested |
| **Agents** | Task queue (assign/wait API) | 🔲 Planned | Issue #7 |
| **Agents** | Multi-agent coordination (AgentManager) | 🔶 Partial | Class exists; distribution logic pending |
| **Core** | GovernanceEngine (policy CRUD + eval) | 🔶 Partial | Partially tested |
| **Core** | Governance audit log export | 🔶 Partial | `get_audit_log()` present, format TBD |
| **Core** | SymbolicPlanner (greedy forward search) | ✅ Implemented | **Not PDDL** — custom greedy algorithm |
| **Core** | PDDL integration | 🔲 Planned | Requires external PDDL solver |
| **CI** | Real pytest pipeline (4-job) | ✅ Implemented | lint/test/build/smoke |
| **CI** | 100% line + branch coverage enforcement | ✅ Implemented | `--cov-fail-under=100` |
| **CI** | SHA-pinned GitHub Actions | ✅ Implemented | All `uses:` lines pinned to commit SHAs |
| **Security** | OpenSSF Scorecard workflow | ✅ Implemented | `scorecard.yml` — runs weekly + on push |
| **Security** | CodeQL SAST (Python) | ✅ Implemented | `codeql.yml` — security-extended queries |
| **Security** | Signed releases (Sigstore) | 🔲 Planned | Issue #13 |
| **Security** | SLSA Level 3 provenance | 🔲 Planned | Issue #13 |
| **Security** | Branch protection rules | 🔲 Planned | Manual setup — Issue #13 |

---

## System Overview

OBLISK is a multi-agent AI orchestration framework built around three core
subsystems: the **Vault** (secure secret storage), the **Agent Layer**
(autonomous task execution), and the **Core Layer** (governance + planning).

```
┌─────────────────────────────────────────────────────────┐
│                     OBLISK Framework                       │
├──────────────────┬─────────────────┬───────────────────┤
│   Vault Layer     │  Agent Layer    │    Core Layer        │
│                  │                 │                     │
│ AES-256-GCM      │ Agent           │ GovernanceEngine    │
│ Authenticated    │ AgentManager    │ SymbolicPlanner     │
│ Encryption       │ Task Execution  │ Policy Evaluation   │
│ PBKDF2 KDF       │ Lifecycle Mgmt  │ Audit Logging       │
│ Key Rotation     │                 │                     │
└──────────────────┴─────────────────┴───────────────────┘
```

---

## Vault Layer

The Vault provides **AES-256-GCM authenticated encryption** for all sensitive
data. The encryption is performed in `vault/crypto.py` using the
`cryptography` library's `AESGCM` primitive (OpenSSL-backed).

**Key properties:**
- Every `store()` call generates a fresh 96-bit random nonce (NIST SP 800-38D)
- The 128-bit GCM authentication tag detects any tampering before decryption
- `InvalidTag` is raised — no plaintext is ever returned from a tampered blob
- Keys are 32 bytes (256-bit); use `derive_key()` to generate from a passphrase
  via PBKDF2-HMAC-SHA256 at 600,000 iterations (OWASP 2023)
- `rotate_key(new_key)` re-encrypts all secrets atomically

---

## Agent Layer

Agents are autonomous execution units managed by `AgentManager`. Each agent
has a lifecycle state (`IDLE → RUNNING → PAUSED → STOPPED`) and executes
tasks via `execute_task(task_dict)`.

**Planned additions (Issue #7):** a `Task` dataclass with `assign_task()` /
`wait_for_task()` queue API.

---

## Core Layer

### GovernanceEngine

Evaluates agent actions against registered policies. Every evaluation is
recorded in an audit log with `agent_id`, `action`, `decision`, and
`timestamp`. Policy CRUD is available via `add_policy()` / `list_policies()`.

### SymbolicPlanner

Implements a **greedy forward search** over a symbolic state space. Given a
goal dict and an optional context, the planner returns an ordered list of
action steps. **This is not a PDDL planner** — PDDL integration requiring an
external solver is planned (see status matrix).

---

## Security Model

| Property | Mechanism |
|----------|-----------|
| Confidentiality | AES-256-GCM (256-bit key) |
| Integrity | GCM authentication tag (128-bit) |
| Key derivation | PBKDF2-HMAC-SHA256 @ 600k iterations |
| Nonce generation | `os.urandom(12)` per encryption call |
| Supply chain | SHA-pinned GitHub Actions + Dependabot |
| SAST | CodeQL Python (security-extended queries) |
| Dependency updates | Dependabot weekly PRs |

---

## Directory Structure

```
OBLISK/
├── agents/                 # Agent + AgentManager
│   ├── agent.py
│   └── agent_manager.py
├── core/                   # GovernanceEngine + SymbolicPlanner
│   ├── governance_engine.py
│   └── symbolic_planner.py
├── vault/                  # AES-256-GCM encrypted vault
│   ├── crypto.py           # Primitive: encrypt/decrypt/derive_key
│   └── vault.py            # High-level Vault class
├── tests/
│   ├── conftest.py
│   └── unit/               # Unit tests targeting 100% coverage
├── examples/
│   └── simple_agent.py     # Runnable demo
├── .github/
│   ├── workflows/
│   │   ├── ci.yml          # 4-job pipeline (lint/test/build/smoke)
│   │   ├── scorecard.yml   # OpenSSF Scorecard (weekly + push)
│   │   ├── codeql.yml      # CodeQL SAST (Python)
│   │   ├── release.yml     # Tagged release automation
│   │   └── build-exe.yml   # Windows EXE build
│   └── dependabot.yml      # Weekly updates: pip + github-actions
├── pyproject.toml          # PEP 517/518 build + tool config
├── SECURITY.md
└── ENHANCEMENT_ROADMAP.md
```
