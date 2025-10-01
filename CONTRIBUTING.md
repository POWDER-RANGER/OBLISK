# Contributing to OBLISK

First off, thank you for considering contributing to OBLISK! It's people like you that make OBLISK such a great tool for the multi-agent AI community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Style Guidelines](#style-guidelines)
  - [Git Commit Messages](#git-commit-messages)
  - [Python Style Guide](#python-style-guide)
  - [Documentation Style Guide](#documentation-style-guide)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** to demonstrate the steps
- **Describe the behavior you observed** and what you expected
- **Include screenshots or error messages** if applicable
- **Specify your environment:**
  - Python version
  - Operating system
  - OBLISK version
  - Relevant dependency versions

**Bug Report Template:**

```markdown
## Bug Description
[Clear description of the bug]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. ...

## Expected Behavior
[What you expected to happen]

## Actual Behavior
[What actually happened]

## Environment
- Python version:
- OS:
- OBLISK version:

## Additional Context
[Any other relevant information]
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the proposed enhancement
- **Explain why this enhancement would be useful** to most OBLISK users
- **List any similar features** in other projects if applicable
- **Include mockups or examples** if relevant

### Pull Requests

We actively welcome your pull requests!

1. **Fork the repository** and create your branch from `main`
2. **Follow the development setup** instructions below
3. **Make your changes:**
   - Write clean, readable code
   - Add tests for new functionality
   - Update documentation as needed
4. **Ensure the test suite passes:**
   ```bash
   pytest tests/
   ```
5. **Ensure code style compliance:**
   ```bash
   black oblisk/
   flake8 oblisk/
   mypy oblisk/
   ```
6. **Write a clear commit message** (see guidelines below)
7. **Open a pull request** with a clear title and description

**PR Checklist:**

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] No new warnings or errors introduced
- [ ] Branch is up to date with main

## Development Setup

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 14+
- Redis 6+
- Git

### Setup Steps

1. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/OBLISK.git
   cd OBLISK
   ```

2. **Add upstream remote:**
   ```bash
   git remote add upstream https://github.com/POWDER-RANGER/OBLISK.git
   ```

3. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

5. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```

6. **Configure the project:**
   ```bash
   cp config.example.yaml config.yaml
   # Edit config.yaml with your local settings
   ```

7. **Initialize the database:**
   ```bash
   python -m oblisk.core.db init
   ```

8. **Run tests to verify setup:**
   ```bash
   pytest tests/
   ```

## Style Guidelines

### Git Commit Messages

Follow these conventions for clear and consistent commit history:

- **Use the present tense** ("Add feature" not "Added feature")
- **Use the imperative mood** ("Move cursor to..." not "Moves cursor to...")
- **Limit the first line to 72 characters or less**
- **Reference issues and pull requests** after the first line
- **Use conventional commit format when applicable:**
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation changes
  - `style:` for formatting changes
  - `refactor:` for code refactoring
  - `test:` for test additions or modifications
  - `chore:` for maintenance tasks

**Example:**
```
feat: add multi-agent coordination protocol

Implements the basic framework for agents to communicate
and coordinate tasks through the messaging layer.

Resolves #123
```

### Python Style Guide

- **Follow PEP 8** with modifications per `.flake8` config
- **Use Black** for code formatting (line length: 88)
- **Use type hints** for all functions and methods
- **Write docstrings** in Google style format
- **Keep functions focused** - one function, one responsibility
- **Use meaningful variable names** - clarity over brevity

**Example:**

```python
from typing import Optional, Dict, Any

def create_agent(
    name: str,
    capabilities: list[str],
    config: Optional[Dict[str, Any]] = None
) -> Agent:
    """Create a new agent with the specified capabilities.
    
    Args:
        name: Unique identifier for the agent
        capabilities: List of capability strings
        config: Optional configuration dictionary
        
    Returns:
        Configured Agent instance
        
    Raises:
        ValueError: If name is empty or capabilities list is invalid
    """
    if not name:
        raise ValueError("Agent name cannot be empty")
    
    return Agent(name=name, capabilities=capabilities, config=config or {})
```

### Documentation Style Guide

- **Use Markdown** for all documentation
- **Keep lines under 100 characters** for readability
- **Include code examples** for API documentation
- **Provide context** - explain the "why" not just the "what"
- **Use proper grammar and spelling**
- **Update relevant docs** when making code changes

## Testing Guidelines

### Writing Tests

- Write tests for all new features and bug fixes
- Aim for high test coverage (>80%)
- Use descriptive test names that explain what is being tested
- Follow the Arrange-Act-Assert pattern
- Use fixtures for common test setup
- Mock external dependencies

**Example:**

```python
import pytest
from oblisk.agents import Agent

@pytest.fixture
def sample_agent():
    """Fixture providing a basic test agent."""
    return Agent(
        name="test_agent",
        capabilities=["test"],
    )

def test_agent_starts_successfully(sample_agent):
    """Test that an agent can be started without errors."""
    # Arrange
    assert sample_agent.state == "initialized"
    
    # Act
    sample_agent.start()
    
    # Assert
    assert sample_agent.state == "running"
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_agents.py

# Run with coverage
pytest --cov=oblisk tests/

# Run with verbose output
pytest -v tests/
```

## Review Process

1. **Automated checks** must pass (tests, linting, type checking)
2. **Code review** by at least one maintainer
3. **Documentation review** if docs are changed
4. **Final approval** and merge by project maintainer

## Community

- **GitHub Discussions:** For questions and general discussion
- **GitHub Issues:** For bug reports and feature requests
- **Pull Requests:** For code contributions

## Recognition

Contributors will be recognized in:
- The project README
- Release notes for their contributions
- The CONTRIBUTORS.md file (if significant contributions)

## Questions?

Don't hesitate to ask! You can:
- Open an issue with the "question" label
- Start a discussion in GitHub Discussions
- Reach out to the maintainers

Thank you for contributing to OBLISK! 🚀
