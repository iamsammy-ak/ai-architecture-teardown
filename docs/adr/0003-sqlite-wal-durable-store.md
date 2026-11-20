# ADR-0003: SQLite in WAL mode as the durable store

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Durable agent state machine](../systems/durable-agent-state-machine.md), [Three-tier agent memory](../systems/three-tier-agent-memory.md)

## Context and problem statement

The durable runtime needs a journal, a runs index, checkpoints, a signal inbox and an outbox, and the outbox is only correct if a step's result and its outgoing messages commit atomically. The memory system needs transactional, namespaced storage for facts, episodes and vectors. Both are single-host prototypes that must be easy to inspect.

## Decision drivers

- One local transaction must cover every table a step touches (no two-phase commit).
- Zero operations: no server to run in CI or on a laptop.
- Inspectable with standard tools; survives process crashes.

## Considered options

1. Postgres
2. A queue plus a database
3. SQLite in WAL mode, one file

## Decision outcome

Chosen option 3, **SQLite in WAL mode, one file**, because the outbox's atomicity comes for free from a single local transaction, and the measured cost of durability is small.

### Consequences

- Good, because A durable step costs 1.97 ms median (`synchronous=NORMAL`, checkpoint every transition); `FULL` durability costs 3.32 ms.
- Good, because SQL triggers make the event journal append-only at the database level.
- Good, because memory recall over SQLite with brute-force cosine takes 1.65 ms median for about 20 items per user.
- Bad, because workers must share one host's disk; write throughput is bounded by one SQLite writer.
- Bad, because `synchronous=NORMAL` can lose the last commits on power loss (never corrupt the file).

### Confirmation

The chaos benchmark kills worker processes 200 times mid-transaction and checks every journal against its invariants: 0 violations.

## Pros and cons of the options

### 1. Postgres

- Good, because multi-host workers; `SELECT ... FOR UPDATE SKIP LOCKED`
- Bad, because A server to operate in every environment

### 2. A queue plus a database

- Good, because scales out
- Bad, because atomic outbox needs distributed transactions or a second outbox

### 3. SQLite in WAL mode, one file

- Good, because one transaction covers everything
- Good, because no server; inspectable
- Good, because WAL allows readers during writes
- Bad, because one host, one writer
- Bad, because network file systems do not give reliable locks

## More information

- Append-only triggers and WAL setup: [`store.py L60-L63`](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/src/durable_agent/store.py#L60-L63)
- Overhead results: [`overhead.md`](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/benchmarks/results/overhead.md)
- Memory store: [`store.py`](https://github.com/iamsammy-ak/three-tier-agent-memory/blob/cf1aea0cbaf79a991cd3bd69612a435518dd6441/src/tiered_memory/store.py)
