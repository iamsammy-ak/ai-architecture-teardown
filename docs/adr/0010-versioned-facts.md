# ADR-0010: Versioned facts with validity intervals: supersede, never overwrite

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Three-tier agent memory](../systems/three-tier-agent-memory.md)

## Context and problem statement

A user says 'I live in Turin', later 'I just moved to Milan'. A vector store returns both; an overwrite loses the history and cannot answer 'where did they live in March?'. Statements can also arrive out of order (a late note about an earlier period).

## Decision drivers

- Recall the current value, not every value ever stated.
- Keep history for audit and as-of queries.
- Handle out-of-order statements.
- Decide contradictions cheaply and testably.

## Considered options

1. Update in place
2. Keep every version current (vector-store behaviour)
3. Ask an LLM whether each pair contradicts
4. Validity intervals `[valid_from, valid_to)` per single-valued slot; contradictions close the old fact and link it to its replacement; cardinality from a small predicate vocabulary

## Decision outcome

Chosen option 4, **validity intervals `[valid_from, valid_to)` per single-valued slot; contradictions close the old fact and link it to its replacement; cardinality from a small predicate vocabulary**, because it removes stale answers without losing information, and the rules are small enough to property-test.

### Consequences

- Good, because stale@5 0.224 with supersession against 0.805 without it (and 0.776 for a flat store).
- Good, because stale@5 0.000 on probes whose updates the extractor understood.
- Bad, because A missed update (unusual phrasing) leaves the old fact current: stale@5 0.500 on those probes.
- Bad, because unknown predicates default to multi-valued, so they never supersede.

### Confirmation

Property-based tests of out-of-order statements; the supersession ablation in the benchmark.

## Pros and cons of the options

### 1. Update in place

- Good, because simplest
- Bad, because history lost; out-of-order statements corrupt the present

### 2. Keep every version current (vector-store behaviour)

- Good, because nothing lost
- Bad, because stale answers (stale@5 0.776)

### 3. Ask an LLM whether each pair contradicts

- Good, because general
- Bad, because slow, paid, hard to test

### 4. Validity intervals `[valid_from, valid_to)` per single-valued slot; contradictions close the old fact and link it to its replacement; cardinality from a small predicate vocabulary

- Good, because clean current recall, full history, `as_of` queries
- Bad, because interval bookkeeping; depends on extraction

## More information

- Interval insertion: [`semantic.py L199-L242`](https://github.com/iamsammy-ak/three-tier-agent-memory/blob/cf1aea0cbaf79a991cd3bd69612a435518dd6441/src/tiered_memory/semantic.py#L199-L242)
- Time travel: [`semantic.py L271-L277`](https://github.com/iamsammy-ak/three-tier-agent-memory/blob/cf1aea0cbaf79a991cd3bd69612a435518dd6441/src/tiered_memory/semantic.py#L271-L277)
