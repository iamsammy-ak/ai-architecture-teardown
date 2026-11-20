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
