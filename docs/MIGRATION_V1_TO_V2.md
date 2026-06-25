# Migration Guide: OBLISK v1 → v2

## Overview

OBLISK v2 is a major architectural evolution. The core principle shifts from
"AI governance" to **human sovereignty**. This guide helps you migrate existing
v1 deployments to v2.

## Key Changes

### Architecture
- **v1**: `core/` + `agents/` + basic `vault/`
- **v2**: Expanded `vault/` + new `conduit/` + new `shield/` + new `ceremony/`

### Philosophy
- **v1**: Governance engine checks rules
- **v2**: Human IS the key. Human writes the law. Human signs every intent.

### Data Flow
- **v1**: Intent → Planner → Agent → External API
- **v2**: Human → Vault → Intent (signed) → FlowController → Planner → Shield → Agent → Back to Human

## Step-by-Step Migration

### Step 1: Preserve v1 Code
Your v1 code in `core/`, `agents/`, and `vault/` (legacy) remains untouched.
The v2 modules are additive and parallel.

```python
# v1 still works
from core.governance_engine import GovernanceEngine
from core.symbolic_planner import SymbolicPlanner
from agents.agent_manager import AgentManager

# v2 is available alongside
from oblisk.vault import Vault, HumanIdentity, PolicyStore
from oblisk.conduit import FlowController, IntentParser
from oblisk.shield import DataGuardian, InferenceFilter
```

### Step 2: Run the Key Ceremony
Establish your sovereign identity:

```python
from oblisk.ceremony import KeyCeremony

ceremony = KeyCeremony()
state = ceremony.begin()

# Acknowledge each warning
for i in range(len(ceremony.WARNINGS)):
    state = ceremony.acknowledge_warning(i)

# Gather entropy
state = ceremony.gather_entropy({
    "system": os.urandom(32),
    "timing": get_keystroke_timing_entropy(),
})

# Generate passphrase
passphrase, state = ceremony.generate_passphrase()
print(f"YOUR RECOVERY PHRASE (WRITE THIS DOWN): {passphrase}")

# Confirm understanding
state = ceremony.confirm_understanding("I understand there is no recovery and I am the key")

# Derive keys
identity, master_key, state = ceremony.derive_keys(passphrase)

# Create vault
vault = Vault.create("~/.oblisk/vault.enc", passphrase)
```

### Step 3: Set Up Policies
Convert your v1 governance rules to v2 policies:

```python
from oblisk.vault import PolicyStore

policy_store = PolicyStore(vault)

# From template
policy = policy_store.set_hard_constraint(
    "location_data(X) :- never_leaves_device(X).",
    policy_id="no_location_sharing"
)

# Or use the wizard
from oblisk.ceremony import PolicyWizard

wizard = PolicyWizard(policy_store)
policy = wizard.create_custom(
    "Never share my location data with anyone",
    policy_id="location_privacy"
)
```

### Step 4: Initialize the Shield
Protect against data exfiltration:

```python
from oblisk.shield import DataGuardian, InferenceFilter, UserAlertSystem

data_guardian = DataGuardian(consent_log, vault)
inference_filter = InferenceFilter(vault)
alerts = UserAlertSystem()

# Register alert handlers
alerts.register_handler(my_desktop_notification_handler)
alerts.register_handler(my_logging_handler)
```

### Step 5: Activate the Flow Controller
Replace direct agent calls with governed flow:

```python
from oblisk.conduit import FlowController

flow = FlowController(
    vault=vault,
    identity=identity,
    intent_store=intent_store,
    consent_log=consent_log,
    policy_store=policy_store,
)

# Create and sign an intent
intent = intent_store.create_intent("Find and summarize my Project Alpha documents")
signed_intent = intent_store.sign_intent(intent.id)

# Generate proof tree (from SymbolicPlanner)
proof_tree = planner.create_plan(intent.id, intent.goal, intent.constraints)

# Authorize through FlowController
decision = flow.authorize_action(intent.id, proof_tree)

if decision.authorized:
    # Proceed with agent execution
    agent.execute(plan)
else:
    alerts.send_alert(
        priority=AlertPriority.WARNING,
        category=AlertCategory.POLICY_VIOLATION,
        title="Action Blocked",
        message=decision.reason,
    )
```

## Backward Compatibility

v1 code continues to work unchanged. The v2 modules are opt-in:
- `core/` → Still functional
- `agents/` → Still functional  
- Legacy `vault/` → Still functional

You can adopt v2 modules incrementally:
1. Start with `vault/` expanded (identity, policy store)
2. Add `conduit/` (flow controller for authorization)
3. Add `shield/` (data guardian for outbound monitoring)
4. Add `ceremony/` (key ceremony, trust ritual)

## Rollback

If you need to rollback from v2 to v1:
1. Stop using v2 modules (FlowController, Shield, Ceremony)
2. Continue using v1 `core/`, `agents/`, legacy `vault/`
3. v2 data in the vault is ignored by v1 code

No data is destroyed during migration. The v2 vault store is additive.

## Timeline

| Phase | Duration | Actions |
|-------|----------|---------|
| Planning | 1 week | Review v2 architecture, plan migration |
| Key Ceremony | 1 day | Run sovereign key generation |
| Policy Migration | 1-2 weeks | Convert rules to Datalog policies |
| Shield Activation | 1 week | Deploy data guardian, inference filter |
| Flow Controller | 2 weeks | Route all actions through FlowController |
| Full Cutover | 1 week | Decommission v1 governance path |

## Support

For migration assistance:
- Review `docs/ARCHITECTURE_V2.md` for full architecture details
- Check `docs/ARCHITECTURE.md` for v1 architecture reference
- File issues at https://github.com/POWDER-RANGER/OBLISK/issues
