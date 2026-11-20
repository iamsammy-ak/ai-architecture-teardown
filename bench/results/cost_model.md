# Cost-per-task model

Reproduce: `PYTHONPATH=src python -m teardown cost`. Every number below is computed from `bench/cost_inputs.yaml`: measurements read from the repositories at their pinned commits, and assumptions stated with their reasons. Prices are illustrative, not quotes.

## Price tables (USD per million tokens)

| Table | small (in / out) | medium (in / out) | large (in / out) | Source |
|---|---:|---:|---:|---|
| Gateway illustrative table | 0.1 / 0.4 | 0.6 / 2.4 | 3 / 15 | [semantic-cache-gateway · `src/cache_gateway/data/default_config.yaml` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/src/cache_gateway/data/default_config.yaml) |
| Gateway narrow table | 1 / 4 | 1.5 / 6 | 3 / 15 | [semantic-cache-gateway · `src/cache_gateway/bench.py` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/src/cache_gateway/bench.py) |
| Trajectory-gate flat table | 0.5 / 1.5 | 0.5 / 1.5 | 0.5 / 1.5 | [trajectory-eval-gate · `src/trajectory_gate/example/agent.py` @ 3921cce](https://github.com/iamsammy-ak/trajectory-eval-gate/blob/3921ccec986ce71b8922398b69a055b9217073cb/src/trajectory_gate/example/agent.py) |
| Scenario: premium large tier | 0.1 / 0.4 | 0.6 / 2.4 | 15 / 75 | **hypothetical scenario** (this repository) |

## Cost per task

USD per task · per 1,000 tasks.

| Scenario | Gateway illustrative table | Gateway narrow table | Trajectory-gate flat table | Scenario: premium large tier |
|---|---:|---:|---:|---:|
| Support answer, cache bypassed (as composed) | $0.00285 · $2.85 | $0.00660 · $6.60 | $0.00220 · $2.20 | $0.0102 · $10.16 |
| Support answer, cache aligned | $0.00152 · $1.52 | $0.00363 · $3.63 | $0.00122 · $1.22 | $0.00538 · $5.38 |
| Coding task, 3 reviewers @ 0.8 | $0.0599 · $59.90 | $0.0599 · $59.90 | $0.00813 · $8.13 | $0.2995 · $299 |
| Research workflow, durable | $0.0440 · $44.02 | $0.0462 · $46.18 | $0.00695 · $6.95 | $0.2143 · $214 |
| Pull-request gate, offline judge | $0.0689 · $68.88 | $0.1550 · $155 | $0.0524 · $52.38 | $0.2457 · $246 |

## Breakdown (gateway illustrative prices)

**Support answer, cache bypassed (as composed)** (cache hit rate 0.0%, routing: logistic router mix (measured))

| Component | System | Tier | Calls / task | Billed calls | Input tokens | Output tokens | USD | Inputs used |
|---|---|---|---:|---:|---:|---:|---:|---|
| query rewrite | self-correcting-agentic-rag | routed | 0.42 | 0.42 | 168 | 50 | $0.00024 | `rag.rewrite_rounds_mean`, `support.rewrite_input_tokens`, `support.rewrite_output_tokens` |
| grounded generation | self-correcting-agentic-rag | routed | 1 | 1 | 3,072 | 250 | $0.00258 | `support.prompt_tokens`, `assembler.retention_at_3072`, `support.answer_tokens` |
| memory consolidation (amortised) | three-tier-agent-memory | small | 0.264 | 0.264 | 136 | 40 | $0.00003 | `memory.llm_calls_per_session`, `memory.turns`, `memory.sessions`, `memory.consolidation_raw_tokens`, `memory.prompt_overhead_tokens`, `memory.output_tokens` |
| **total** |  |  |  | 1.68 | 3,376 | 340 | **$0.00285** |  |

- The agentic RAG generator calls the model at temperature 0.1 and the gateway caches only requests at or below cache.max_temperature (0.0 by default), so as composed today the cache never serves this task. The 'cache aligned' scenario assumes the generator is moved to temperature 0.
- Routing shares are the gateway's measured routing of its synthetic support workload, applied to these prompts by assumption.

**Support answer, cache aligned** (cache hit rate 47.2%, routing: logistic router mix (measured))

| Component | System | Tier | Calls / task | Billed calls | Input tokens | Output tokens | USD | Inputs used |
|---|---|---|---:|---:|---:|---:|---:|---|
| query rewrite | self-correcting-agentic-rag | routed | 0.42 | 0.222 | 89 | 27 | $0.00013 | `rag.rewrite_rounds_mean`, `support.rewrite_input_tokens`, `support.rewrite_output_tokens` |
| grounded generation | self-correcting-agentic-rag | routed | 1 | 0.528 | 1,623 | 132 | $0.00136 | `support.prompt_tokens`, `assembler.retention_at_3072`, `support.answer_tokens` |
| memory consolidation (amortised) | three-tier-agent-memory | small | 0.264 | 0.264 | 136 | 40 | $0.00003 | `memory.llm_calls_per_session`, `memory.turns`, `memory.sessions`, `memory.consolidation_raw_tokens`, `memory.prompt_overhead_tokens`, `memory.output_tokens` |
| **total** |  |  |  | 1.01 | 1,847 | 198 | **$0.00152** |  |

- The agentic RAG generator calls the model at temperature 0.1 and the gateway caches only requests at or below cache.max_temperature (0.0 by default), so as composed today the cache never serves this task. The 'cache aligned' scenario assumes the generator is moved to temperature 0.
- Routing shares are the gateway's measured routing of its synthetic support workload, applied to these prompts by assumption.

**Coding task, 3 reviewers @ 0.8** (cache hit rate 0.0%, routing: logistic router mix (measured))

| Component | System | Tier | Calls / task | Billed calls | Input tokens | Output tokens | USD | Inputs used |
|---|---|---|---:|---:|---:|---:|---:|---|
| agent calls (3 reviewers @ 0.8) | typed-multi-agent-swarm | large | 9.1 | 9.1 | 10,714 | 1,850 | $0.0599 | `swarm.r3.a0.8.calls`, `swarm.r3.a0.8.tokens`, `swarm.output_share`, `swarm.system_prompt_tokens` |
| **total** |  |  |  | 9.1 | 10,714 | 1,850 | **$0.0599** |  |

Measured success rate 94.3%, so **$0.0635 per correct accepted solution**.

- Calls and payload tokens are the swarm's offline measurements with simulated agent competence; the success rate is measured by running the accepted code against hidden tests.
- Swarm agents call models at temperature 0.2 and every task is different, so no cache hit is assumed.

**Research workflow, durable** (cache hit rate 0.0%, routing: logistic router mix (measured))

| Component | System | Tier | Calls / task | Billed calls | Input tokens | Output tokens | USD | Inputs used |
|---|---|---|---:|---:|---:|---:|---:|---|
| plan | durable-agent-state-machine | medium | 1 | 1 | 1,200 | 300 | $0.00144 | `research.plan_input_tokens`, `research.plan_output_tokens` |
| draft | durable-agent-state-machine | large | 1 | 1 | 8,192 | 1,200 | $0.0426 | `research.draft_input_tokens`, `research.draft_output_tokens` |
| **total** |  |  |  | 2 | 9,392 | 1,500 | **$0.0440** |  |

- The crash model assumes every step attempt crashes independently with the same probability and that a crash wastes the tokens of the interrupted attempt.
- In the chaos benchmark, 200 kills over 756 runs caused 89 re-run attempts and no completed step ran twice.

**Pull-request gate, offline judge** (cache hit rate 0.0%, routing: logistic router mix (measured))

| Component | System | Tier | Calls / task | Billed calls | Input tokens | Output tokens | USD | Inputs used |
|---|---|---|---:|---:|---:|---:|---:|---|
| agent runs, candidate | trajectory-eval-gate | routed | 88.5 | 88.5 | 67,224 | 3,781 | $0.0517 | `trajectory.run.llm_calls`, `trajectory.run.tokens_in`, `trajectory.run.tokens_out`, `gate.cases`, `gate.candidate_runs_per_case` |
| agent runs, baseline (amortised) | trajectory-eval-gate | routed | 29.5 | 29.5 | 22,408 | 1,260 | $0.0172 | `trajectory.run.llm_calls`, `trajectory.run.tokens_in`, `trajectory.run.tokens_out`, `gate.cases`, `gate.baseline_runs_per_case`, `gate.prs_per_baseline` |
| **total** |  |  |  | 118 | 89,632 | 5,042 | **$0.0689** |  |

- Eval runs must bypass the response cache: a temperature-0 cache would replay the baseline and hide both regressions and flakiness.
- Token counts are the scripted travel-desk agent's simulated usage, not a live model's.

## Sensitivity: cache hit rate

Measured hit rates on the gateway's synthetic workloads: support 47.2%, assistant 29.4% (exact + semantic, guard rails on).

USD per 1,000 support answers, gateway illustrative prices.

| Cache hit rate | everything on the large tier | rules router mix (measured) | logistic router mix (measured) | everything on the small tier |
|---|---:|---:|---:|---:|
| 0% | $14.26 | $3.98 | $2.85 | $0.4736 |
| 10% | $12.83 | $3.59 | $2.57 | $0.4292 |
| 20% | $11.41 | $3.19 | $2.29 | $0.3848 |
| 30% | $9.99 | $2.80 | $2.01 | $0.3403 |
| 40% | $8.57 | $2.40 | $1.72 | $0.2959 |
| 50% | $7.14 | $2.01 | $1.44 | $0.2515 |
| 60% | $5.72 | $1.61 | $1.16 | $0.2071 |

## Sensitivity: reviewers

Large tier, gateway illustrative prices. Success = the accepted code passes every visible and hidden test with no major security finding (measured by execution).

| Panel | Agent calls / task | Success | USD / task | USD / correct solution |
|---|---:|---:|---:|---:|
| 1 @ 0.6 | 4.5 | 69.8% | $0.0296 | $0.0424 |
| 3 @ 0.6 | 11.4 | 82.5% | $0.0767 | $0.0930 |
| 5 @ 0.6 | 16.3 | 80.5% | $0.1139 | $0.1415 |
| 1 @ 0.7 | 4.4 | 78.8% | $0.0285 | $0.0362 |
| 3 @ 0.7 | 10.2 | 90.3% | $0.0680 | $0.0752 |
| 5 @ 0.7 | 14.1 | 90.7% | $0.0967 | $0.1066 |
| 1 @ 0.8 | 4.3 | 85.8% | $0.0275 | $0.0320 |
| 3 @ 0.8 | 9.1 | 94.3% | $0.0599 | $0.0635 |
| 5 @ 0.8 | 11.5 | 96.8% | $0.0751 | $0.0775 |
| 1 @ 0.9 | 4.1 | 93.8% | $0.0265 | $0.0283 |
| 3 @ 0.9 | 7.9 | 98.2% | $0.0510 | $0.0519 |
| 5 @ 0.9 | 10.0 | 98.5% | $0.0625 | $0.0635 |
| single coder | 2.2 | 62.0% | $0.0138 | $0.0223 |
| coder + executor | 2.3 | 72.0% | $0.0149 | $0.0207 |

Going from 1 to 3 reviewers:

| Reviewer accuracy | Success change | Extra USD / task | USD per additional correct solution |
|---|---:|---:|---:|
| 0.6 | +12.7 pts | $0.0471 | $0.3721 |
| 0.7 | +11.5 pts | $0.0394 | $0.3429 |
| 0.8 | +8.5 pts | $0.0324 | $0.3814 |
| 0.9 | +4.3 pts | $0.0244 | $0.5633 |

## Sensitivity: crashes

Measured in the chaos benchmark: 200 worker kills over 756 runs caused 89 re-run attempts (0.118 per run), 0 completed steps executed again, and 10 duplicate publications when the side effect bypassed the outbox.

Expected cost relative to a crash-free run.

| Crash probability per step | research, durable | research, restart | 15 steps, durable | 15 steps, restart |
|---|---:|---:|---:|---:|
| 0% | 1.00x | 1.00x | 1.00x | 1.00x |
| 2% | 1.02x | 1.06x | 1.02x | 1.18x |
| 5% | 1.05x | 1.17x | 1.05x | 1.54x |
| 10% | 1.11x | 1.38x | 1.11x | 2.57x |
| 15% | 1.18x | 1.65x | 1.18x | 4.64x |
| 20% | 1.25x | 1.99x | 1.25x | 9.14x |
| 25% | 1.33x | 2.43x | 1.33x | 19.69x |
| 30% | 1.43x | 3.01x | 1.43x | 46.59x |

## Measured non-LLM latency on each path

**Support answer**

| Step | System | Measured | Input |
|---|---|---:|---|
| gateway, cache miss | semantic-cache-gateway | 42.6 ms | `gateway.overhead.miss_p50_ms` |
| proxy screening (hashing classifier) | inter-agent-security-proxy | 3.7 ms | `proxy.screen_hashing_short_p50_ms` |
| memory recall (retrieval) | three-tier-agent-memory | 1.6 ms | `memory.recall_p50_ms` |
| memory query embedding | three-tier-agent-memory | 23.6 ms | `memory.embed_p50_ms` |
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

## Measured inputs

| Id | Value | What it is | Source at pinned commit | Pointer |
|---|---:|---|---|---|
| `gateway.support.requests` | 3,000 requests | Requests in the synthetic support workload | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/support/rows/0/requests` |
| `gateway.support.hit_rate.exact` | 0.3223 share | Exact-cache hit rate, support workload | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/support/rows/1/cache_hit_rate` |
| `gateway.support.hit_rate.exact_semantic` | 0.4717 share | Exact + semantic cache hit rate (bge-small, threshold 0.94, guard rails on), support workload | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/support/rows/2/cache_hit_rate` |
| `gateway.assistant.hit_rate.exact_semantic` | 0.2943 share | Exact + semantic cache hit rate, assistant workload | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/assistant/rows/2/cache_hit_rate` |
| `gateway.support.false_hit_rate` | 0.004464 share of semantic hits | Wrong answers among semantic hits at the default threshold, support workload | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/support/rows/2/false_hit_rate` |
| `gateway.support.routed.logistic.small` | 1,790 requests | Requests routed to the small tier (cache + logistic router), support workload | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/support/rows/6/served_tiers/small` |
| `gateway.support.routed.logistic.medium` | 825 requests | Requests routed to the medium tier (cache + logistic router), support workload | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/support/rows/6/served_tiers/medium` |
| `gateway.support.routed.logistic.large` | 385 requests | Requests routed to the large tier (cache + logistic router), support workload | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/support/rows/6/served_tiers/large` |
| `gateway.support.routed.rules.small` | 1,256 requests | Requests routed to the small tier (cache + rules router), support workload | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/support/rows/5/served_tiers/small` |
| `gateway.support.routed.rules.medium` | 1,169 requests | Requests routed to the medium tier (cache + rules router), support workload | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/support/rows/5/served_tiers/medium` |
| `gateway.support.routed.rules.large` | 575 requests | Requests routed to the large tier (cache + rules router), support workload | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/support/rows/5/served_tiers/large` |
| `gateway.support.under_routed.logistic` | 0.137 share | Requests answered by a smaller tier than the author's label (cache + logistic router) | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/support/rows/6/under_routed_rate` |
| `gateway.support.under_routed.rules` | 0.047 share | Requests answered by a smaller tier than the author's label (cache + rules router) | [semantic-cache-gateway · `benchmarks/results/ablation.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/ablation.json) | `/workloads/support/rows/5/under_routed_rate` |
| `gateway.overhead.miss_p50_ms` | 42.6 ms | Time inside the gateway for a cache miss with a bge-small embedding (median) | [semantic-cache-gateway · `benchmarks/results/overhead.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/overhead.json) | `/profiles/0/paths/miss/p50_ms` |
| `gateway.overhead.exact_p50_ms` | 0.3762 ms | Time inside the gateway for an exact-cache hit (median) | [semantic-cache-gateway · `benchmarks/results/overhead.json` @ b8b77e0](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/overhead.json) | `/profiles/0/paths/exact/p50_ms` |
| `rag.rewrite_rounds_mean` | 0.4203 rounds per question | Mean rewrite rounds per test question (histogram {0: 52, 1: 5, 2: 12}) | [self-correcting-agentic-rag · `benchmarks/results/benchmark-models.json` @ e84144b](https://github.com/iamsammy-ak/self-correcting-agentic-rag/blob/e84144b098876e7718e2e5e5c1043c02fe045298/benchmarks/results/benchmark-models.json) | `/test_rewrites` (derived: `histogram_mean`) |
| `rag.latency_agentic_mean_ms` | 1,660.4 ms | Mean CPU time per question of the agentic pipeline (embeddings + cross-encoder, extractive writer) | [self-correcting-agentic-rag · `benchmarks/results/benchmark-models.json` @ e84144b](https://github.com/iamsammy-ak/self-correcting-agentic-rag/blob/e84144b098876e7718e2e5e5c1043c02fe045298/benchmarks/results/benchmark-models.json) | `/latency_ms/agentic_mean` |
| `rag.latency_naive_mean_ms` | 325.7 ms | Mean CPU time per question of naive RAG | [self-correcting-agentic-rag · `benchmarks/results/benchmark-models.json` @ e84144b](https://github.com/iamsammy-ak/self-correcting-agentic-rag/blob/e84144b098876e7718e2e5e5c1043c02fe045298/benchmarks/results/benchmark-models.json) | `/latency_ms/naive_mean` |
| `assembler.scenario_tokens_mean` | 5,105 tokens | Mean size of the synthetic support conversations before assembly | [context-assembler-engine · `benchmarks/results/benchmark.json` @ 1f7863c](https://github.com/iamsammy-ak/context-assembler-engine/blob/1f7863ceab66f865fa5e69ff1d0806df8ed260fb/benchmarks/results/benchmark.json) | `/scenario_source_tokens/mean` |
| `assembler.retention_at_2048` | 95.4 percent | Required-fact retention of the engine at a 2,048-token prompt budget | [context-assembler-engine · `benchmarks/results/benchmark.json` @ 1f7863c](https://github.com/iamsammy-ak/context-assembler-engine/blob/1f7863ceab66f865fa5e69ff1d0806df8ed260fb/benchmarks/results/benchmark.json) | `/per_budget/engine/2048/fact_retention_pct` |
| `assembler.retention_at_3072` | 100 percent | Required-fact retention of the engine at a 3,072-token prompt budget | [context-assembler-engine · `benchmarks/results/benchmark.json` @ 1f7863c](https://github.com/iamsammy-ak/context-assembler-engine/blob/1f7863ceab66f865fa5e69ff1d0806df8ed260fb/benchmarks/results/benchmark.json) | `/per_budget/engine/3072/fact_retention_pct` |
| `assembler.latency_p50_ms` | 37.6 ms | Median assembly time (busy laptop CPU) | [context-assembler-engine · `benchmarks/results/benchmark.json` @ 1f7863c](https://github.com/iamsammy-ak/context-assembler-engine/blob/1f7863ceab66f865fa5e69ff1d0806df8ed260fb/benchmarks/results/benchmark.json) | `/overall/engine/latency_p50_ms` |
| `memory.turns` | 7,568 turns | Conversation turns in the benchmark (50 users x 10 sessions) | [three-tier-agent-memory · `benchmarks/results/benchmark.json` @ cf1aea0](https://github.com/iamsammy-ak/three-tier-agent-memory/blob/cf1aea0cbaf79a991cd3bd69612a435518dd6441/benchmarks/results/benchmark.json) | `/meta/turns` |
| `memory.sessions` | 500 sessions | Sessions consolidated into episodes | [three-tier-agent-memory · `benchmarks/results/benchmark.json` @ cf1aea0](https://github.com/iamsammy-ak/three-tier-agent-memory/blob/cf1aea0cbaf79a991cd3bd69612a435518dd6441/benchmarks/results/benchmark.json) | `/consolidation/episodes` |
| `memory.consolidation_raw_tokens` | 56,609 tokens | Raw tokens flushed to consolidation over all sessions (approximate counter) | [three-tier-agent-memory · `benchmarks/results/benchmark.json` @ cf1aea0](https://github.com/iamsammy-ak/three-tier-agent-memory/blob/cf1aea0cbaf79a991cd3bd69612a435518dd6441/benchmarks/results/benchmark.json) | `/consolidation/raw_tokens` |
| `memory.recall_p50_ms` | 1.65 ms | Median tiered recall time, retrieval only | [three-tier-agent-memory · `benchmarks/results/benchmark.json` @ cf1aea0](https://github.com/iamsammy-ak/three-tier-agent-memory/blob/cf1aea0cbaf79a991cd3bd69612a435518dd6441/benchmarks/results/benchmark.json) | `/systems/2/latency_ms_p50` |
| `memory.embed_p50_ms` | 23.56 ms | Median time to embed the recall query with bge-small | [three-tier-agent-memory · `benchmarks/results/benchmark.json` @ cf1aea0](https://github.com/iamsammy-ak/three-tier-agent-memory/blob/cf1aea0cbaf79a991cd3bd69612a435518dd6441/benchmarks/results/benchmark.json) | `/meta/question_embedding_ms_p50` |
| `proxy.screen_hashing_short_p50_ms` | 3.7 ms | Full screening of a short message with the hashing classifier (median) | [inter-agent-security-proxy · `benchmarks/results/latency.json` @ d2ad5b5](https://github.com/iamsammy-ak/inter-agent-security-proxy/blob/d2ad5b5b66bc524c70a2d14d5d7b3097109062fa/benchmarks/results/latency.json) | `/groups/short messages/stages/full screen with hashing (detect + mask + spotlight)/p50_ms` |
| `proxy.screen_bge_short_p50_ms` | 34.4 ms | Full screening of a short message with the bge-small classifier (median) | [inter-agent-security-proxy · `benchmarks/results/latency.json` @ d2ad5b5](https://github.com/iamsammy-ak/inter-agent-security-proxy/blob/d2ad5b5b66bc524c70a2d14d5d7b3097109062fa/benchmarks/results/latency.json) | `/groups/short messages/stages/full screen with bge-small (detect + mask + spotlight)/p50_ms` |
| `mcp.calculate_p50_ms` | 1.077 ms | tools/call round trip over stdio (median) | [raw-mcp-tool-server · `benchmarks/results/stdio_benchmark.json` @ 1cfc10e](https://github.com/iamsammy-ak/raw-mcp-tool-server/blob/1cfc10ed5a7f643fada223d85b4e6b3bbf660dab/benchmarks/results/stdio_benchmark.json) | `/latency/rawmcp · calculate (2026-07-28)/p50_ms` |
| `mcp.run_python_p50_ms` | 305.2 ms | run_python in the subprocess sandbox over stdio (median, Windows process start-up) | [raw-mcp-tool-server · `benchmarks/results/stdio_benchmark.json` @ 1cfc10e](https://github.com/iamsammy-ak/raw-mcp-tool-server/blob/1cfc10ed5a7f643fada223d85b4e6b3bbf660dab/benchmarks/results/stdio_benchmark.json) | `/latency/rawmcp · run_python sandbox (2026-07-28)/p50_ms` |
| `durable.step_overhead_ms` | 1.971 ms per step | Median cost of one durable step (synchronous=NORMAL, checkpoint every transition) | [durable-agent-state-machine · `benchmarks/results/overhead.json` @ 5facc0f](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/benchmarks/results/overhead.json) | `/per_step/0/ms_per_step` |
| `durable.chaos.runs` | 756 runs | Runs in the chaos benchmark (outbox) | [durable-agent-state-machine · `benchmarks/results/chaos.json` @ 5facc0f](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/benchmarks/results/chaos.json) | `/outbox/runs` |
| `durable.chaos.kills` | 200 kills | Worker processes killed | [durable-agent-state-machine · `benchmarks/results/chaos.json` @ 5facc0f](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/benchmarks/results/chaos.json) | `/outbox/kills` |
| `durable.chaos.in_doubt_attempts` | 89 attempts | Interrupted attempts re-run after a takeover (WorkerLost) | [durable-agent-state-machine · `benchmarks/results/chaos.json` @ 5facc0f](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/benchmarks/results/chaos.json) | `/outbox/in_doubt_attempts` |
| `durable.chaos.completed_step_reexecutions` | 0 steps | Completed steps executed again after a crash | [durable-agent-state-machine · `benchmarks/results/chaos.json` @ 5facc0f](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/benchmarks/results/chaos.json) | `/outbox/completed_step_reexecutions` |
| `durable.chaos.direct_duplicates` | 10 runs | Runs published twice when the side effect is called directly (baseline) | [durable-agent-state-machine · `benchmarks/results/chaos.json` @ 5facc0f](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/benchmarks/results/chaos.json) | `/direct/duplicate_publications` |
| `trajectory.run.llm_calls` | 5.9 calls per run | LLM turns per run of the scripted travel-desk agent (mean over 100 baseline runs) | [trajectory-eval-gate · `examples/travel_desk/baseline.jsonl` @ 3921cce](https://github.com/iamsammy-ak/trajectory-eval-gate/blob/3921ccec986ce71b8922398b69a055b9217073cb/examples/travel_desk/baseline.jsonl) | (derived: `trajectory_llm_calls_per_run`) |
| `trajectory.run.tokens_in` | 4,481.6 tokens per run | Input tokens per run (simulated by the scripted agent, mean over 100 baseline runs) | [trajectory-eval-gate · `examples/travel_desk/baseline.jsonl` @ 3921cce](https://github.com/iamsammy-ak/trajectory-eval-gate/blob/3921ccec986ce71b8922398b69a055b9217073cb/examples/travel_desk/baseline.jsonl) | (derived: `trajectory_tokens_in_per_run`) |
| `trajectory.run.tokens_out` | 252.1 tokens per run | Output tokens per run (simulated by the scripted agent, mean over 100 baseline runs) | [trajectory-eval-gate · `examples/travel_desk/baseline.jsonl` @ 3921cce](https://github.com/iamsammy-ak/trajectory-eval-gate/blob/3921ccec986ce71b8922398b69a055b9217073cb/examples/travel_desk/baseline.jsonl) | (derived: `trajectory_tokens_out_per_run`) |
| `trajectory.grade_ms_mean` | 6.89 ms | Mean time to grade one trajectory against its golden DAG | [trajectory-eval-gate · `benchmarks/results/benchmark.json` @ 3921cce](https://github.com/iamsammy-ak/trajectory-eval-gate/blob/3921ccec986ce71b8922398b69a055b9217073cb/benchmarks/results/benchmark.json) | `/runtime/grade_ms_per_trajectory_mean` |
| `swarm.r1.a0.6.calls` | 4.542 calls | Agent calls per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r1~1a0.6/metrics/calls_mean` |
| `swarm.r1.a0.6.tokens` | 2,594 tokens | Payload tokens per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r1~1a0.6/metrics/tokens_mean` |
| `swarm.r1.a0.6.success` | 0.6983 share | Tasks ending with a correct accepted solution | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r1~1a0.6/metrics/success_rate` |
| `swarm.r1.a0.7.calls` | 4.398 calls | Agent calls per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r1~1a0.7/metrics/calls_mean` |
| `swarm.r1.a0.7.tokens` | 2,496 tokens | Payload tokens per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r1~1a0.7/metrics/tokens_mean` |
| `swarm.r1.a0.7.success` | 0.7883 share | Tasks ending with a correct accepted solution | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r1~1a0.7/metrics/success_rate` |
| `swarm.r1.a0.8.calls` | 4.252 calls | Agent calls per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r1~1a0.8/metrics/calls_mean` |
| `swarm.r1.a0.8.tokens` | 2,399 tokens | Payload tokens per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r1~1a0.8/metrics/tokens_mean` |
| `swarm.r1.a0.8.success` | 0.8583 share | Tasks ending with a correct accepted solution | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r1~1a0.8/metrics/success_rate` |
| `swarm.r1.a0.9.calls` | 4.128 calls | Agent calls per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r1~1a0.9/metrics/calls_mean` |
| `swarm.r1.a0.9.tokens` | 2,309 tokens | Payload tokens per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r1~1a0.9/metrics/tokens_mean` |
| `swarm.r1.a0.9.success` | 0.9383 share | Tasks ending with a correct accepted solution | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r1~1a0.9/metrics/success_rate` |
| `swarm.r3.a0.6.calls` | 11.36 calls | Agent calls per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r3~1a0.6/metrics/calls_mean` |
| `swarm.r3.a0.6.tokens` | 6,868 tokens | Payload tokens per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r3~1a0.6/metrics/tokens_mean` |
| `swarm.r3.a0.6.success` | 0.825 share | Tasks ending with a correct accepted solution | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r3~1a0.6/metrics/success_rate` |
| `swarm.r3.a0.7.calls` | 10.19 calls | Agent calls per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r3~1a0.7/metrics/calls_mean` |
| `swarm.r3.a0.7.tokens` | 6,043 tokens | Payload tokens per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r3~1a0.7/metrics/tokens_mean` |
| `swarm.r3.a0.7.success` | 0.9033 share | Tasks ending with a correct accepted solution | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r3~1a0.7/metrics/success_rate` |
| `swarm.r3.a0.8.calls` | 9.097 calls | Agent calls per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r3~1a0.8/metrics/calls_mean` |
| `swarm.r3.a0.8.tokens` | 5,287 tokens | Payload tokens per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r3~1a0.8/metrics/tokens_mean` |
| `swarm.r3.a0.8.success` | 0.9433 share | Tasks ending with a correct accepted solution | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r3~1a0.8/metrics/success_rate` |
| `swarm.r3.a0.9.calls` | 7.922 calls | Agent calls per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r3~1a0.9/metrics/calls_mean` |
| `swarm.r3.a0.9.tokens` | 4,440 tokens | Payload tokens per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r3~1a0.9/metrics/tokens_mean` |
| `swarm.r3.a0.9.success` | 0.9817 share | Tasks ending with a correct accepted solution | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r3~1a0.9/metrics/success_rate` |
| `swarm.r5.a0.6.calls` | 16.25 calls | Agent calls per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r5~1a0.6/metrics/calls_mean` |
| `swarm.r5.a0.6.tokens` | 10,400 tokens | Payload tokens per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r5~1a0.6/metrics/tokens_mean` |
| `swarm.r5.a0.6.success` | 0.805 share | Tasks ending with a correct accepted solution | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r5~1a0.6/metrics/success_rate` |
| `swarm.r5.a0.7.calls` | 14.13 calls | Agent calls per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r5~1a0.7/metrics/calls_mean` |
| `swarm.r5.a0.7.tokens` | 8,716 tokens | Payload tokens per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r5~1a0.7/metrics/tokens_mean` |
| `swarm.r5.a0.7.success` | 0.9067 share | Tasks ending with a correct accepted solution | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r5~1a0.7/metrics/success_rate` |
| `swarm.r5.a0.8.calls` | 11.46 calls | Agent calls per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r5~1a0.8/metrics/calls_mean` |
| `swarm.r5.a0.8.tokens` | 6,605 tokens | Payload tokens per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r5~1a0.8/metrics/tokens_mean` |
| `swarm.r5.a0.8.success` | 0.9683 share | Tasks ending with a correct accepted solution | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r5~1a0.8/metrics/success_rate` |
| `swarm.r5.a0.9.calls` | 9.977 calls | Agent calls per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r5~1a0.9/metrics/calls_mean` |
| `swarm.r5.a0.9.tokens` | 5,359 tokens | Payload tokens per task | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r5~1a0.9/metrics/tokens_mean` |
| `swarm.r5.a0.9.success` | 0.985 share | Tasks ending with a correct accepted solution | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/grid~1r5~1a0.9/metrics/success_rate` |
| `swarm.single.calls` | 2.165 calls | Agent calls per task, single coder | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/topology~1single/metrics/calls_mean` |
| `swarm.single.tokens` | 1,201 tokens | Payload tokens per task, single coder | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/topology~1single/metrics/tokens_mean` |
| `swarm.single.success` | 0.62 share | Correct accepted solutions, single coder | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/topology~1single/metrics/success_rate` |
| `swarm.coder_executor.calls` | 2.298 calls | Agent calls per task, coder + executor | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/topology~1coder-executor/metrics/calls_mean` |
| `swarm.coder_executor.tokens` | 1,308 tokens | Payload tokens per task, coder + executor | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/topology~1coder-executor/metrics/tokens_mean` |
| `swarm.coder_executor.success` | 0.72 share | Correct accepted solutions, coder + executor | [typed-multi-agent-swarm · `benchmarks/results/swarm_benchmark.json` @ 37b44ec](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.json) | `/experiments/topology~1coder-executor/metrics/success_rate` |

## Assumptions

| Id | Value | Why this value |
|---|---:|---|
| `support.prompt_tokens` | 3,072 tokens | Prompt budget for one support answer: the smallest budget at which the context assembler kept every planted fact in its benchmark (measurement assembler.retention_at_3072). |
| `support.answer_tokens` | 250 tokens | Mean answer length. The agentic RAG generator caps answers at max_tokens=500 (generate.py); half of the cap is assumed. |
| `support.rewrite_input_tokens` | 400 tokens | An LLM query rewrite sees the question, the grader's diagnosis and an instruction block; no repository measures it. |
| `support.rewrite_output_tokens` | 120 tokens | A few rewritten queries returned as JSON. |
| `memory.llm_calls_per_session` | 2 calls | With a key, consolidation runs an LLM summary and an LLM fact extraction; one consolidation per session is assumed. |
| `memory.prompt_overhead_tokens` | 400 tokens | Instructions and output schema around the flushed turns of a consolidation call. |
| `memory.output_tokens` | 150 tokens | A short summary or a JSON list of facts. |
| `swarm.system_prompt_tokens` | 800 tokens per call | Role instructions plus the JSON schema of the expected artifact, which the offline payload estimate leaves out. Order of magnitude implied by agents/prompts.py, not measured. |
| `swarm.output_share` | 0.35 share of payload tokens | The swarm reports request + reply tokens as one number; replies (code, votes) are assumed to be 35% of it. |
| `research.plan_input_tokens` | 1,200 tokens | Brief, instructions and the plan schema. |
| `research.plan_output_tokens` | 300 tokens | A handful of research questions. |
| `research.draft_input_tokens` | 8,192 tokens | Draft prompt filled to the largest budget of the context assembler's sweep (8,192), where its fact retention is 100%. |
| `research.draft_output_tokens` | 1,200 tokens | A one-page brief. |
| `gate.cases` | 5 cases | The travel-desk suite has five cases (trajectory-eval-gate benchmark setup). |
| `gate.candidate_runs_per_case` | 3 runs | Runs per case for each pull request, as in the trajectory-eval-gate benchmark (benchmark.json /setup/candidate_run_set). |
| `gate.baseline_runs_per_case` | 20 runs | Baseline runs per case, as in the trajectory-eval-gate benchmark. |
| `gate.prs_per_baseline` | 20 pull requests | The baseline is re-recorded once every 20 merged pull requests, so its cost is spread over 20. |
| `gate.judge_input_tokens` | 900 tokens | Only for the optional LLM judge: rubric, facts and the final reply. |
| `gate.judge_output_tokens` | 150 tokens | A JSON verdict with a short rationale. |
