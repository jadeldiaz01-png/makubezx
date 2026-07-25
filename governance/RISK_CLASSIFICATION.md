# Risk Classification

## R0 — Informational

Documentation, comments or metadata with no operational effect.

Required: basic review and content validation.

## R1 — Low

Reversible tooling or developer-experience changes without production access.

Required: green CI, one reviewer and explicit rollback.

## R2 — Moderate

Internal runtime, data model, dependency, workflow or permission changes with bounded impact.

Required: owner review, tests, security checks, evidence record and rollback validation.

## R3 — High

External integrations, authentication, secrets handling, agent privileges, production infrastructure, public publishing or testnet execution.

Required: two-role review, staged rollout, SLO/alert coverage, explicit GO/NO-GO and recovery exercise.

## R4 — Critical

Real-money trading, autonomous public actions, destructive migrations, irreversible operations, regulated data or broad privilege escalation.

Required: independent security and safety approval, change advisory decision, canary or pilot, tested disaster recovery, continuous monitoring and manual kill switch.

## Mandatory escalation triggers

A change moves to at least R3 when it:

- accesses production credentials;
- modifies authorization or policy enforcement;
- creates externally visible content;
- executes against financial or market accounts;
- changes backup, recovery or encryption controls;
- introduces a new model, agent tool or autonomous decision path.

A change moves to R4 when financial loss, public harm, irreversible data loss or regulatory exposure is plausible.

## Current repository constraint

Until independent review, production infrastructure and operational runbooks exist, all R3 and R4 capabilities remain `PROPOSED` or `EXPERIMENTAL` and are NO-GO for production.
