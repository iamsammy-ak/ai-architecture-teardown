# ADR-0007: Guard rails on top of the similarity threshold for semantic caching

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Semantic cache gateway](../systems/semantic-cache-gateway.md)

## Context and problem statement

A semantic cache reuses an answer when a new prompt is similar enough to a cached one. 'Convert 8 km to miles' and 'convert 5 km to miles' are nearly identical in embedding space and need different answers. The question is how to keep wrong hits rare without giving up most of the saving.

## Decision drivers

- Wrong cached answers under 1% of semantic hits.
- Microseconds-to-milliseconds per lookup.
- Explainable rejections.

## Considered options

1. A stricter similarity threshold
2. A cross-encoder re-check of every hit
3. Exact guard rails: numbers, named entities, negation and antonym polarity must agree

## Decision outcome

Chosen option 3, **exact guard rails: numbers, named entities, negation and antonym polarity must agree**, because the threshold sweep shows a threshold alone cannot separate paraphrases from near misses, and the guards fix the case that matters most at negligible cost.

### Consequences

- Good, because 0.4% wrong answers among semantic hits at threshold 0.94 with guards, 29.5% without.
- Good, because semantic hits add 14.9 points of hit rate on the support workload.
- Bad, because the threshold was chosen on the evaluation workload (in-sample).
- Bad, because residual wrong hits come from differences the heuristics cannot see.

### Confirmation

The threshold sweep with guard rails on and off, on the same workload.

## Pros and cons of the options

### 1. A stricter similarity threshold

- Good, because one knob
- Bad, because near misses are often *closer* than paraphrases: without guards no threshold gets below about 30% wrong

### 2. A cross-encoder re-check of every hit

- Good, because general
- Bad, because tens of milliseconds per hit; unreliable on digits

### 3. Exact guard rails: numbers, named entities, negation and antonym polarity must agree

- Good, because cheap, explainable, catches the dominant failure
- Bad, because english-centric; blind to lower-case noun swaps ('my manager' vs 'my landlord')

## More information

- Guard conflict check: [`guards.py L161-L175`](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/src/cache_gateway/guards.py#L161-L175)
- Sweep results: [`sweep_bge-small.md`](https://github.com/iamsammy-ak/semantic-cache-gateway/blob/b8b77e02b5ed88b329e3af6652060544bd4aeb57/benchmarks/results/sweep_bge-small.md)
