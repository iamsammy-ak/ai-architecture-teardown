# ADR-0009: Session-scoped HMAC tokens for personal data, rehydrated only at the tool boundary

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Inter-agent security proxy](../systems/inter-agent-security-proxy.md)

## Context and problem statement

Agents pass text that contains personal data the next agent and its model provider do not need. Masking must keep multi-turn conversations coherent (the same customer stays the same customer), must not let tokens be joined across sessions, and must still let an allowed tool receive the real value.

## Decision drivers

- Same value, same token within a session.
- Unlinkable across sessions.
- Real values never enter a model context.
- Masked values must not look real.

## Considered options

1. Redaction (`[EMAIL]`)
2. Random IDs per occurrence
3. Format-preserving encryption
4. `<EMAIL_7f3a9c1e>` = truncated HMAC-SHA256 under a per-session key; rehydrate only into allowed tool calls for principals with `pii:reveal`

## Decision outcome

Chosen option 4, **`<EMAIL_7f3a9c1e>` = truncated HMAC-SHA256 under a per-session key; rehydrate only into allowed tool calls for principals with `pii:reveal`**, because it is the only option that is coherent within a session, unlinkable across sessions and obviously not a real value.

### Consequences

- Good, because PII F1 0.969 with precision 1.000 on the synthetic corpus; no hard negative masked.
- Good, because `send_email(to=<EMAIL_...>)` is refused when the hidden address is outside the allowlist.
- Bad, because the vault lives in one process's memory today.
- Bad, because format-based detection misses unusual spellings (every recall miss in the benchmark).

### Confirmation

Unit tests for canonical forms and collisions; the PII benchmark with 498 hard negatives.

## Pros and cons of the options

### 1. Redaction (`[EMAIL]`)

- Good, because simple
- Bad, because loses which customer is which

### 2. Random IDs per occurrence

- Good, because unlinkable
- Bad, because breaks coherence: the same address gets new IDs

### 3. Format-preserving encryption

- Good, because reversible; keeps formats
- Bad, because masked values look real and invite a model to use them

### 4. `<EMAIL_7f3a9c1e>` = truncated HMAC-SHA256 under a per-session key; rehydrate only into allowed tool calls for principals with `pii:reveal`

- Good, because coherent, unlinkable, unforgeable
- Good, because policy can reason about what a token stands for
- Bad, because the vault is state that must be shared and protected

## More information

- Token vault: [`vault.py L102-L120`](https://github.com/iamsammy-ak/inter-agent-security-proxy/blob/d2ad5b5b66bc524c70a2d14d5d7b3097109062fa/src/agent_proxy/pii/vault.py#L102-L120)
- Rehydration in the tool policy: [`policy.py L279-L287`](https://github.com/iamsammy-ak/inter-agent-security-proxy/blob/d2ad5b5b66bc524c70a2d14d5d7b3097109062fa/src/agent_proxy/policy.py#L279-L287)
