# Fuzz campaign

Command: `PYTHONPATH=src python benchmarks/fuzz_campaign.py --cases 1000 --seed 7`

- cases: 1000 (seed 7), 338.5 cases/s
- server crashes: 0 (the process answered every sentinel and exited cleanly with code 0 at end of input)
- stdout lines that were not valid JSON-RPC: 0
- internal errors (-32603): 0

| Case kind | count |
|---|---:|
| batch | 96 |
| big | 60 |
| bytes | 115 |
| deep | 80 |
| json | 124 |
| mutated | 409 |
| truncated | 116 |

| Reply | count |
|---|---:|
| -32600 | 466 |
| -32601 | 9 |
| -32602 | 68 |
| -32700 | 308 |
| result | 49 |
| result (isError) | 64 |
