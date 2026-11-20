# ADR-0013: Typed hand-offs with bounded, budgeted repair

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Typed multi-agent swarm](../systems/typed-multi-agent-swarm.md), [GraphRAG knowledge pipeline](../systems/graphrag-knowledge-pipeline.md), [Self-correcting agentic RAG](../systems/self-correcting-agentic-rag.md)

## Context and problem statement

Agents that pass free-form text break on malformed output; agents that return objects bypass validation in tests. The swarm needs every hand-off checked for meaning (code parses and defines the entry point, a change request has a severity), and malformed output handled without unbounded retries.

## Decision drivers

- Validate meaning, not just syntax.
- Same path for simulated and LLM agents.
- Bounded cost of malformed output.

## Considered options

1. Free text between agents
2. Agents return Python objects
3. Agents return text; a hand-off layer validates it against frozen Pydantic artifacts with semantic validators and sends field-level repair requests at most `max_repairs` times, each charged to the budget

## Decision outcome

Chosen option 3, **agents return text; a hand-off layer validates it against frozen Pydantic artifacts with semantic validators and sends field-level repair requests at most `max_repairs` times, each charged to the budget**, because it makes the offline benchmark exercise the code that matters in production.

### Consequences

- Good, because 5% malformed simulated replies are repaired or fail cleanly within budget.
- Good, because the same pattern (validate into a schema, one repair round-trip) is used for LLM extraction in GraphRAG and structured calls in agentic RAG.
- Bad, because schema evolution is a coordinated change across roles.

### Confirmation

Tests of each artifact's validators and of the repair loop; the property test that the agent-call budget is never exceeded.

## Pros and cons of the options

### 1. Free text between agents

- Good, because flexible
- Bad, because breaks silently; no contract

### 2. Agents return Python objects

- Good, because typed
- Bad, because simulated agents skip the parsing path real models need

### 3. Agents return text; a hand-off layer validates it against frozen Pydantic artifacts with semantic validators and sends field-level repair requests at most `max_repairs` times, each charged to the budget

- Good, because one contract for every agent
- Good, because repairs are visible and bounded
- Bad, because schemas must be maintained

## More information

- Hand-off loop: [`handoff.py L86-L130`](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/src/agent_swarm/handoff.py#L86-L130)
- Artifacts: [`artifacts.py L135-L138`](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/src/agent_swarm/artifacts.py#L135-L138)
