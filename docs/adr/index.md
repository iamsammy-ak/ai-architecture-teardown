# Architecture decision records

Sixteen decisions that recur across the eleven systems, written up in the MADR format (context, decision
drivers, options considered, outcome, consequences, confirmation, links to the code at the pinned commit).
Each one records a decision that was actually made and measured in a repository; the alternatives are the
ones its README weighs, and the consequences cite the benchmark that shows the trade-off.

| ADR | Decision | Applies to |
|---|---|---|
| [ADR-0001](0001-explicit-state-machines.md) | Explicit state machines instead of an agent framework | [Self-correcting agentic RAG](../systems/self-correcting-agentic-rag.md), [Typed multi-agent swarm](../systems/typed-multi-agent-swarm.md), [Durable agent state machine](../systems/durable-agent-state-machine.md) |
| [ADR-0002](0002-offline-first-stand-ins.md) | Offline-first: deterministic stand-ins for every model-backed component | [Context assembler engine](../systems/context-assembler-engine.md), [GraphRAG knowledge pipeline](../systems/graphrag-knowledge-pipeline.md), [Self-correcting agentic RAG](../systems/self-correcting-agentic-rag.md), [Durable agent state machine](../systems/durable-agent-state-machine.md), [Raw MCP tool server](../systems/raw-mcp-tool-server.md), [Three-tier agent memory](../systems/three-tier-agent-memory.md), [Typed multi-agent swarm](../systems/typed-multi-agent-swarm.md), [Trajectory eval gate](../systems/trajectory-eval-gate.md), [Inter-agent security proxy](../systems/inter-agent-security-proxy.md), [Semantic cache gateway](../systems/semantic-cache-gateway.md), [Hybrid rerank retrieval](../systems/hybrid-rerank-retrieval.md) |
| [ADR-0003](0003-sqlite-wal-durable-store.md) | SQLite in WAL mode as the durable store | [Durable agent state machine](../systems/durable-agent-state-machine.md), [Three-tier agent memory](../systems/three-tier-agent-memory.md) |
| [ADR-0004](0004-transactional-outbox.md) | Transactional outbox and idempotency keys for side effects | [Durable agent state machine](../systems/durable-agent-state-machine.md) |
| [ADR-0005](0005-leases-with-fencing.md) | Leases with fencing tokens for run ownership | [Durable agent state machine](../systems/durable-agent-state-machine.md) |
| [ADR-0006](0006-partial-order-trajectory-specs.md) | Partial-order golden DAGs for grading agent trajectories | [Trajectory eval gate](../systems/trajectory-eval-gate.md) |
| [ADR-0007](0007-guard-rails-over-similarity-threshold.md) | Guard rails on top of the similarity threshold for semantic caching | [Semantic cache gateway](../systems/semantic-cache-gateway.md) |
| [ADR-0008](0008-mcp-without-sdk.md) | Implement the Model Context Protocol from the JSON-RPC layer up | [Raw MCP tool server](../systems/raw-mcp-tool-server.md) |
| [ADR-0009](0009-hmac-pii-tokens.md) | Session-scoped HMAC tokens for personal data, rehydrated only at the tool boundary | [Inter-agent security proxy](../systems/inter-agent-security-proxy.md) |
| [ADR-0010](0010-versioned-facts.md) | Versioned facts with validity intervals: supersede, never overwrite | [Three-tier agent memory](../systems/three-tier-agent-memory.md) |
| [ADR-0011](0011-hash-chained-audit-log.md) | Hash-chained, HMAC-signed audit logs as append-only files | [Inter-agent security proxy](../systems/inter-agent-security-proxy.md), [Raw MCP tool server](../systems/raw-mcp-tool-server.md), [Durable agent state machine](../systems/durable-agent-state-machine.md) |
| [ADR-0012](0012-verified-token-budget.md) | Verify the rendered prompt with the real tokenizer, then repair | [Context assembler engine](../systems/context-assembler-engine.md) |
| [ADR-0013](0013-typed-handoffs-bounded-repair.md) | Typed hand-offs with bounded, budgeted repair | [Typed multi-agent swarm](../systems/typed-multi-agent-swarm.md), [GraphRAG knowledge pipeline](../systems/graphrag-knowledge-pipeline.md), [Self-correcting agentic RAG](../systems/self-correcting-agentic-rag.md) |
| [ADR-0014](0014-security-veto-and-grounded-debate.md) | A security veto and evidence-grounded debate in reviewer consensus | [Typed multi-agent swarm](../systems/typed-multi-agent-swarm.md) |
| [ADR-0015](0015-exact-search-at-small-scale.md) | Exact, partitioned search instead of an approximate vector index | [Three-tier agent memory](../systems/three-tier-agent-memory.md), [Semantic cache gateway](../systems/semantic-cache-gateway.md), [Hybrid rerank retrieval](../systems/hybrid-rerank-retrieval.md), [GraphRAG knowledge pipeline](../systems/graphrag-knowledge-pipeline.md) |
| [ADR-0016](0016-rank-fusion-over-score-mixing.md) | Rank fusion instead of mixing raw scores | [GraphRAG knowledge pipeline](../systems/graphrag-knowledge-pipeline.md), [Self-correcting agentic RAG](../systems/self-correcting-agentic-rag.md), [Hybrid rerank retrieval](../systems/hybrid-rerank-retrieval.md) |

Status values follow MADR: every record here is *accepted*. When a decision is revisited (for example ADR-0003
when the runtime moves to Postgres) the old record stays and a new one supersedes it, the same rule
[ADR-0010](0010-versioned-facts.md) applies to facts.
