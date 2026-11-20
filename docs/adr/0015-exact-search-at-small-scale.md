# ADR-0015: Exact, partitioned search instead of an approximate vector index

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Three-tier agent memory](../systems/three-tier-agent-memory.md), [Semantic cache gateway](../systems/semantic-cache-gateway.md), [Hybrid rerank retrieval](../systems/hybrid-rerank-retrieval.md), [GraphRAG knowledge pipeline](../systems/graphrag-knowledge-pipeline.md)

## Context and problem statement

Four systems search embeddings: per-user memories, per-tenant cache partitions, a few thousand to a few hundred thousand documents, and graph evidence sentences. Approximate indexes (HNSW, IVF) or a vector database are the default advice.

## Decision drivers

- No recall lost to approximation at these sizes.
- No extra service or index to tune.
- Latency dominated by something else (embedding the query).

## Considered options

1. A vector database
2. An in-process ANN index (HNSW, FAISS)
3. Brute-force cosine as one matrix-vector product over a small partition (tenant, user, corpus)

## Decision outcome

Chosen option 3, **brute-force cosine as one matrix-vector product over a small partition (tenant, user, corpus)**, because at the measured sizes the query embedding, not the search, is the cost.

### Consequences

- Good, because memory recall 1.65 ms median vs 23.6 ms to embed the question.
- Good, because A gateway miss costs 43 ms median, almost all of it the embedding.
- Good, because hybrid rerank's int8 index cuts memory 4x without an approximate index.
- Bad, because revisit past roughly a million vectors per partition, or when partitions are shared across replicas.

### Confirmation

Each system's latency benchmark reports search and embedding time separately.

## Pros and cons of the options

### 1. A vector database

- Good, because scales; managed
- Bad, because A service and a dependency for every repository

### 2. An in-process ANN index (HNSW, FAISS)

- Good, because fast at scale
- Bad, because approximate recall; parameters to tune

### 3. Brute-force cosine as one matrix-vector product over a small partition (tenant, user, corpus)

- Good, because exact; trivial; fast at these sizes
- Bad, because linear in the partition size

## More information

- Memory benchmark: [`benchmark.md`](https://github.com/iamsammy-ak/three-tier-agent-memory/blob/cf1aea0cbaf79a991cd3bd69612a435518dd6441/benchmarks/results/benchmark.md)
- Gateway overhead: [`overhead.md`](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/overhead.md)
- Hybrid dense search: [`dense.py`](https://github.com/iamsammy-ak/hybrid-rerank-retrieval/blob/b43a6ecbd07c50621b42f650c3606348cf2c3d93/src/hybrid_retrieval/dense.py)
