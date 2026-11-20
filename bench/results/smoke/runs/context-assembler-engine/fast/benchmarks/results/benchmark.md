# Benchmark results

Reproduce: `PYTHONPATH=src python benchmarks/run_benchmark.py`

Data: 5 seeded **synthetic** support conversations (scenario sizes 4,746-5,296 tokens, mean 5,002), each with 6 labelled required facts, assembled at prompt budgets of 1,024, 3,072 tokens. Tokenizer `o200k_base` (tiktoken 0.14.0), Python 3.13.2 on Windows. No model calls.

## Overall (all budgets)

| Strategy | Fact retention | Query kept | Budget violations | Mean overshoot | Mean wasted tokens | Latency p50 | Latency p95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Head truncation | 50.0% | 0.0% | 8 / 10 (80.0%) | 211 | 4 | 9.7 ms | 20.8 ms |
| Keep most recent | 66.7% | 100.0% | 10 / 10 (100.0%) | 2021 | 0 | 9.6 ms | 12.0 ms |
| Fixed proportional split | 56.7% | 100.0% | 0 / 10 (0.0%) | 0 | 326 | 8.1 ms | 13.8 ms |
| Context Assembler Engine | 90.0% | 100.0% | 0 / 10 (0.0%) | 0 | 7 | 31.2 ms | 65.9 ms |

## Required-fact retention by budget

| Budget | Head truncation | Keep most recent | Fixed proportional split | Context Assembler Engine |
|---:|---:|---:|---:|---:|
| 1,024 | 20.0% | 66.7% | 40.0% | 80.0% |
| 3,072 | 80.0% | 66.7% | 73.3% | 100.0% |

## Budget violations by budget (of each cell's assemblies)

| Budget | Head truncation | Keep most recent | Fixed proportional split | Context Assembler Engine |
|---:|---:|---:|---:|---:|
| 1,024 | 3 | 5 | 0 | 0 |
| 3,072 | 5 | 5 | 0 | 0 |

## Mean wasted tokens by budget

| Budget | Head truncation | Keep most recent | Fixed proportional split | Context Assembler Engine |
|---:|---:|---:|---:|---:|
| 1,024 | 7 | 0 | 163 | 5 |
| 3,072 | 0 | 0 | 489 | 9 |

## Retention by where the fact lives

| Location | Head truncation | Keep most recent | Fixed proportional split | Context Assembler Engine |
|---|---:|---:|---:|---:|
| `history_early` | 50.0% | 0.0% | 10.0% | 100.0% |
| `history_recent` | 50.0% | 0.0% | 100.0% | 100.0% |
| `memory` | 100.0% | 100.0% | 60.0% | 80.0% |
| `retrieved_top` | 40.0% | 100.0% | 100.0% | 100.0% |
| `retrieved_mid` | 0.0% | 100.0% | 50.0% | 60.0% |
| `tool` | 60.0% | 100.0% | 20.0% | 100.0% |

## Engine estimate accuracy

Estimated minus verified tokens per assembly: mean 2.7, min 2, max 3. Overflow repairs triggered: 0.

## Definitions and assumptions

- **Fact retention**: share of the labelled facts whose marker survives in the rendered prompt (a tool fact counts if that tool's schema is sent).
- **Budget violation**: the rendered messages and tools, re-counted with the tokenizer and the chat-format overheads, exceed the prompt budget.
- **Wasted tokens**: budget left unused while some content was dropped or cut; 0 when everything fitted or the budget was violated.
- **Latency**: wall-clock time of one assembly with a cold token-count cache, measured on a shared laptop with other work running; compare strategies with each other rather than reading the absolute values as a hardware benchmark.
- The baselines count tokens the way their simple counterparts usually do (see `src/context_assembler/bench/baselines.py`): head truncation ignores per-message chat overhead, keep-most-recent only budgets the history, the fixed split never re-verifies. Their violations come from those choices.
- The engine is not told which items hold facts. The facts are planted in places a real assistant would need them, and the scenario generator's scores are noisy on purpose.
