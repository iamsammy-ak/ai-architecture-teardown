| Repository | Commit | Mode | Status | Wall time | Python | Result files |
|---|---|---|---|---:|---|---:|
| context-assembler-engine | [`1f7863c`](https://github.com/iamsammy-ak/context-assembler-engine/tree/1f7863ceab66f865fa5e69ff1d0806df8ed260fb) | fast | ✅ passed | 9 s | Python 3.13.2 | 2 / 2 |
| inter-agent-security-proxy | [`d2ad5b5`](https://github.com/iamsammy-ak/inter-agent-security-proxy/tree/d2ad5b5b66bc524c70a2d14d5d7b3097109062fa) | fast | ✅ passed | 19 s | Python 3.13.2 | 2 / 2 |
| raw-mcp-tool-server | [`1cfc10e`](https://github.com/iamsammy-ak/raw-mcp-tool-server/tree/1cfc10ed5a7f643fada223d85b4e6b3bbf660dab) | fast | ✅ passed | 13 s | Python 3.13.2 | 4 / 4 |
| self-correcting-agentic-rag | [`e84144b`](https://github.com/iamsammy-ak/self-correcting-agentic-rag/tree/e84144b098876e7718e2e5e5c1043c02fe045298) | fast | ✅ passed | 21 s | Python 3.13.2 | 2 / 2 |
| semantic-cache-gateway | [`b8b77e0`](https://github.com/iamsammy-ak/semantic-cache-gateway/tree/b8b77e02b5ed88b329e3af6652060544bd4aeb57) | fast | ✅ passed | 19 s | Python 3.13.2 | 2 / 2 |
| three-tier-agent-memory | [`cf1aea0`](https://github.com/iamsammy-ak/three-tier-agent-memory/tree/cf1aea0cbaf79a991cd3bd69612a435518dd6441) | fast | ✅ passed | 16 s | Python 3.13.2 | 2 / 2 |
| typed-multi-agent-swarm | [`37b44ec`](https://github.com/iamsammy-ak/typed-multi-agent-swarm/tree/37b44ec34961f5d3879863a284f203e79d06c1c3) | fast | ✅ passed | 34 s | Python 3.13.2 | 2 / 2 |

**context-assembler-engine** (fast; smaller settings or a non-deterministic benchmark, so fresh values are not expected to equal the committed full-mode values)

| Headline | Fresh run | Committed | Difference |
|---|---:|---:|---:|
| fact retention, engine (%) | 90 | 88.6 | 1.4 |
| budget violations, engine | 0 | 0 | 0 |
| fact retention, fixed split (%) | 56.7 | 66.2 | -9.5 |

**inter-agent-security-proxy** (fast; same settings as the committed results on a deterministic benchmark: fresh and committed values should agree)

| Headline | Fresh run | Committed | Difference |
|---|---:|---:|---:|
| PII F1, regex + validators | 0.9691 | 0.9691 | 0 |
| PII precision, regex + validators | 1 | 1 | 0 |

**raw-mcp-tool-server** (fast; smaller settings or a non-deterministic benchmark, so fresh values are not expected to equal the committed full-mode values)

| Headline | Fresh run | Committed | Difference |
|---|---:|---:|---:|
| server crashes under fuzzing | 0 | 0 | 0 |
| internal errors under fuzzing | 0 | 0 | 0 |
| non-JSON-RPC stdout lines | 0 | 0 | 0 |

**self-correcting-agentic-rag** (fast; same settings as the committed results on a deterministic benchmark: fresh and committed values should agree)

| Headline | Fresh run | Committed | Difference |
|---|---:|---:|---:|
| wrong answers, agentic (share) | 0 | 0 | 0 |
| wrong answers, naive (share) | 0.2899 | 0.2899 | 0 |

**semantic-cache-gateway** (fast; smaller settings or a non-deterministic benchmark, so fresh values are not expected to equal the committed full-mode values)

| Headline | Fresh run | Committed | Difference |
|---|---:|---:|---:|
| saving, cache + logistic routing, support (%) | 70.14 | 73.22 | -3.077 |
| hit rate, exact + semantic, support | 0.1933 | 0.4717 | -0.2783 |

**three-tier-agent-memory** (fast; smaller settings or a non-deterministic benchmark, so fresh values are not expected to equal the committed full-mode values)

| Headline | Fresh run | Committed | Difference |
|---|---:|---:|---:|
| recall@5, tiered | 0.6222 | 0.8044 | -0.1822 |
| stale@5, tiered | 0.1852 | 0.2241 | -0.0389 |
| stale@5, flat vector store | 0.8148 | 0.7759 | 0.0389 |

**typed-multi-agent-swarm** (fast; smaller settings or a non-deterministic benchmark, so fresh values are not expected to equal the committed full-mode values)

| Headline | Fresh run | Committed | Difference |
|---|---:|---:|---:|
| accepted-solution correctness, 3 reviewers @ 0.8 | 1 | 0.9792 | 0.0208 |
| agent calls per task, 3 reviewers @ 0.8 | 8.75 | 9.097 | -0.3467 |
| correctness, single coder | 0.65 | 0.62 | 0.03 |
