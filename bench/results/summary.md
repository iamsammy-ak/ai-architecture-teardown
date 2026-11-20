| Repository | Commit | Mode | Status | Wall time | Python | Result files |
|---|---|---|---|---:|---|---:|
| durable-agent-state-machine | [`5facc0f`](https://github.com/iamsammy-ak/durable-agent-state-machine/tree/5facc0f0b769a2e68a57b8601f0730d9f8d4382f) | fast | ✅ passed | 226 s | Python 3.13.2 | 2 / 2 |
| trajectory-eval-gate | [`3921cce`](https://github.com/iamsammy-ak/trajectory-eval-gate/tree/3921ccec986ce71b8922398b69a055b9217073cb) | fast | ✅ passed | 329 s | Python 3.13.2 | 2 / 2 |

**durable-agent-state-machine** (fast; smaller settings or a non-deterministic benchmark, so fresh values are not expected to equal the committed full-mode values)

| Headline | Fresh run | Committed | Difference |
|---|---:|---:|---:|
| runs ending as expected (share) | 1 | 1 | 0 |
| duplicate publications, outbox | 0 | 0 | 0 |
| duplicate publications, direct call | 0 | 10 | -10 |
| completed steps executed again | 0 | 0 | 0 |

**trajectory-eval-gate** (fast; same settings as the committed results on a deterministic benchmark: fresh and committed values should agree)

| Headline | Fresh run | Committed | Difference |
|---|---:|---:|---:|
| regressions blocked, trajectory gate (%) | 100 | 100 | 0 |
| regressions blocked, outcome-only (%) | 55.3 | 55.3 | 0 |
| benign run sets blocked (%) | 16.5 | 16.5 | 0 |
