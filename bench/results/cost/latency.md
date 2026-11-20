**Support answer**

| Step | System | Measured | Input |
|---|---|---:|---|
| gateway, cache miss | semantic-cache-gateway | 42.6 ms | `gateway.overhead.miss_p50_ms` |
| proxy screening (hashing classifier) | inter-agent-security-proxy | 3.7 ms | `proxy.screen_hashing_short_p50_ms` |
| memory recall (retrieval) | three-tier-agent-memory | 1.6 ms | `memory.recall_p50_ms` |
| memory query embedding | three-tier-agent-memory | 23.6 ms | `memory.embed_p50_ms` |
| hybrid retrieval, BM25 + dense + RRF (SciFact) | hybrid-rerank-retrieval | 19.0 ms | `hybrid.rrf_p50_ms` |
| agentic RAG pipeline, mean (offline writer) | self-correcting-agentic-rag | 1,660.4 ms | `rag.latency_agentic_mean_ms` |
| context assembly | context-assembler-engine | 37.6 ms | `assembler.latency_p50_ms` |

**Coding task (3 reviewers @ 0.8)**

| Step | System | Measured | Input |
|---|---|---:|---|
| proxy screening per hand-off (hashing) | inter-agent-security-proxy | 3.7 ms | `proxy.screen_hashing_short_p50_ms` |
| MCP tools/call round trip | raw-mcp-tool-server | 1.1 ms | `mcp.calculate_p50_ms` |
| MCP run_python sandbox | raw-mcp-tool-server | 305.2 ms | `mcp.run_python_p50_ms` |

**Research workflow (durable, crash p=0)**

| Step | System | Measured | Input |
|---|---|---:|---|
| one durable step (SQLite WAL, checkpoint every transition) | durable-agent-state-machine | 2.0 ms | `durable.step_overhead_ms` |

**Pull-request gate (offline judge)**

| Step | System | Measured | Input |
|---|---|---:|---|
| grade one trajectory | trajectory-eval-gate | 6.9 ms | `trajectory.grade_ms_mean` |
