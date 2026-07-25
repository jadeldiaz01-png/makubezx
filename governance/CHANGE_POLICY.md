# Change Management Policy

## Purpose

Every repository change must be attributable, reviewable, reversible and supported by evidence proportional to risk.

## Required lifecycle

1. Define the problem and measurable acceptance criteria.
2. Classify risk from R0 to R4.
3. Implement on an isolated branch.
4. Run applicable CI, tests, security and supply-chain checks.
5. Record evidence and residual risk.
6. Obtain human approval required by the risk level.
7. Merge manually with an expected head SHA.
8. Observe post-merge health and retain rollback capability.

## Approval matrix

- R0: one reviewer; documentation-only changes.
- R1: one human reviewer and green CI.
- R2: owner review, green CI, rollback and evidence record.
- R3: two-role review, explicit GO/NO-GO and operational monitoring.
- R4: change advisory decision, independent safety/security review, staged rollout and tested recovery.

The repository is currently maintained by one account. Where independent reviewers are unavailable, R3 and R4 remain NO-GO for production and may only proceed as experimental designs.

## Protected main target state

The intended `main` ruleset is:

- pull requests required;
- at least one approving review;
- dismissal of stale approvals;
- CODEOWNERS review for sensitive paths;
- all conversations resolved;
- required checks by current job name: `quality`, `sbom`, and `validate` when their path filters apply;
- governance changes must pass the `governance-evidence` workflow;
- supply-chain changes must pass the `supply-chain-evidence` workflow;
- branch must be current before merge;
- force pushes and deletion prohibited;
- direct pushes prohibited except documented emergency recovery;
- signed commits or verified merge provenance preferred;
- manual merge only; auto-merge disabled.

Workflow and job names are operational identifiers. Any rename must update the repository ruleset in the same approved change or the merge gate is considered unverified.

This document defines the target control. Repository settings must be configured separately through GitHub rulesets or branch protection and verified after activation.

## Emergency changes

Emergency changes require an incident identifier, minimum safe scope, explicit rollback, retrospective review and evidence entry. Emergency status never authorizes secrets in Git, real-money trading or unapproved external publication.