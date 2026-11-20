# Benchmark results

Synthetic data: 10 users × 5 sessions (926 turns), 90 probe questions {'changed': 27, 'stable': 53, 'event': 10}, seed 7, embedder `hashing-384`.
Latency is retrieval only (best of 3 per question); embedding a question takes a median 0.123 ms on top for every system except recency-window.

Reproduce: `python -m tiered_memory bench --users 10 --sessions 5 --seed 7 --embedder hashing --k 5 --budget 200 --growth-users 2 --growth-sessions 10`

| System | Recall@5 | Stale@5 | Recall@200 tok | Stale@200 tok | Recall changed / stable / event | p50 ms | p95 ms | Items/user | KB/user |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| recency-window | 0.078 | 0.000 | 0.333 | 0.111 | 0.19 / 0.04 / 0.00 | 0.04 | 0.17 | 92.6 | 2.8 |
| flat-vector | 0.667 | 0.815 | 0.811 | 0.852 | 0.67 / 0.77 / 0.10 | 0.14 | 0.27 | 92.6 | 141.7 |
| tiered | 0.622 | 0.185 | 0.800 | 0.222 | 0.70 / 0.64 / 0.30 | 1.17 | 2.23 | 14.4 | 56.3 |
| tiered-no-supersede | 0.622 | 0.741 | 0.789 | 0.926 | 0.67 / 0.66 / 0.30 | 1.07 | 1.81 | 14.4 | 56.3 |
| tiered-no-eviction | 0.622 | 0.185 | 0.800 | 0.222 | 0.70 / 0.64 / 0.30 | 1.07 | 2.35 | 14.4 | 56.3 |

Stale rates are computed over probes whose fact changed at least once.

### Stale@5 split by extraction coverage

Changed facts whose every statement used a phrasing the rule-based extractor covers (19 probes) versus facts with at least one statement it cannot parse (8 probes).

| System | all phrasings covered | some phrasings uncovered |
|---|---:|---:|
| recency-window | 0.000 | 0.000 |
| flat-vector | 0.842 | 0.750 |
| tiered | 0.000 | 0.625 |
| tiered-no-supersede | 0.789 | 0.625 |
| tiered-no-eviction | 0.000 | 0.625 |

## Rule-based fact extraction against ground truth

- Mentions: 117; recall 0.803 (covered phrasings 1.000, uncovered phrasings 0.000); precision 1.000 over 94 predictions.

## Consolidation (tiered system)

- Episodes created: 50; they keep 32.8% of the raw tokens (2344 of 7155).
- Facts added 65, superseded 29, reinforced or merged 0.

## Store growth (mean per user after each session)

| Session | recency-window | flat-vector | tiered | tiered-no-supersede | tiered-no-eviction |
|---:|---:|---:|---:|---:|---:|
| 1 | 22.0 items / 0.6 KB | 22.0 items / 33.6 KB | 4.7 items / 16.4 KB | 4.7 items / 16.4 KB | 4.7 items / 16.4 KB |
| 2 | 40.8 items / 1.2 KB | 40.8 items / 62.4 KB | 7.9 items / 28.2 KB | 7.9 items / 28.2 KB | 7.9 items / 28.2 KB |
| 3 | 58.4 items / 1.7 KB | 58.4 items / 89.3 KB | 10.2 items / 37.6 KB | 10.2 items / 37.6 KB | 10.2 items / 37.6 KB |
| 4 | 74.8 items / 2.2 KB | 74.8 items / 114.4 KB | 12.0 items / 46.1 KB | 12.0 items / 46.1 KB | 12.0 items / 46.1 KB |
| 5 | 92.6 items / 2.8 KB | 92.6 items / 141.7 KB | 14.4 items / 56.3 KB | 14.4 items / 56.3 KB | 14.4 items / 56.3 KB |

## Long-horizon store growth (2 users × 10 sessions, seed 8)

| Session | flat-vector | tiered-no-eviction | tiered |
|---:|---:|---:|---:|
| 1 | 22.0 items / 33.6 KB | 3.0 items / 12.3 KB | 3.0 items / 12.3 KB |
| 6 | 103.0 items / 157.5 KB | 14.0 items / 57.6 KB | 14.0 items / 57.6 KB |
| 10 | 157.0 items / 240.1 KB | 20.0 items / 83.2 KB | 20.0 items / 83.2 KB |
