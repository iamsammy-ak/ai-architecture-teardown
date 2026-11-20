# Benchmark results

Command: `PYTHONPATH=src python benchmarks/run_benchmarks.py` · data: synthetic: the bundled scripted travel-desk agent and its simulated tools (5 cases) · judge: offline heuristic judge (no LLM).
Baseline: healthy agent, 20 runs per case (examples/travel_desk/baseline.jsonl). Each candidate run set: 3 runs per case x 5 cases; 45 run sets per scenario. Regression faults fire in each run with probability 1.0, 0.67 or 0.34 (cycled), so many regressions are intermittent.

## Regression detection (share of run sets blocked)

| Regression | Run sets | Trajectory gate | Outcome-only | Gate at rate 1.0 / 0.67 / 0.34 | Faulty runs flagged (gate / outcome) | Main blocking rule |
|---|---:|---:|---:|---|---|---|
| skipped verification | 41 | 100% | 20% | 100% / 100% / 100% | 100% / 0% | `case_regression` |
| wrong order | 45 | 100% | 9% | 100% / 100% / 100% | 100% / 0% | `case_regression` |
| extra costly calls | 45 | 100% | 13% | 100% / 100% / 100% | 100% / 3% | `case_regression` |
| forbidden tool | 45 | 100% | 87% | 100% / 100% / 100% | 100% / 24% | `forbidden_steps` |
| wrong arguments | 45 | 100% | 100% | 100% / 100% / 100% | 100% / 83% | `case_regression` |
| ungrounded reply | 45 | 100% | 100% | 100% / 100% / 100% | 100% / 100% | `case_regression` |

## False positives on benign variations (share of run sets blocked)

| Variation | Run sets | Trajectory gate | Without flakiness handling | Outcome-only | Clean runs flagged |
|---|---:|---:|---:|---:|---:|
| seed noise only | 45 | 0% | 29% | 0% | 0% |
| reordered calls | 45 | 11% | 40% | 11% | 0% |
| transient retries | 45 | 0% | 47% | 0% | 0% |
| other notify channel | 45 | 9% | 47% | 9% | 0% |
| optional steps | 45 | 2% | 31% | 2% | 0% |
| reworded | 45 | 4% | 42% | 4% | 0% |
| all combined | 45 | 89% | 89% | 9% | 0% |

Pooled: the trajectory gate blocked 100.0% of regressed run sets (outcome-only: 55.3%) and 16.5% of benign ones (without flakiness handling: 46.4%).

## Offline judge calibration (81 author-labelled replies, 40 labelled pass)

| Setting | Threshold | Accuracy | Cohen's κ | Fail recall |
|---|---:|---:|---:|---:|
| Judge's own verdict | 0.75 | 0.81 | 0.63 | 0.78 |
| Threshold fitted per fold (5-fold CV) | 0.65 | 0.81 | 0.63 | 0.73 |

Probability calibration, out-of-fold: Brier 0.175 → 0.133, ECE 0.188 → 0.129, log loss 0.790 → 0.455 (raw score → Platt scaling).
Verbosity probe: 41 words of polite filler change the mean score by -0.001; 0 fail→pass flips. Position-swap probe: consistency 1.00 over 39 pairs (the heuristic judge is position-invariant by construction; the probe matters for the LLM judge).

## Runtime

Grading: 2.78 ms per trajectory on average (p95 6.69 ms) over 8775 trajectories; one gate comparison (rules + 3 paired bootstraps of 2,000 resamples) 9.6 ms. Python 3.13.2, laptop CPU, single process; whole benchmark 48.0 s.
