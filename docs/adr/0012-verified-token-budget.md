# ADR-0012: Verify the rendered prompt with the real tokenizer, then repair

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Context assembler engine](../systems/context-assembler-engine.md)

## Context and problem statement

Byte-pair encodings are not additive (`".\n"` is one token, not two), chat formats add per-message overhead and tool definitions are rendered in provider-specific ways. A prompt whose item counts sum to the budget can still be over it.

## Decision drivers

- Never exceed the budget.
- Waste as few tokens as possible.
- Deterministic, explainable cuts.

## Considered options

1. Trust the sum of per-item counts
2. Pad every estimate pessimistically
3. Price items as rendered (with separators), then re-count the whole rendered prompt with the tokenizer and remove the least valuable optional item until it fits

## Decision outcome

Chosen option 3, **price items as rendered (with separators), then re-count the whole rendered prompt with the tokenizer and remove the least valuable optional item until it fits**, because it turns 'usually fits' into 'always fits' for the cost of one tokenizer pass.

### Consequences

- Good, because 0 budget violations in 320 assemblies; mean 8 wasted tokens (fixed split: 902).
- Good, because estimates were 2-3 tokens above the verified count, so repair rarely runs; property tests force it with an adversarial tokenizer.
- Bad, because the guarantee is only as good as the tokenizer supplied (tiktoken covers OpenAI-family encodings).

### Confirmation

Hypothesis tests with tiktoken, an approximate tokenizer and an adversarial non-additive one.

## Pros and cons of the options

### 1. Trust the sum of per-item counts

- Good, because fast
- Bad, because 'Usually fits'

### 2. Pad every estimate pessimistically

- Good, because simple
- Bad, because wastes budget on every call and is still not a proof

### 3. Price items as rendered (with separators), then re-count the whole rendered prompt with the tokenizer and remove the least valuable optional item until it fits

- Good, because A guarantee with respect to the tokenizer
- Good, because near-zero waste
- Bad, because one extra full count per assembly

## More information

- Render-verify-repair loop: [`assembler.py L187-L206`](https://github.com/iamsammy-ak/context-assembler-engine/blob/1f7863ceab66f865fa5e69ff1d0806df8ed260fb/src/context_assembler/assembler.py#L187-L206)
