# OBLISK Metropolis Architecture

> **From Gotham to Metropolis: The OBLISK v2 Upgrade**
>
> OBLISK v1 was your Batman — encrypted, solitary, effective in the shadows.
> OBLISK v2 is your Superman — faster than a speeding bullet, leaping tall data centers, powered by the yellow sun of cloud-native infrastructure.

---

## Gotham vs. Metropolis: The Upgrade

| Dimension | Gotham (Current) | Metropolis (Target) |
|---|---|---|
| **Agents** | Python classes in memory | Containerized micro-agents with gRPC APIs, multi-language SDK |
| **Vault** | Local AES-256-GCM file | HashiCorp Vault + cloud KMS, dynamic secrets, Shamir sharing |
| **Planning** | Greedy forward search | Temporal.io workflows + Monte Carlo Tree Search |
| **Governance** | In-memory policy lists | OPA (Open Policy Agent) sidecars with Rego |
| **Messaging** | Python pub/sub | NATS / Kafka event mesh |
| **Observability** | File logging | OpenTelemetry -> Jaeger + Prometheus + Grafana |
| **Identity** | Hardcoded 32-byte keys | SPIFFE/SPIRE workload identities, mTLS everywhere |
| **Scale** | Single machine | Kubernetes-native, KEDA auto-scaling, Istio service mesh |

---

## The New Skyline

### The Fortress of Solitude (Vault 2.0)

- Distributed HashiCorp Vault with auto-unseal
- Dynamic secrets: each agent gets short-lived AWS IAM/DB tokens
- Secrets never touch disk; in-flight mTLS only
- HSM-backed root keys (YubiHSM / CloudHSM)

### The Justice League Registry (Agent Mesh)

- Rust/Go/Python SDKs via gRPC
- Circuit breakers & leader election (Raft)
- WebAssembly sandboxes for untrusted plugins
- GPU-accelerated symbolic planning

### The Phantom Zone (Immutable Audit)

- Amazon QLDB / immudb for cryptographically verifiable logs
- Zero-knowledge proofs for compliance without exposure
- WORM storage for SOC2/FedRAMP

### X-Ray Vision (Observability)

- Every agent emits OpenTelemetry traces
- Real-time dashboards showing agent health, vault latency, task throughput
- PagerDuty alerts when nodes go dark

---

## The Lex Luthor Defense

| Threat | Metropolis Counter |
|--------|-----------------|
| Memory dump | Intel SGX / AMD SEV enclaves |
| Supply chain | SLSA Level 3, signed SBOMs |
| Insider threat | RBAC + ABAC + M-of-N dual control |
| Quantum future | CRYSTALS-Kyber hybrid post-quantum TLS |

---

## Build Phases

### Phase 1: Foundation
- Containerize all services
- gRPC service definitions
- NATS message backbone
- Local Kubernetes (kind/k3d)

### Phase 2: Towers
- HashiCorp Vault deployment
- Temporal.io workflow engine
- Helm charts for all services

### Phase 3: Sky
- Rust SDK
- Istio mTLS mesh
- KEDA autoscaling

### Phase 4: Stars
- GPU-accelerated planner
- WebAssembly sandbox runtime
- FedRAMP compliance package

---

## Architecture Diagram (High-Level)

```
                     ┌─────────────────────────────────┐
                     │         K8s Ingress (Istio)      │
                     └──────────────┬──────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
             ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
             │   Agent      │ │  Agent     │ │   Agent    │
             │   SDK (gRPC) │ │  SDK (gRPC)│ │  SDK (gRPC)│
             └──────┬──────┘ └─────┬──────┘ └─────┬──────┘
                    │               │               │
                    └───────┬───────┴───────┬───────┘
                            │               │
                     ┌──────▼───────────────▼──────┐
                     │    NATS / Kafka Event Mesh    │
                     └──────┬───────────────┬────────┘
                            │               │
               ┌────────────▼──┐     ┌─────▼────────────┐
               │  Temporal.io   │     │  HashiCorp Vault  │
               │  (Workflows)   │     │  (Secrets/KMS)    │
               └────────────┬──┘     └─────┬────────────┘
                            │               │
               ┌────────────▼──┐     ┌─────▼────────────┐
               │  OPA Sidecars  │     │  QLDB / immudb    │
               │  (Policy)      │     │  (Audit Log)      │
               └───────────────┘     └──────────────────┘
                            │
               ┌────────────▼──────────────┐
               │  OpenTelemetry ->          │
               │  Jaeger + Prometheus       │
               │  + Grafana + PagerDuty     │
               └────────────────────────────┘
```

---

## Component Details

### Agent SDK (Multi-Language)
```protobuf
service OBLISKAgent {
  rpc ExecuteTask(TaskRequest) returns (TaskResponse);
  rpc StreamEvents(EventStream) returns (stream Event);
  rpc GetCapabilities(Empty) returns (Capabilities);
  rpc CheckHealth(Empty) returns (HealthStatus);
}
```

### Vault Integration
- Vault Agent sidecar pattern
- Kubernetes auth method
- Dynamic database credentials
- Transit encryption as a service
- PKI for service-to-service mTLS

### Temporal.io Workflows
- Long-running task orchestration
- Retry policies and sagas
- Human-in-the-loop approval workflows
- Cron-based scheduled tasks

### OPA Governance
- Rego policies for agent authorization
- Data filtering policies
- Rate limiting decisions
- Admission control for K8s resources

---

## Security Architecture

### Identity & Trust
- SPIFFE IDs for all workloads
- SPIRE agent on each node
- Automatic SVID rotation
- mTLS between all services

### Secret Lifecycle
1. Agent requests identity attestation
2. SPIRE issues SVID
3. Agent presents SVID to Vault
4. Vault issues dynamic secret (15-min TTL)
5. Agent uses secret, never persists to disk
6. Secret auto-revoked on TTL expiry

### Compliance
- SOC 2 Type II controls
- FedRAMP Moderate (Phase 4)
- Zero-trust architecture alignment
- Supply chain integrity (SLSA L3)

---

## Infrastructure as Code

```yaml
# Example: Vault Helm values
vault:
  ha:
    enabled: true
    replicas: 3
    raft:
      enabled: true
  injector:
    enabled: true
  serverTelemetry:
    prometheusRules: true
  securityContext:
    capabilities:
      add: ["IPC_LOCK"]

# Example: Temporal Helm values
temporal:
  server:
    replicaCount: 3
  elasticsearch:
    enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true

# Example: Istio service mesh
istio:
  profile: default
  meshConfig:
    enableAutoMtls: true
    defaultConfig:
      tracing:
        sampling: 100.0
  telemetry:
    enabled: true
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Agent task latency (p99) | < 50ms |
| Vault secret retrieval | < 10ms |
| Workflow start latency | < 100ms |
| Event mesh throughput | > 100K msg/s |
| Trace ingestion | > 10K spans/s |
| KEDA scale-out time | < 15s |
| Recovery time (RTO) | < 5 minutes |
| Recovery point (RPO) | < 1 second |

---

## Migration Path from Gotham

1. **Dual-run mode**: Gotham and Metropolis operate in parallel
2. **Shadow traffic**: Mirror production traffic to Metropolis
3. **Gradual cutover**: Migrate agent by agent
4. **Vault migration**: Export/import encrypted secrets with HSM ceremony
5. **Decommission**: Sunset Gotham after 30-day validation period

---

*"OBLISK Metropolis isn't just an upgrade — it's a different species. Where Gotham hid in shadows, Metropolis stands in the sun."*
