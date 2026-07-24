# Security Policy

## Supported state

This repository is currently `EXPERIMENTAL`. No component is approved for autonomous trading, real-money execution, production social publishing, or unrestricted agent actions.

## Reporting a vulnerability

Do not open a public issue containing secrets, credentials, personal data, exploit payloads, or operational details that would increase risk. Use GitHub private vulnerability reporting when enabled. If that channel is unavailable, contact the repository owner privately and provide:

- affected commit and file;
- reproducible impact without destructive execution;
- severity and prerequisites;
- proposed mitigation;
- evidence that no production system was accessed.

## Response objectives

- Critical: initial triage within 1 business day.
- High: initial triage within 3 business days.
- Medium/Low: initial triage within 7 business days.

These are operational objectives, not contractual SLAs.

## Security invariants

- No secrets in Git history.
- Deny by default for tools and agent capabilities.
- Human approval for irreversible or externally visible actions.
- Immutable GitHub Action references.
- Reproducible dependency declarations.
- Evidence and rollback for every security-sensitive change.

## Disclosure

Coordinate disclosure after a fix or compensating control is available. Never test against third-party systems without explicit authorization.
