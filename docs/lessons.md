# Lessons

What eleven systems and their benchmarks say when read together, where the numbers are weaker than they look, and
what I would do next with real traffic.

## What the benchmarks show

**1. Cheap exact checks beat better scores wherever exactness is the requirement.** The same pattern appears five
times, measured each time against a score-only alternative:

| Where | Score-only approach | Exact check added | Effect |
|---|---|---|---|
| Semantic cache | Similarity threshold | Numbers, entities, negation, antonyms must agree | Wrong semantic hits 29.5% → 0.4% |
| RAG verification | Cross-encoder support score | Numbers, dates, names and negation must appear in the cited unit | Swapped-number F1 0.27 → 0.81; negation 0.20 → 0.96 |
| Tool use after an injection | Injection classifier | Deterministic tool policy | Malicious calls refused even when the model obeys (demo) |
| Prompt budgets | Sum of per-item token estimates | Re-count the rendered prompt, repair | 0 / 320 violations |
| Worker ownership | Heartbeats | Fencing epoch checked inside each write | No completed step re-executed under 200 kills |

The lesson is not "rules beat models"; it is that a probabilistic signal should *propose* and an exact check should
*dispose* whenever being wrong is expensive.

**2. Ablations found where the gains come from, and they were rarely where I expected.** GraphRAG's gain is not the
graph (PageRank on it does no better than vectors) but scoring edges with entity names masked (full support@5 0.28 →
0.75). The memory system's gain over a vector store is almost entirely supersession (stale@5 0.81 → 0.22), not
compression or eviction. The swarm's cheapest ten points come from running the visible tests, not from reviewers.

**3. Every design lost somewhere, and the losses are reported.** The confidence gate in agentic RAG refuses correct
multi-part answers; GraphRAG's hybrid does not beat graph search alone; the learned router does not beat hand-written
rules; debate in a five-reviewer panel breaks almost as many decisions as it fixes; circuit breakers cost 0.2 points
of availability; the proxy's classifier flags 48% of benign agent messages; and on SciFact a cross-encoder reranker
*lowered* nDCG@10 (0.718 → 0.706) while adding 1.6 s per query, the opposite of the usual advice. A benchmark that
only shows wins is not measuring a trade-off.

**4. Independence is the hidden assumption of redundancy.** Voting reviewers stop helping as their errors correlate
(insecure acceptances 0 → 5 at correlation 0.9), and a fallback model in the same tier is no help when the whole tier
is down (the gateway chaos run's residual errors come from the window when both small models were out). Redundancy
needs diversity, and diversity needs measuring.

**5. Composition creates failure modes no component has.** Read in isolation, the gateway's temperature cap and the
RAG generator's temperature are both sensible; together they make the cache useless for RAG answers
([integration seams](architecture.md#integration-seams)). Eval runs through a temperature-0 cache would hide
regressions. These only show up when the systems are drawn on one page.

## Where the numbers are synthetic

| System | Data | Who wrote it | Model in the loop | In-sample risk |
|---|---|---|---|---|
| Semantic cache gateway | 3,000-request synthetic workloads; 180 labelled router prompts | Me | Mock upstream | Threshold chosen on the evaluation workload |
| Security proxy | deepset/prompt-injections (public) + synthetic agentic suite and PII corpus | deepset; me | bge-small classifier, no LLM | Rules written while reading the train split; agentic suite written with the rules |
| Context assembler | 40 synthetic conversations | Me | None | Extractive summariser favours identifiers, which the facts carry |
| Three-tier memory | 50 users × 10 template sessions | Me | bge-small, rule extractor | Extractor written knowing the templates (results split by coverage for that reason) |
| Hybrid rerank | BEIR SciFact, NFCorpus (public) | Dataset authors | bge-small + MiniLM cross-encoder | BM25 grid and fusion sweeps (k, alpha) on the test split, reported as sensitivity |
| GraphRAG | 54 synthetic documents, 42 questions | Me | spaCy rules, bge-small | Dev/test split; held-out extraction set written in a different style |
| Agentic RAG | 53-page synthetic handbook, 199 questions | Me | bge-small + MiniLM, extractive writer | Train/dev/test split; 69 test questions is small |
| Typed swarm | 20 tasks, 89 candidate solutions | Me | Simulated competence | Competence is an input; only execution is real |
| Durable runtime | 24 synthetic notes, real process kills | Me | Stand-in LLM | Low: the measured property is crash safety |
| Raw MCP server | Seeded fuzz cases, 22 attack scenarios | Me | None | Attacks I thought of |
| Trajectory gate | Scripted agent, 6 seeded regressions | Me | Heuristic judge | Faults and specs written by the same person |

Two of the eleven benchmarks touch public data (the proxy's injection test split and BEIR). Everything else is data I
wrote, which is the right tool for controlled ablations and the wrong tool for estimating production behaviour.

## Common limitations

- **No live-LLM numbers.** Every model-backed component was benchmarked with a deterministic stand-in
  ([ADR-0002](adr/0002-offline-first-stand-ins.md)). That isolates each design's contribution and makes every number
  reproducible, and it says nothing about how a real model writes, extracts, reviews or follows an injection.
- **Single host, mostly in memory.** Gateway caches and budgets, the proxy's vault and the swarm's state are lost on
  restart; the two durable stores are single-file SQLite.
- **Timings from one busy laptop.** Every latency on this site was measured on a Windows laptop running other jobs.
  Ratios between configurations hold up; absolute milliseconds are pessimistic.
- **Small evaluation sets.** 69 RAG test questions, 32 GraphRAG test questions, 5 trajectory cases: rankings of
  methods are more trustworthy than the exact percentages.
- **English-centric heuristics.** Guard rails, question analysis and stemming assume English; the proxy covers five
  languages for injection rules and Italian for PII formats.
- **Not integrated.** The platform view is a design ([reference architecture](architecture.md)); no request has
  crossed all eleven systems.

## What would come next with real traffic

1. **Make composition possible**: configurable model endpoints, one trace format (OpenTelemetry GenAI spans), shared
   stores for the gateway and the proxy.
2. **Shadow traffic through the gateway** to measure real repetition and routing: the hit rate and the routing mix
   are the two numbers that move the [cost model](cost.md) most, and both are borrowed from a synthetic workload today.
3. **Live-model evaluations with calibrated judges**: the RAG writer, the LLM extractors (memory, GraphRAG) and the
   swarm in LLM mode on the same splits, with the trajectory gate's calibration procedure applied to every judge.
4. **Attack success, not detection rate**: how often do real models follow injections with and without spotlighting
   and the tool policy?
5. **Real token accounting** from provider usage fields, replacing every token assumption in
   [`bench/cost_inputs.yaml`](https://github.com/iamsammy-ak/ai-architecture-teardown/blob/main/bench/cost_inputs.yaml).
6. **Load and failure tests across process boundaries**: the chaos harness of the durable runtime, extended to kill
   gateway and proxy replicas.

## What I would do differently

- **Agree the seams first.** A configurable base URL, a shared trace format and a common stand-in contract would have
  cost an hour per repository at the start and would make the integration list on the architecture page much shorter.
- **Record token usage from day one**, even with stand-ins, in the same schema a live model's usage would have.
- **Write one public-data benchmark per system** next to the synthetic one, even a small one, to keep the synthetic
  numbers honest.
