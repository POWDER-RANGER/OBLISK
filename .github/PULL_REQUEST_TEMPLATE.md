## Summary

<!-- Concise description of what this PR does -->

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that changes existing API)
- [ ] Refactor / cleanup (no functional change)
- [ ] CI / tooling change
- [ ] Documentation only

## Testing

- [ ] `pytest --cov --cov-fail-under=100` passes locally
- [ ] All new code has tests achieving 100% line + branch coverage
- [ ] `ruff format --check .` passes
- [ ] `ruff check .` passes
- [ ] `mypy agents/ core/ vault/ --strict` passes

## Documentation Accuracy

- [ ] `docs/ARCHITECTURE.md` status matrix updated if any feature status changed
- [ ] README claims match the implemented (not planned) code
- [ ] New features not yet fully tested are marked 🔲 Planned in the status matrix
- [ ] SECURITY.md is accurate if crypto/vault changes were made

## Security Checklist (if applicable)

- [ ] No hardcoded keys, secrets, or passwords
- [ ] No `eval()` / `exec()` on untrusted input
- [ ] `subprocess` calls use `shell=False`
- [ ] No `pickle` for untrusted data
- [ ] Vault changes maintain AES-256-GCM guarantee

## Related Issues

Closes #
