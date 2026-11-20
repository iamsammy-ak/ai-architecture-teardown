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
