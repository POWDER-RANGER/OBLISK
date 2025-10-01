# Core Module

This directory contains the core system components of OBLISK.

## Components

- **Agent Engine**: Core agent orchestration and lifecycle management
- **Communication**: Inter-agent communication protocols
- **Configuration**: System configuration management
- **Database**: Database interfaces and models
- **Governance**: Policy enforcement and audit mechanisms
- **Security**: Core security primitives and encryption

## Structure

```
core/
├── __init__.py
├── agent.py          # Agent base class and orchestration
├── communication.py  # Communication layer
├── config.py         # Configuration management
├── db.py            # Database interfaces
├── governance.py    # Governance engine
└── security.py      # Security primitives
```

## Getting Started

The core module provides the fundamental building blocks for the OBLISK system. All other modules depend on these core components.
