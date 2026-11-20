# The eleven systems

Each system is its own repository with its own tests, CI, benchmark and README. None of them imports another: this
site describes how they *could* compose (see the [reference architecture](../architecture.md)), not an integrated
product. Every number below comes from a results file at the pinned commit; follow the deep-dive for the source link
and the conditions it was measured under.

| Layer | System | One line | Headline (measured) | Data |
|---|---|---|---|---|
| Edge | [Semantic cache gateway](semantic-cache-gateway.md) | OpenAI-compatible gateway: exact + guarded semantic cache, tiered routing, budgets, fallbacks | 73.2% cheaper than "large model, no cache"; 0.4% wrong semantic hits with guard rails vs 29.5% without | synthetic workload, illustrative prices |
| Trust boundary | [Inter-agent security proxy](inter-agent-security-proxy.md) | PII tokenisation, injection screening, least-privilege tool policy, hash-chained audit | injection F1 0.924 (public test split); PII F1 0.969 at precision 1.000 | public + synthetic |
| Context | [Context assembler engine](context-assembler-engine.md) | Allocates a verified token budget across eight prompt slots and explains every cut | 88.6% fact retention, 0 / 320 budget violations (fixed split: 66.2%) | synthetic |
| Memory | [Three-tier agent memory](three-tier-agent-memory.md) | Working, episodic and semantic memory with versioned facts | stale@5 0.224 vs 0.776 for a flat vector store, 1/8 of the items | synthetic |
| Retrieval | [Hybrid rerank retrieval](hybrid-rerank-retrieval.md) | BM25 + dense + fusion + cross-encoder + typed filters | hybrid RRF nDCG@10 0.718 vs 0.677 BM25 and 0.713 dense on SciFact; a cross-encoder rerank lowered it to 0.706 | public (BEIR) |
| Retrieval | [GraphRAG knowledge pipeline](graphrag-knowledge-pipeline.md) | Cited knowledge graph from text; relation-aware multi-hop search | full support@5 0.75 vs 0.19 for vector search | synthetic |
| Answering | [Self-correcting agentic RAG](self-correcting-agentic-rag.md) | Plan, retrieve, grade, verify every claim, abstain when unsure | wrong answers 4.3% vs 27.5% for naive RAG | synthetic |
| Orchestration | [Typed multi-agent swarm](typed-multi-agent-swarm.md) | Supervisor state machine, typed hand-offs, consensus, veto, grounded debate | 97.9% accepted-solution correctness (3 reviewers @ 0.8) vs 62.0% single coder | simulated competence, real execution |
| Runtime | [Durable agent state machine](durable-agent-state-machine.md) | Journal-backed workflows: leases, fencing, timers, human gates, outbox | 0 duplicate publications under 200 kills vs 10 with direct calls | synthetic, real process kills |
| Tools | [Raw MCP tool server](raw-mcp-tool-server.md) | MCP from JSON-RPC up, scoped, jailed, sandboxed and audited | 0 crashes in 10,000 fuzz cases; 1.1 ms vs 4.0 ms per call (SDK) | synthetic |
| Quality | [Trajectory eval gate](trajectory-eval-gate.md) | Grades agent runs against partial-order DAGs; blocks regressing pull requests | 100% of regressions blocked vs 55.3% outcome-only | synthetic |

## What is common to all eleven

- **Offline first.** Every number above was produced without a live language model. Model-backed components have a
  deterministic stand-in (extractive writers, rule extractors, scripted or simulated agents) and the live path is one
  key away. See [ADR-0002](../adr/0002-offline-first-stand-ins.md) and the [lessons](../lessons.md) for what that
  does and does not prove.
- **Explicit control flow.** Three of the systems are state machines with declared transitions; none uses an agent
  framework ([ADR-0001](../adr/0001-explicit-state-machines.md)).
- **Measured against a baseline.** Each benchmark compares against the naive design it replaces, and reports where
  the design loses.
- **Pinned and reproducible.** [`bench/manifest.yaml`](https://github.com/iamsammy-ak/ai-architecture-teardown/blob/main/bench/manifest.yaml)
  pins every repository to a commit, and `python -m teardown bench` re-runs the benchmarks in fresh clones and
  virtual environments ([reproducible benchmarks](../benchmarks.md)).

## How to read a deep-dive

Every page has the same sections: the problem, an architecture diagram, the key mechanisms with short code excerpts
linked to the exact lines at the pinned commit, measured results with links to the results files, trade-offs, failure
modes with where each is handled, and what I would change at scale.
