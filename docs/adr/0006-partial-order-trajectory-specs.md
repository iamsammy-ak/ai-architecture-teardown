# ADR-0006: Partial-order golden DAGs for grading agent trajectories

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Trajectory eval gate](../systems/trajectory-eval-gate.md)

## Context and problem statement

A CI gate must block agent changes that take the wrong path (refund before identity check, card data read, loops) even when the final reply looks right, without blocking harmless variation: reordered independent calls, retries of flaky tools, alternative notification channels, reworded arguments.

## Decision drivers

- Catch process regressions that outcome checks miss.
- Do not block benign reorderings.
- Deterministic verdicts, explainable per step.

## Considered options

1. Outcome-only grading (final reply + end state)
2. Exact reference sequence or edit distance
3. An LLM judge over the whole trajectory
4. Golden DAG with `after` edges, `any_of` alternatives, forbidden tools and budgets; optimal node-to-step assignment, then order repair among equally good matches

## Decision outcome

Chosen option 4, **golden DAG with `after` edges, `any_of` alternatives, forbidden tools and budgets; optimal node-to-step assignment, then order repair among equally good matches**, because it encodes exactly the dependencies that matter and nothing else, and the assignment cannot trade a correct argument match for a convenient position.

### Consequences

- Good, because 100% of regressed run sets blocked against 55.3% for outcome-only grading.
- Good, because benign reorderings were blocked only by the one genuinely flaky case, never by ordering.
- Bad, because DAG authoring effort; a case whose correct behaviour changes needs its spec and baseline updated.

### Confirmation

The benchmark's six seeded regressions and five benign variations, 45 run sets each.

## Pros and cons of the options

### 1. Outcome-only grading (final reply + end state)

- Good, because cheap; matches common benchmarks
- Bad, because blind to order and process: blocked 55.3% of seeded regressions

### 2. Exact reference sequence or edit distance

- Good, because simple to specify
- Bad, because every harmless reordering is a deviation

### 3. An LLM judge over the whole trajectory

- Good, because flexible
- Bad, because non-deterministic and biased unless calibrated; costs per pull request

### 4. Golden DAG with `after` edges, `any_of` alternatives, forbidden tools and budgets; optimal node-to-step assignment, then order repair among equally good matches

- Good, because only real dependencies are constraints
- Good, because per-step verdicts
- Good, because deterministic
- Bad, because someone has to write and maintain the DAGs

## More information

- Example golden DAG: [`refund_cancelled.yaml`](https://github.com/iamsammy-ak/trajectory-eval-gate/blob/3921ccec986ce71b8922398b69a055b9217073cb/src/trajectory_gate/example/data/golden/refund_cancelled.yaml)
- Order repair: [`align.py L166-L197`](https://github.com/iamsammy-ak/trajectory-eval-gate/blob/3921ccec986ce71b8922398b69a055b9217073cb/src/trajectory_gate/align.py#L166-L197)
- Results: [`benchmark.md`](https://github.com/iamsammy-ak/trajectory-eval-gate/blob/3921ccec986ce71b8922398b69a055b9217073cb/benchmarks/results/benchmark.md)
