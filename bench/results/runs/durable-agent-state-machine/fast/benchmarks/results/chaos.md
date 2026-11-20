# Chaos benchmark

Command: `PYTHONPATH=src python benchmarks/chaos_bench.py --runs 12 --crashes 6 --workers 2 --seed 7 --lease-ttl 1`

Environment: Python 3.13.2, SQLite 3.45.3, Windows 11, 12 logical CPUs. Offline: deterministic stand-in LLM and a synthetic corpus; the search tool fails 30% of attempts on purpose.

Setup: research-workflow runs are admitted two per worker (at least 12, more while kill plans remain), 2 worker processes that receive kill plans plus 1 standby worker(s) that are never killed, lease TTL 1s, seed 7. Kill plans: 75% at named crash points (seeded point and hit number), 25% at a random time after the worker is ready; a planned worker whose crash point never comes is killed after 6s. Approver decisions are seeded: approve 70%, edit 15%, reject 10%, none 5%.

| Metric | outbox (as designed) | direct call (baseline) |
|---|---|---|
| Runs | 21 | 22 |
| Worker processes killed | 6 | 5 |
| ... at a named crash point / random time / unfired plan | 3 / 3 / 0 | 2 / 3 / 0 |
| Kills that interrupted a leased run | 5 | 5 |
| Runs ending as their decision implies | 21/21 (100.0%) | 22/22 (100.0%) |
| **Runs published twice** | **0** | **0** |
| Approved runs never published | 0 | 0 |
| CMS content differing from the journal | 0 | 0 |
| Redeliveries absorbed by the idempotency key | 1 | n/a |
| Journal invariant violations | 0 | 0 |
| Completed steps executed again | 0 | 0 |
| Activity executions (StepStarted) | 92 | 96 |
| In-doubt attempts re-run (WorkerLost) | 4 | 4 |
| Retries exhausted | 0 | 0 |
| Recovery time p50 / p95 / max (s) | 1.0294 / 1.2876 / 1.2876 | 1.0052 / 1.3907 / 1.3907 |
| Replay on takeover p50 / max (ms) | 0.761 / 1.558 | 1.31 / 6.661 |
| Events / checkpoints written | 503 / 104 | 525 / 109 |
| Wall time (s) | 10.85 | 9.49 |

Failed attempts by type (outbox run): WorkerLost 4, RateLimited 3, ActivityTimeout 3, SearchUnavailable 1.

Attempts needed by the flaky `gather` step (outbox run): 1 attempt: 14 runs, 2 attempts: 5 runs, 3 attempts: 1 runs, 4 attempts: 1 runs.

Kills by crash point (outbox run): `outbox.after_deliver` 1, `random` 3, `run.after_claim` 1, `step.after_start` 1.

Recovery time is measured from the kill to the `RunRecovered` event written by the worker that took over. It is bounded below by the remaining lease (heartbeats renew it every TTL/3) and includes the poll interval and, when every healthy worker is busy or still starting, the start-up of a replacement.
