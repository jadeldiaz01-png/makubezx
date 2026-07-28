# Registry benchmark evidence plan

## Status

`PROPOSED` — no benchmark has been executed.

## Dataset sizes

- 1,000 versioned agent definitions.
- 5,000 versioned agent definitions.
- 15,000 versioned agent definitions.

## Reproducibility requirements

Every benchmark report must record:

- commit SHA;
- database engine and version;
- migration revision;
- Python and dependency versions;
- runner hardware or hosted-runner class;
- deterministic dataset seed;
- warm-up and measured iterations;
- exact commands;
- index definitions and relevant query plans.

## Required measurements

- Bulk registration duration.
- Single-registration latency distribution.
- Exact capability-search latency distribution.
- Owner, risk, version and expiration filter latency.
- Pagination latency.
- Conflict and duplicate rejection latency.
- Database size.
- Query-plan index usage.

## Integrity checks

- Zero cross-tenant results.
- Zero accepted hash mismatches.
- Zero silent duplicate versions.
- Stable pagination for an unchanged dataset.
- Atomic manifest-plus-audit behavior under induced failure.

## Reporting rule

Do not publish invented, extrapolated or marketing-derived performance figures. Results are evidence only when produced by committed benchmark code against a documented environment.
