# OBLISK v2 — Human-Sovereign Architecture

## The Obelisk Metaphor

OBLISK v2 is structured like its namesake — an obelisk:

```
                    ▲
                   /█\         THE APEX (Symbolic Planner)
                  /███\        Proof trees. Goal decomposition.
                 /█████\       Constraint verification.
                /███████\
               ━━━━━━━━━━━     THE CONDUIT (Flow Controller)
               │ ███████ │     One-directional flow. Intent verification.
               │ ███████ │     Constraint engine. Proof collector.
               │ ███████ │
               │ ███████ │
               │ ███████ │     THE SHIELD (Data Guardian)
               │ ███████ │     Inference filter. Exfiltration detection.
               │ ███████ │     User alerts.
               ━━━━━━━━━━━
              ┌───────────┐    THE BASE (Vault)
              │ ▓▓▓▓▓▓▓▓▓ │    Human identity. Policy store.
              │ ▓▓▓▓▓▓▓▓▓ │    Signed intents. Consent log.
              │ ▓▓▓▓▓▓▓▓▓ │
              └───────────┘
                   
              ◯ HUMAN        THE CAPSTONE (You)
                             You are the key. You are the law.
```

## Architectural Flow

```
Human Intent
      │
      ▼
┌──────────────┐
│ IntentParser │──→ Natural language → Governed intent
└──────────────┘
      │
      ▼
┌──────────┐
│ Identity │──→ Sovereign key ceremony → "You ARE the key"
│  Store   │
└──────────┘
      │
      ▼
┌──────────┐
│  Intent  │──→ Cryptographic signing → Non-repudiable authorization
│  Store   │
└──────────┘
      │
      ▼
┌──────────┐
│  Policy  │──→ Human-authored Datalog rules → The Law
│  Store   │
└──────────┘
      │
      ▼
┌──────────────┐
│FlowController│──→ Intent verification + Constraint checking → THE GATE
└──────────────┘
      │
      ▼
┌──────────────┐
│ SymbolicPlanner│──→ Goal decomposition → Proof tree generation
└──────────────┘
      │
      ▼
┌──────────────┐
│ ProofCollector│──→ Proof verification + Archival → Audit trail
└──────────────┘
      │
      ▼
┌──────────────┐
│ DataGuardian │──→ Outbound data interception → Consent verification
└──────────────┘
      │
      ▼
┌──────────────┐
│InferenceFilter│──→ LLM call sanitization → No vault data leakage
└──────────────┘
      │
      ▼
┌──────────────┐
│   AGENTS     │──→ Bound to ONE vault, ONE identity → Execution
└──────────────┘
      │
      ▼
┌──────────────┐
│  Exfiltrate  │──→ Behavioral monitoring → "Phoning home?" detection
│  Detector    │
└──────────────┘
      │
      ▼
┌──────────────┐
│  UserAlert   │──→ Real-time human notification → Always in the loop
│   System     │
└──────────────┘
      │
      ▼
   HUMAN
   (back at the base, reviewing, revoking, governing)
```

## Module Architecture

### `oblisk/vault/` — The Base

| Module | Purpose | Key Class |
|--------|---------|-----------|
| `vault.py` | AES-256-GCM encrypted store | `Vault` |
| `identity.py` | Sovereign key ceremony | `HumanIdentity` |
| `policy_store.py` | Human-authored governance rules | `PolicyStore` |
| `intent_store.py` | Cryptographically signed intents | `IntentStore` |
| `consent_log.py` | Immutable chained audit trail | `ConsentLog` |

**Invariant**: The human IS the key. No cloud backup. No recovery service.

### `oblisk/conduit/` — The Shaft

| Module | Purpose | Key Class |
|--------|---------|-----------|
| `intent_parser.py` | Natural language → Governed intent | `IntentParser` |
| `constraint_engine.py` | Datalog constraint verification | `ConstraintEngine` |
| `flow_controller.py` | One-directional authorization | `FlowController` |
| `proof_collector.py` | Proof tree archival + audit | `ProofCollector` |

**Invariant**: Flow is one-directional. Human initiates, agents execute.

### `oblisk/shield/` — The Barrier

| Module | Purpose | Key Class |
|--------|---------|-----------|
| `data_guardian.py` | Outbound data interception | `DataGuardian` |
| `inference_filter.py` | LLM prompt sanitization | `InferenceFilter` |
| `exfiltration_detect.py` | Behavioral anomaly detection | `ExfiltrationDetector` |
| `user_alert.py` | Real-time human notification | `UserAlertSystem` |

**Invariant**: Default deny. Every data movement is suspicious until proven consented.

### `oblisk/ceremony/` — The Ritual

| Module | Purpose | Key Class |
|--------|---------|-----------|
| `key_generation.py` | Sovereign key ceremony | `KeyCeremony` |
| `policy_creation.py` | NL → Datalog wizard | `PolicyWizard` |
| `trust_ritual.py` | Agent binding ceremony | `TrustRitual` |
| `proof_viewer.py` | Human audit interface | `ProofViewer` |

**Invariant**: Every binding is intentional. Every ceremony is verified cryptographically.

## Governance Principles

### 1. Cryptographic Intent
No agent acts without a cryptographically signed intent from the vault identity. The signature is non-repudiable — it proves a specific human authorized a specific action at a specific time.

### 2. Hard Constraints
Policies are written in Prolog/Datalog and stored in the vault. Every proof tree from the SymbolicPlanner must satisfy all active constraints. A plan that violates any hard constraint is rejected before execution.

### 3. Immutable Audit
Every authorization, every data transfer request, every policy change is logged in a cryptographically chained consent log. The human can audit any decision, at any time, for any reason.

### 4. Default Deny
The Shield operates on default deny:
- No data leaves without consent-log approval
- No LLM sees vault data
- No agent communicates without authorization
- Anomalous behavior triggers immediate alerts

### 5. Human Sovereignty
The human is the root of trust. They:
- Generate and control the master keys
- Write the governance policies
- Sign all intents
- Can revoke any authorization instantly
- Can audit any decision through the proof viewer

## Proof Tree Format

A proof tree is a structured explanation of why an agent took a specific action:

```json
{
  "steps": [
    {
      "description": "Search documents for 'Project Alpha'",
      "reason": "Intent requires finding documents about Project Alpha",
      "data_accessed": ["document_index", "search_index"],
      "constraints_satisfied": ["no_location_sharing", "data_locality"]
    },
    {
      "description": "Summarize found documents",
      "reason": "Intent requires summarizing the found documents",
      "data_accessed": ["document_contents"],
      "constraints_satisfied": ["inference_filter_passed"]
    }
  ],
  "data_access": ["document_index", "search_index", "document_contents"],
  "external_calls": [
    {"endpoint": "local_inference_engine", "method": "generate", "transmits_data": false}
  ],
  "data_flow": [
    {"source": "document_store", "destination": "local", "data_type": "document_contents"}
  ]
}
```

## Ceremonies

### Key Ceremony
A multi-phase ritual that:
1. Presents warnings (no recovery, human IS the key)
2. Gathers entropy from multiple sources
3. Generates a high-entropy passphrase (not user-chosen)
4. Requires explicit confirmation of understanding
5. Derives sovereign identity with cryptographic attestation

### Trust Ritual
A binding ceremony that:
1. Presents agent capabilities for human review
2. Reviews data access permissions
3. Requires explicit human confirmation
4. Performs cryptographic binding (agent key derived from master)
5. Records binding in consent log

### Policy Creation
A wizard that:
1. Presents templates for common governance scenarios
2. Asks clarifying questions in natural language
3. Translates answers into Prolog/Datalog rules
4. Validates generated rules
5. Stores policies encrypted in vault

## Migration from v1

The v1 architecture (`core/`, `agents/`) remains functional. The v2 modules (`vault/` expanded, `conduit/`, `shield/`, `ceremony/`) are additive. Migration path:

1. Run the KeyCeremony to establish sovereign identity
2. Import existing vault data into new AES-256-GCM store
3. Create policies via PolicyWizard to replace hardcoded rules
4. Bind existing agents through TrustRitual
5. Activate Shield components for outbound monitoring

## Threat Model

### What OBLISK Defends Against
- **Unauthorized data exfiltration**: Shield blocks all outbound data without consent
- **Prompt injection attacks**: InferenceFilter prevents vault data in LLM contexts
- **Agent compromise**: ExfiltrationDetector spots anomalous agent behavior
- **Policy bypass**: FlowController verifies every plan against hard constraints
- **Repudiation**: ConsentLog provides cryptographic proof of human approvals

### What OBLISK Does NOT Defend Against
- **Physical device compromise**: If the device is compromised at the OS level,
  OBLISK's protections can be bypassed. The vault encryption provides defense
  in depth but is not absolute.
- **Social engineering**: If the human is tricked into signing malicious intents
  or revealing their recovery phrase, OBLISK cannot prevent this.
- **Supply chain attacks**: Compromised dependencies or build tools could
  undermine OBLISK's security guarantees.

## License

See LICENSE file in repository root.
