Measured in the chaos benchmark: 200 worker kills over 756 runs caused 89 re-run attempts (0.118 per run), 0 completed steps executed again, and 10 duplicate publications when the side effect bypassed the outbox.

Expected cost relative to a crash-free run.

| Crash probability per step | research, durable | research, restart | 15 steps, durable | 15 steps, restart |
|---|---:|---:|---:|---:|
| 0% | 1.00x | 1.00x | 1.00x | 1.00x |
| 2% | 1.02x | 1.06x | 1.02x | 1.18x |
| 5% | 1.05x | 1.17x | 1.05x | 1.54x |
| 10% | 1.11x | 1.38x | 1.11x | 2.57x |
| 15% | 1.18x | 1.65x | 1.18x | 4.64x |
| 20% | 1.25x | 1.99x | 1.25x | 9.14x |
| 25% | 1.33x | 2.43x | 1.33x | 19.69x |
| 30% | 1.43x | 3.01x | 1.43x | 46.59x |
