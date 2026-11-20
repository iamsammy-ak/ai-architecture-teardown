# ADR-0011: Hash-chained, HMAC-signed audit logs as append-only files

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Inter-agent security proxy](../systems/inter-agent-security-proxy.md), [Raw MCP tool server](../systems/raw-mcp-tool-server.md), [Durable agent state machine](../systems/durable-agent-state-machine.md)

## Context and problem statement

Security decisions (masking, injection verdicts, tool allow/deny, reveals) need an audit trail that an attacker with file access cannot quietly edit, truncate or rewrite, and that existing log pipelines can ingest without a database.

## Decision drivers

- Detect edits, deletions, reordering, truncation and full rewrites.
- No raw personal values in logs.
- Verifiable offline; shippable as JSON Lines.

## Considered options

1. A database table
2. Plain JSON Lines
3. JSON Lines where each record carries the previous record's hash, an optional HMAC and a pinned head

## Decision outcome

Chosen option 3, **JSON Lines where each record carries the previous record's hash, an optional HMAC and a pinned head**, because it gives tamper evidence with nothing but a file and a key, and `verify-audit` pinpoints the first bad record.

### Consequences

- Good, because records carry tokens and rule ids, never raw values.
- Good, because the same append-only principle is enforced in the durable journal by SQL triggers.
- Bad, because inconsistent across systems: the MCP server's audit log is plain JSONL (argument hashes, no chain).
- Bad, because tamper evidence, not prevention: shipping to write-once storage is still needed.

### Confirmation

Tests that edit, delete, reorder and truncate records and check `verify-audit` reports each.

## Pros and cons of the options

### 1. A database table

- Good, because queryable
- Bad, because an admin can rewrite rows; another service to run

### 2. Plain JSON Lines

- Good, because easy to ship
- Bad, because silent edits are undetectable

### 3. JSON Lines where each record carries the previous record's hash, an optional HMAC and a pinned head

- Good, because edits and reordering break the chain; the HMAC stops a full rewrite; the pinned head catches truncation
- Bad, because the key and the head must be kept outside the file

## More information

- Proxy audit append: [`audit.py L88-L111`](https://github.com/iamsammy-ak/inter-agent-security-proxy/blob/d2ad5b5b66bc524c70a2d14d5d7b3097109062fa/src/agent_proxy/audit.py#L88-L111)
- MCP audit log: [`audit.py`](https://github.com/iamsammy-ak/raw-mcp-tool-server/blob/1cfc10ed5a7f643fada223d85b4e6b3bbf660dab/src/rawmcp/audit.py)
- Durable journal triggers: [`store.py L60-L63`](https://github.com/iamsammy-ak/durable-agent-state-machine/blob/5facc0f0b769a2e68a57b8601f0730d9f8d4382f/src/durable_agent/store.py#L60-L63)
