# ADR-0002: Offline-first: deterministic stand-ins for every model-backed component

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Context assembler engine](../systems/context-assembler-engine.md), [GraphRAG knowledge pipeline](../systems/graphrag-knowledge-pipeline.md), [Self-correcting agentic RAG](../systems/self-correcting-agentic-rag.md), [Durable agent state machine](../systems/durable-agent-state-machine.md), [Raw MCP tool server](../systems/raw-mcp-tool-server.md), [Three-tier agent memory](../systems/three-tier-agent-memory.md), [Typed multi-agent swarm](../systems/typed-multi-agent-swarm.md), [Trajectory eval gate](../systems/trajectory-eval-gate.md), [Inter-agent security proxy](../systems/inter-agent-security-proxy.md), [Semantic cache gateway](../systems/semantic-cache-gateway.md), [Hybrid rerank retrieval](../systems/hybrid-rerank-retrieval.md)

## Context and problem statement

Every system can call a language model, but CI has no key, live calls cost money and drift, and free endpoints are rate-limited. Every number in every README must be reproducible by anyone from a clean checkout. The model-backed parts are writers (RAG generator, summaries), extractors (facts, entities, relations), judges (trajectory rubric), agents (swarm roles) and the gateway's upstream.

## Decision drivers

- Benchmarks must be reproducible and free to run.
- Tests must not need the network or a key, and must force offline mode even when a key is set.
- The offline path must exercise the same code as the live path, not bypass it.

## Considered options

1. LLM-only components
2. Mocks that return canned strings
3. Deterministic stand-ins behind the same interface (rules, extractive writers, simulated agents with a stated competence model), with the live model one key away and a fallback to the stand-in on errors

## Decision outcome

Chosen option 3, **deterministic stand-ins behind the same interface (rules, extractive writers, simulated agents with a stated competence model), with the live model one key away and a fallback to the stand-in on errors**, because it is the only option under which every published number can be re-run by a reviewer, and the stand-ins exercise the same validation, repair and control flow as live models.

### Consequences

- Good, because all eleven repositories run tests, demos and benchmarks without a key; this site's runner removes keys from the environment before running anything.
- Good, because ablations are clean: in agentic RAG both pipelines use the same extractive writer, so the difference comes from the pipeline.
- Bad, because no live-LLM number exists yet for any of the eleven systems ([lessons](../lessons.md)).
- Bad, because simulated competence (swarm) and simulated token usage (trajectory gate) are inputs, so absolute levels say nothing about a real model.

### Confirmation

Each repository's `tests/conftest.py` deletes `OPENROUTER_API_KEY` with an autouse fixture; `python -m teardown bench` strips API keys before installing or running anything.

## Pros and cons of the options

### 1. LLM-only components

- Good, because highest quality where the model is good
- Bad, because flaky tests, paid benchmarks, numbers nobody can reproduce

### 2. Mocks that return canned strings

- Good, because trivial to write
- Bad, because benchmarks measure nothing; the pipeline around the model is not exercised

### 3. Deterministic stand-ins behind the same interface (rules, extractive writers, simulated agents with a stated competence model), with the live model one key away and a fallback to the stand-in on errors

- Good, because every benchmark number is reproducible
- Good, because isolates the pipeline's contribution from the model's
- Good, because CI runs the real pipeline
- Bad, because numbers say nothing about live-model quality
- Bad, because stand-ins can flatter a design (an extractive writer rarely produces an unsupported claim for the verifier to catch)

## More information

- Swarm: simulated agents share the hand-off path: [`simulated.py`](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/src/agent_swarm/agents/simulated.py)
- Agentic RAG: offline extractive generator: [`generate.py`](https://github.com/iamsammy-ak/self-correcting-agentic-rag/blob/e84144b098876e7718e2e5e5c1043c02fe045298/src/agentic_rag/generate.py)
- Gateway: deterministic mock upstream: [`mock.py`](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/src/cache_gateway/upstreams/mock.py)
