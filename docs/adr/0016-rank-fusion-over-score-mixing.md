# ADR-0016: Rank fusion instead of mixing raw scores

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [GraphRAG knowledge pipeline](../systems/graphrag-knowledge-pipeline.md), [Self-correcting agentic RAG](../systems/self-correcting-agentic-rag.md), [Hybrid rerank retrieval](../systems/hybrid-rerank-retrieval.md)

## Context and problem statement

Three systems combine retrievers whose scores live on unrelated scales: BM25, cosine similarity, PageRank mass and beam-search path scores.

## Decision drivers

- No calibration data needed.
- Robust defaults.
- Report fusion even when it does not win.

## Considered options

1. A weighted sum of raw scores
2. Normalised scores with a tuned convex weight
3. Reciprocal rank fusion, Σ w / (k + rank)

## Decision outcome

Chosen option 3, **reciprocal rank fusion, Σ w / (k + rank)**, because it works without calibration on every pair of retrievers here; the convex blend is kept as a tunable option in hybrid rerank.

### Consequences

- Good, because agentic RAG fuses BM25 and dense lists by RRF in every retrieval round.
- Good, because graphRAG reports its weighted-RRF hybrid even though it did not beat graph search alone (full support@5 0.72 vs 0.75).
- Bad, because fusing a weaker retriever costs slots at small k (GraphRAG).
- Bad, because hybrid rerank's fusion numbers on BEIR are not measured yet.

### Confirmation

GraphRAG's benchmark reports graph, vector and hybrid side by side.

## Pros and cons of the options

### 1. A weighted sum of raw scores

- Good, because simple
- Bad, because scales differ; weights do not transfer

### 2. Normalised scores with a tuned convex weight

- Good, because can beat RRF
- Bad, because needs held-out data to tune alpha

### 3. Reciprocal rank fusion, Σ w / (k + rank)

- Good, because ranks only; one forgiving parameter
- Bad, because ignores score margins

## More information

- Hybrid RRF: [`fusion.py`](https://github.com/iamsammy-ak/hybrid-rerank-retrieval/blob/b43a6ecbd07c50621b42f650c3606348cf2c3d93/src/hybrid_retrieval/fusion.py)
- GraphRAG results: [`benchmark-bge-small-en-v1.5.md`](https://github.com/iamsammy-ak/graphrag-knowledge-pipeline/blob/21dc6d17dbd5fbc6ef827b8963c6a746f644b96e/benchmarks/results/benchmark-bge-small-en-v1.5.md)
