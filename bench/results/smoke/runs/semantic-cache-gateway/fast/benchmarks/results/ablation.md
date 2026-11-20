# Cost ablation: support workload

600 synthetic requests (seed 7), embedder `hashing`, semantic threshold 0.96, baseline `large-1` with no cache = $1.060.

| Configuration | Exact hits | Semantic hits | False hits | Under-routed | Cost | Saving (default prices) | Saving (narrow prices) | Latency p50 / p95 (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline: large model, no cache | 0.0% | 0.0% | 0 | 0.0% | $1.060 | 0.0% | 0.0% | 3.22 / 6.65 |
| Exact cache only | 19.3% | 0.0% | 0 | 0.0% | $0.886 | 16.3% | 16.3% | 2.91 / 7.08 |
| Exact + semantic cache | 19.3% | 0.0% | 0 | 0.0% | $0.886 | 16.3% | 16.3% | 2.92 / 7.09 |
| Routing only (rules) | 0.0% | 0.0% | 0 | 3.7% | $0.412 | 61.1% | 44.4% | 1.19 / 6.77 |
| Routing only (logistic) | 0.0% | 0.0% | 0 | 14.3% | $0.327 | 69.1% | 50.9% | 0.79 / 7.14 |
| Cache + routing (rules) | 19.3% | 0.0% | 0 | 3.7% | $0.382 | 64.0% | 50.9% | 0.89 / 7.05 |
| Cache + routing (logistic) | 19.3% | 0.0% | 0 | 14.3% | $0.316 | 70.1% | 55.9% | 0.70 / 7.15 |

*Under-routed* = share of requests answered by a cheaper tier than the author's label for that prompt. *Narrow prices* re-prices the same calls with a table where the large tier is only ~4x the small tier.

# Cost ablation: assistant workload

600 synthetic requests (seed 7), embedder `hashing`, semantic threshold 0.96, baseline `large-1` with no cache = $1.276.

| Configuration | Exact hits | Semantic hits | False hits | Under-routed | Cost | Saving (default prices) | Saving (narrow prices) | Latency p50 / p95 (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline: large model, no cache | 0.0% | 0.0% | 0 | 0.0% | $1.276 | 0.0% | 0.0% | 3.54 / 8.61 |
| Exact cache only | 6.0% | 0.0% | 0 | 0.0% | $1.215 | 4.7% | 4.7% | 3.55 / 8.07 |
| Exact + semantic cache | 6.0% | 0.0% | 0 | 0.0% | $1.215 | 4.7% | 4.7% | 3.55 / 8.07 |
| Routing only (rules) | 0.0% | 0.0% | 0 | 8.5% | $0.750 | 41.2% | 29.9% | 1.66 / 8.50 |
| Routing only (logistic) | 0.0% | 0.0% | 0 | 15.8% | $0.677 | 47.0% | 34.4% | 1.25 / 8.80 |
| Cache + routing (rules) | 6.0% | 0.0% | 0 | 8.5% | $0.729 | 42.9% | 32.4% | 1.55 / 8.29 |
| Cache + routing (logistic) | 6.0% | 0.0% | 0 | 15.8% | $0.662 | 48.1% | 36.5% | 1.15 / 8.28 |

*Under-routed* = share of requests answered by a cheaper tier than the author's label for that prompt. *Narrow prices* re-prices the same calls with a table where the large tier is only ~4x the small tier.

Reproduce:

```bash
PYTHONPATH=src python -m cache_gateway bench --suite ablation --embedder hashing --requests 600
```

Assumptions:

- Synthetic workload written by the author (workload.py): templated prompts in paraphrase families, exact repeats, near misses, complex prompts and temperature-0.7 creative prompts across 3 tenants.
- Upstream is the deterministic offline mock: answer length depends only on the prompt (identical across models), latency is simulated per tier, faults are injected only in the chaos suite.
- Prices are the ILLUSTRATIVE table in data/default_config.yaml (dated 2026-11-20), not provider quotes.
- Token counts use the offline approximate counter (about 1 token per word plus 1 per 5 extra characters).
- Baseline = every request sent to large-1 with no cache.
- Router labels are the author's judgement of the tier a prompt needs; nobody verified answer quality.
