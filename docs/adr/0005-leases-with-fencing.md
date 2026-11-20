# ADR-0005: Leases with fencing tokens for run ownership

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Durable agent state machine](../systems/durable-agent-state-machine.md)

## Context and problem statement

Several workers poll for ready runs. When a worker dies, another must take over; when a worker merely freezes (garbage collection, a suspended laptop) past its lease, it must not wake up and write over the new owner's progress.

## Decision drivers

- At most one worker commits progress for a run.
- Recovery without a coordinator service.
- A stale worker must fail loudly, not corrupt the journal.

## Considered options

1. Heartbeats only
2. An external lock service
3. Leases with an epoch (fencing token) checked inside every write transaction

## Decision outcome

Chosen option 3, **leases with an epoch (fencing token) checked inside every write transaction**, because the fencing check lives in the same transaction as the write it protects, so it cannot race.

### Consequences

- Good, because recovery p50 1.01 s with a 1 s TTL in the chaos run; no completed step executed again.
- Good, because A lost worker uses up one attempt, so a poison input eventually fails instead of looping.
- Bad, because recovery latency is bounded below by the TTL; a short TTL risks taking over from a slow worker.
- Bad, because leases compare wall-clock times, which assumes agreeing clocks (trivial on one host).

### Confirmation

`test_a_stalled_worker_is_fenced_off_after_another_takes_over` and the chaos benchmark.

## Pros and cons of the options

### 1. Heartbeats only

- Good, because simple
- Bad, because do not stop a frozen worker from writing after it wakes

### 2. An external lock service

- Good, because battle-tested semantics
- Bad, because another system to run

### 3. Leases with an epoch (fencing token) checked inside every write transaction

- Good, because A stale worker gets `LeaseLost`
- Good, because no extra service
- Bad, because recovery waits up to one lease TTL

## More information

- Fenced transaction: [`store.py L326-L357`](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/src/durable_agent/store.py#L326-L357)
