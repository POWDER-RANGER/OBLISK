# OBLISK Architecture

## System Overview

OBLISK (Organized Blockchain-Linked Intelligence System with Kernelized security) is a multi-agent AI system designed for secure, decentralized intelligence operations with encrypted vaults and symbolic planning capabilities.

## Core Components

### 1. Agent Framework

#### Agent Manager (`agents/`)
- **Purpose**: Coordinates multiple AI agents with distinct roles and capabilities
- **Key Features**:
  - Dynamic agent spawning and lifecycle management
  - Inter-agent communication protocols
  - Resource allocation and task distribution
  - Agent health monitoring and recovery

#### Agent Types
- **Reasoning Agent**: Symbolic logic and inference
- **Planning Agent**: Multi-step task decomposition
- **Security Agent**: Threat detection and vault management
- **Learning Agent**: Adaptive behavior and pattern recognition

### 2. Vault System

#### Encrypted Storage (`core/vault/`)
- **Encryption**: AES-256-GCM for data at rest
- **Key Management**: Hierarchical key derivation (HKDF)
- **Access Control**: Role-based permissions with audit logging
- **Vault Types**:
  - Memory vaults (agent state)
  - Knowledge vaults (structured data)
  - Credential vaults (API keys, tokens)
  - Artifact vaults (models, outputs)

### 3. Governance Engine

#### Decision Framework (`core/governance/`)
- **Consensus Mechanisms**:
  - Multi-agent voting on critical decisions
  - Weighted authority based on agent specialization
  - Byzantine fault tolerance for adversarial scenarios

- **Policy Enforcement**:
  - Declarative rules engine
  - Dynamic policy updates
  - Compliance verification

### 4. Symbolic Planning

#### Planner Architecture (`core/planner/`)
- **PDDL Integration**: Planning Domain Definition Language support
- **Heuristic Search**: A* and hierarchical task networks
- **Temporal Planning**: Time-aware scheduling
- **Reactive Re-planning**: Dynamic plan adaptation

#### Planning Components
```
planner/
├── domain/          # Problem domain definitions
├── heuristics/      # Search heuristics
├── executor/        # Plan execution engine
└── monitor/         # Plan monitoring and replanning
```

## Data Flow

### Request Processing Pipeline

1. **Ingress**: External request arrives
2. **Authentication**: Vault system verifies credentials
3. **Routing**: Agent manager assigns to appropriate agent
4. **Planning**: Symbolic planner generates action sequence
5. **Governance**: Multi-agent consensus on execution
6. **Execution**: Agents execute plan steps
7. **Persistence**: Results stored in encrypted vaults
8. **Response**: Structured output returned

### Inter-Agent Communication

- **Message Bus**: Asynchronous pub/sub via internal queue
- **Protocols**: JSON-based message format with schemas
- **Security**: All messages signed with agent keys
- **Monitoring**: Full message audit trail

## Security Model

### Defense in Depth

1. **Network Layer**: TLS 1.3 for all external communication
2. **Application Layer**: Input validation and sanitization
3. **Data Layer**: Encryption at rest and in transit
4. **Access Control**: Zero-trust architecture

### Threat Model

- **External Attacks**: API hardening, rate limiting
- **Internal Threats**: Agent sandboxing, permission isolation
- **Data Leakage**: Vault segmentation, need-to-know access
- **Availability**: Redundancy, graceful degradation

## Scalability Considerations

### Horizontal Scaling
- Agent pool can scale across multiple processes/machines
- Vault system supports distributed storage backends
- Load balancing via agent manager

### Performance Optimization
- Lazy loading of vault data
- Caching layer for frequent queries
- Asynchronous execution where possible
- Resource pooling for expensive operations

## Technology Stack

- **Language**: Python 3.11+
- **Agent Framework**: Custom (built on asyncio)
- **Cryptography**: `cryptography` library (FIPS 140-2 compliant)
- **Planning**: `unified-planning` library
- **Storage**: SQLite (dev), PostgreSQL (prod)
- **Message Queue**: Internal (dev), Redis (prod)

## Future Enhancements

### Q1 2025
- [ ] Blockchain integration for audit trail
- [ ] ML-based agent coordination
- [ ] Advanced threat detection

### Q2 2025
- [ ] Distributed vault consensus
- [ ] GPU acceleration for planning
- [ ] External policy integration

## References

- [PDDL Specification](https://planning.wiki/)
- [Multi-Agent Systems](https://mitpress.mit.edu/books/multiagent-systems)
- [Cryptographic Best Practices](https://www.nist.gov/cryptography)

---

**Last Updated**: December 2025  
**Version**: 0.2.0-alpha
