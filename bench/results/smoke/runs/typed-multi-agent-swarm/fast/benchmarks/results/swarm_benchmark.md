# Benchmark results (offline simulation)

Generated 2026-11-20 with `python benchmarks/run_benchmarks.py --seeds 2` on Python 3.13.2.
20 tasks x 2 seeds = 40 episodes per configuration.

Agent competence is simulated (coder skill, reviewer accuracy are inputs); the numbers measure what the orchestration does with that competence. Correctness is judged by real execution of the accepted code against hidden tests plus a static security check.

## Reviewers x accuracy (majority, security veto, one debate round)

| Configuration | Accepted-solution correctness (95% CI) | Accepted | Correct overall | Agent calls / task | Executor runs / task | Insecure accepted |
|---|---:|---:|---:|---:|---:|---:|
| 1 reviewer @ 0.6 | 86.1% (71.3%-93.9%) | 90.0% | 77.5% | 4.4 | 1.65 | 0 |
| 1 reviewer @ 0.7 | 86.8% (72.7%-94.2%) | 95.0% | 82.5% | 3.9 | 1.43 | 0 |
| 1 reviewer @ 0.8 | 87.2% (73.3%-94.4%) | 97.5% | 85.0% | 3.9 | 1.40 | 0 |
| 1 reviewer @ 0.9 | 97.5% (87.1%-99.6%) | 100.0% | 97.5% | 4.0 | 1.45 | 0 |
| 3 reviewers @ 0.6 | 97.3% (86.2%-99.5%) | 92.5% | 90.0% | 11.1 | 2.20 | 0 |
| 3 reviewers @ 0.7 | 100.0% (91.0%-100.0%) | 97.5% | 97.5% | 10.2 | 2.05 | 0 |
| 3 reviewers @ 0.8 | 100.0% (91.2%-100.0%) | 100.0% | 100.0% | 8.8 | 1.75 | 0 |
| 3 reviewers @ 0.9 | 100.0% (91.2%-100.0%) | 100.0% | 100.0% | 7.9 | 1.62 | 0 |
| 5 reviewers @ 0.6 | 97.2% (85.8%-99.5%) | 90.0% | 87.5% | 15.7 | 2.42 | 0 |
| 5 reviewers @ 0.7 | 100.0% (90.6%-100.0%) | 92.5% | 92.5% | 13.8 | 2.12 | 0 |
| 5 reviewers @ 0.8 | 100.0% (91.0%-100.0%) | 97.5% | 97.5% | 10.4 | 1.70 | 0 |
| 5 reviewers @ 0.9 | 100.0% (91.2%-100.0%) | 100.0% | 100.0% | 9.1 | 1.48 | 0 |

## Topology ablation

| Configuration | Accepted-solution correctness (95% CI) | Accepted | Correct overall | Agent calls / task | Executor runs / task | Insecure accepted |
|---|---:|---:|---:|---:|---:|---:|
| single coder | 65.0% (49.5%-77.9%) | 100.0% | 65.0% | 2.2 | 0.00 | 1 |
| coder + executor | 77.5% (62.5%-87.7%) | 100.0% | 77.5% | 2.4 | 1.15 | 0 |
| 3 reviewers @ 0.8 | 100.0% (91.2%-100.0%) | 100.0% | 100.0% | 8.8 | 1.75 | 0 |

## Debate on split votes (paired: same seeds, identical independent votes)

| Panel | Split first votes | Decision accuracy without debate | With debate | Fixed | Broken |
|---|---:|---:|---:|---:|---:|
| r3/a0.7 | 28 | 60.7% | 82.1% | 8 | 2 |
| r5/a0.7 | 19 | 79.0% | 73.7% | 3 | 4 |

| Configuration | Accepted-solution correctness (95% CI) | Accepted | Correct overall | Agent calls / task | Executor runs / task | Insecure accepted |
|---|---:|---:|---:|---:|---:|---:|
| 3 @ 0.7, no debate | 89.2% (75.3%-95.7%) | 92.5% | 82.5% | 6.9 | 1.57 | 0 |
| 3 reviewers @ 0.7 | 100.0% (91.0%-100.0%) | 97.5% | 97.5% | 10.2 | 2.05 | 0 |
| 5 @ 0.7, no debate | 92.3% (79.7%-97.4%) | 97.5% | 90.0% | 8.6 | 1.35 | 0 |
| 5 reviewers @ 0.7 | 100.0% (90.6%-100.0%) | 92.5% | 92.5% | 13.8 | 2.12 | 0 |

## Consensus rules, heterogeneous panel (accuracy [0.9, 0.65, 0.6])

Weights use reliabilities measured on 2 separate calibration seeds: reviewer-1 0.87, reviewer-2 0.69, reviewer-3 0.64.

| Configuration | Accepted-solution correctness (95% CI) | Accepted | Correct overall | Agent calls / task | Executor runs / task | Insecure accepted |
|---|---:|---:|---:|---:|---:|---:|
| majority | 100.0% (90.6%-100.0%) | 92.5% | 92.5% | 10.2 | 2.02 | 0 |
| reliability-weighted | 97.5% (87.1%-99.6%) | 100.0% | 97.5% | 7.4 | 1.60 | 0 |
| quorum 3 of 3 | 100.0% (89.3%-100.0%) | 80.0% | 80.0% | 12.0 | 2.42 | 0 |

## Security veto

Only the three tasks with security-defective candidates (evaluate-arithmetic, parse-config, safe-path-join), 4x the seeds. A review counts as insecure when the submission is a security-defective bank candidate.

| Configuration | Insecure submissions reviewed | Approved by the panel | Insecure accepted (final) | Correct overall | Agent calls / task |
|---|---:|---:|---:|---:|---:|
| security tasks, 3 @ 0.6, no veto | 4 | 0 (0.0%) | 0 | 91.7% | 10.9 |
| security tasks, 3 @ 0.6, veto | 4 | 0 (0.0%) | 0 | 91.7% | 10.4 |

## Correlated reviewer errors

| Configuration | Accepted-solution correctness (95% CI) | Accepted | Correct overall | Agent calls / task | Executor runs / task | Insecure accepted |
|---|---:|---:|---:|---:|---:|---:|
| 3 reviewers @ 0.7 | 100.0% (91.0%-100.0%) | 97.5% | 97.5% | 10.2 | 2.05 | 0 |
| 3 @ 0.7, correlation 0.5 | 94.1% (80.9%-98.4%) | 85.0% | 80.0% | 9.5 | 2.00 | 0 |
| 3 @ 0.7, correlation 0.9 | 91.7% (78.2%-97.1%) | 90.0% | 82.5% | 8.1 | 1.77 | 0 |

## Simulation inputs

```json
{
  "coder_skill": 0.5,
  "brief_effect": 0.3,
  "fix_rate": 0.6,
  "malformed_rate": 0.05,
  "repair_success": 0.8,
  "counterexample_rate": 0.7,
  "bogus_counterexample_rate": 0.3,
  "persuasion": 0.9,
  "conformity": 0.2,
  "error_correlation": 0.0
}
```
