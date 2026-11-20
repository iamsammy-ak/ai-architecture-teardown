# ADR-0004: Transactional outbox and idempotency keys for side effects

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Durable agent state machine](../systems/durable-agent-state-machine.md)

## Context and problem statement

A workflow publishes an article after approval. A crash between performing a side effect and recording that it was performed cannot be closed by any code inside one process: either the effect happens twice on retry, or it may never happen. 'Exactly-once execution' is not available; something weaker but precise is.

## Decision drivers

- No duplicate publication after any crash.
- No lost publication of an approved run.
- Precise, documented delivery semantics.

## Considered options

1. Call the sink directly from the activity
2. Call directly with a stable idempotency key
3. Queue an outbox message in the step's transaction; a relay delivers at least once with a deterministic key; the sink deduplicates

## Decision outcome

Chosen option 3, **queue an outbox message in the step's transaction; a relay delivers at least once with a deterministic key; the sink deduplicates**, because it turns an unsolvable exactly-once problem into an at-least-once delivery plus deduplication, which can be tested under real crashes.

### Consequences

- Good, because chaos run: 0 duplicate publications over 756 runs and 200 kills, against 10 when the same workflow called the CMS directly; 19 redeliveries were absorbed by the key.
- Good, because the key `<run>/<state>#<visit>` is stable across attempts and workers.
- Bad, because every sink must deduplicate by key.
- Bad, because A message can sit in the outbox while the relay retries.

### Confirmation

The chaos benchmark compares outbox and direct-call configurations under the same kill schedule.

## Pros and cons of the options

### 1. Call the sink directly from the activity

- Good, because simple; synchronous
- Bad, because A crash after the call and before the commit repeats the effect

### 2. Call directly with a stable idempotency key

- Good, because works when the sink honours keys
- Bad, because depends on every external API supporting keys

### 3. Queue an outbox message in the step's transaction; a relay delivers at least once with a deterministic key; the sink deduplicates

- Good, because effectively-once effects
- Good, because the effect is decoupled from the step's commit
- Bad, because sinks must be idempotent receivers
- Bad, because delivery is asynchronous to the step

## More information

- Outbox relay: [`outbox.py L1-L7`](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/src/durable_agent/outbox.py#L1-L7)
- Idempotency key: [`context.py L54-L56`](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/src/durable_agent/context.py#L54-L56)
- Chaos results: [`chaos.md`](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/benchmarks/results/chaos.md)
