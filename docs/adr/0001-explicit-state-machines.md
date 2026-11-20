# ADR-0001: Explicit state machines instead of an agent framework

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Self-correcting agentic RAG](../systems/self-correcting-agentic-rag.md), [Typed multi-agent swarm](../systems/typed-multi-agent-swarm.md), [Durable agent state machine](../systems/durable-agent-state-machine.md)

## Context and problem statement

Three systems have non-trivial control flow: the agentic RAG loop (rewrite, retrieve, grade, generate, verify, revise, abstain), the swarm supervisor (research, code, execute, review, consensus, debate) and the durable workflow runtime. Each needs every decision to be inspectable after the fact, budgets that stop a run *before* it overspends, and invariants that tests can check. Agent frameworks offer graphs and planner agents, but hide routing in library code or in a model's output.

## Decision drivers

- Every transition must be explainable from a log (who acted next, and why).
- Illegal paths must be impossible, not merely unlikely.
- Budgets must be checked before a phase spends money.
- Simulated and LLM agents must run through the same control flow, so offline benchmarks exercise it.

## Considered options

1. An agent framework's graph or a planner LLM that picks the next step
2. A hand-written loop with implicit transitions (if/else in a while loop)
3. A declared transition table with one handler per state, enforced at run time

## Decision outcome

Chosen option 3, **A declared transition table with one handler per state, enforced at run time**, because it makes auditability and budget enforcement properties of the structure rather than of discipline, for about 40 lines of loop code per system.

### Consequences

- Good, because the RAG trace, the swarm routing log and the durable journal all record *why* each transition happened.
- Good, because the swarm's agent-call budget is never exceeded (property-tested), because the guard runs before a phase.
- Good, because the durable runtime records each decision (`StepCompleted` carries `next`), so replay is a fold over data and workflow code needs no determinism rules.
- Bad, because open-ended tasks that do not decompose into known phases fit poorly.
- Bad, because each system has its own small state-machine implementation; a shared one would need a common package.

### Confirmation

Agentic RAG has a test that an undeclared transition raises `TransitionError`; the swarm has a property-based test that drives random configurations through the supervisor and checks that only declared transitions occur and the agent-call budget is never exceeded; the durable runtime validates and draws each workflow definition.

## Pros and cons of the options

### 1. An agent framework's graph or a planner LLM that picks the next step

- Good, because fast to start; flexible for open-ended tasks
- Bad, because routing is non-deterministic (planner) or hidden in library code
- Bad, because budgets are checked after the fact
- Bad, because hard to property-test

### 2. A hand-written loop with implicit transitions (if/else in a while loop)

- Good, because no dependency, little code
- Bad, because nothing stops an illegal path being added later
- Bad, because the trace has to be hand-built at every branch

### 3. A declared transition table with one handler per state, enforced at run time

- Good, because illegal transitions raise; every step records source, target and reason
- Good, because property tests can drive random configurations through it
- Good, because the durable runtime can draw the definition as a Mermaid diagram
- Bad, because less flexible for open-ended work: loops and branches must be modelled as states

## More information

- Agentic RAG transition table: [`pipeline.py L54-L66`](https://github.com/iamsammy-ak/self-correcting-agentic-rag/blob/e84144b098876e7718e2e5e5c1043c02fe045298/src/agentic_rag/pipeline.py#L54-L66)
- Swarm supervisor transitions: [`supervisor.py L69-L79`](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/src/agent_swarm/supervisor.py#L69-L79)
- Durable workflow definition: [`workflow.py`](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/src/durable_agent/workflow.py)
