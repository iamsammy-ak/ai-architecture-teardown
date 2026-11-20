# Benchmark results (hashing backend)

Reproduce: `agentic-rag bench --backend hashing --target-risk 0.1`

- Data: the bundled synthetic handbook of a fictional company (53 documents) and 199 questions (train 80, dev 50, test 69).
- Models: embeddings `hashing-512`, cross-encoder `lexical-overlap`; no LLM (offline extractive generator).
- Abstention threshold chosen on dev for a target risk of 10.0%; all numbers below are on the test split.
- **Offline stand-in backend**: feature hashing and a lexical-overlap scorer replace the neural models. These numbers only check that the pipeline runs without downloads; the reported results are in `benchmark-models.md`.

## Answer quality and abstention (test)

| Metric | Naive RAG | Naive + similarity cut-off | Agentic, no gate | Agentic (full) |
|---|---:|---:|---:|---:|
| Answer accuracy (answerable questions) | 89.1% | 1.8% | 98.2% | 50.9% |
| Coverage (questions answered) | 100.0% | 1.4% | 87.0% | 40.6% |
| Precision of given answers | 71.0% | 100.0% | 90.0% | 100.0% |
| Wrong answers (share of all questions) | 29.0% | 0.0% | 8.7% | 0.0% |
| Correct outcome (right answer or right abstention) | 71.0% | 21.7% | 91.3% | 60.9% |
| Abstention precision (unanswerable) | 0.0% | 20.6% | 100.0% | 34.1% |
| Abstention recall (unanswerable) | 0.0% | 100.0% | 64.3% | 100.0% |
| Citation precision (gold documents) | 81.8% | 100.0% | 97.1% | 97.2% |
| Citation recall (gold documents) | 93.5% | 100.0% | 96.8% | 96.9% |
| AURC (lower is better) | 0.232 | | | 0.039 |

Oracle AURC for the same correctness labels: naive 0.049, agentic 0.027. Test risk at the dev-chosen threshold: naive cut-off 0.0%, agentic 0.0%.

## Correct outcomes by question type (test)

| Type | n | Naive RAG | Agentic |
|---|---:|---:|---:|
| single | 44 | 97.7% | 50.0% |
| multi_part | 6 | 83.3% | 66.7% |
| multi_hop | 5 | 20.0% | 40.0% |
| unanswerable | 14 | 0.0% | 100.0% |

## Hallucination detection (dev + test answers)

88 correct answers were paraphrased and perturbed (one seeded error per type). Thresholds flag at most 5.0% of clean train answers.

| Error type | n | Lexical overlap only P / R / F1 | Cross-encoder only P / R / F1 | Full verifier (+ consistency) P / R / F1 |
|---|---:|---:|---:|---:|
| swap_number | 56 | 0.65 / 0.20 / 0.30 | 0.62 / 0.18 / 0.28 | 0.85 / 0.79 / 0.81 |
| swap_entity | 38 | 0.60 / 0.24 / 0.34 | 0.54 / 0.18 / 0.27 | 0.82 / 0.97 / 0.89 |
| negation | 82 | 0.68 / 0.16 / 0.26 | 0.57 / 0.10 / 0.17 | 0.91 / 1.00 / 0.95 |
| unsupported_sentence | 88 | 0.94 / 1.00 / 0.97 | 0.94 / 1.00 / 0.97 | 0.92 / 1.00 / 0.96 |
| all | 264 | 0.95 / 0.46 / 0.62 | 0.95 / 0.43 / 0.59 | 0.97 / 0.95 / 0.96 |

Clean answers flagged (false alarms): Lexical overlap only 6.8%, Cross-encoder only 6.8%, Full verifier (+ consistency) 9.1%.

Mean latency per question: agentic 17 ms, naive 4 ms (CPU). Total run time 15.9 s.
