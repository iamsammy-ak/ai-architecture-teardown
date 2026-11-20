# ADR-0008: Implement the Model Context Protocol from the JSON-RPC layer up

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Raw MCP tool server](../systems/raw-mcp-tool-server.md)

## Context and problem statement

Tools are where a model's mistakes become actions. Securing an MCP server means owning the behaviour under malformed input, the version negotiation, which errors a model can read and recover from, and who may call what. An SDK hides those decisions.

## Decision drivers

- Every protocol and security decision visible and testable.
- Serve both the stateless 2026-07-28 revision and the handshake-era revisions.
- Never crash or pollute stdout on hostile input.

## Considered options

1. The official SDK
2. The SDK plus middleware
3. JSON-RPC 2.0 from scratch, a per-revision feature table, strict Pydantic schemas, policy as tool errors

## Decision outcome

Chosen option 3, **JSON-RPC 2.0 from scratch, a per-revision feature table, strict Pydantic schemas, policy as tool errors**, because the point of the server is the controls, and the controls live exactly in the layers an SDK hides.

### Consequences

- Good, because 10,000 fuzz cases: 0 crashes, 0 internal errors, 0 non-protocol stdout lines.
- Good, because 1.1 ms per `tools/call` round trip against 4.0 ms for the SDK server doing the same work.
- Good, because all protocol differences live in one table (`versions.py`).
- Bad, because not implemented: prompts, completions, the tasks extension, resource templates and subscriptions.
- Bad, because HTTP authentication is static bearer tokens, not OAuth 2.1.

### Confirmation

The official SDK client drives the server over stdio and HTTP in both eras in the test suite.

## Pros and cons of the options

### 1. The official SDK

- Good, because A few decorators per tool; conformance by construction
- Bad, because security-relevant behaviour hidden; one revision family at a time

### 2. The SDK plus middleware

- Good, because less code
- Bad, because still bound to the SDK's framing and error choices

### 3. JSON-RPC 2.0 from scratch, a per-revision feature table, strict Pydantic schemas, policy as tool errors

- Good, because full control of framing, errors, eras and policy
- Good, because tested against the official SDK client
- Bad, because more code to maintain as the protocol evolves

## More information

- Revision feature table: [`versions.py L38-L68`](https://github.com/iamsammy-ak/raw-mcp-tool-server/blob/1cfc10ed5a7f643fada223d85b4e6b3bbf660dab/src/rawmcp/versions.py#L38-L68)
- Fuzz results: [`fuzz_campaign.md`](https://github.com/iamsammy-ak/raw-mcp-tool-server/blob/1cfc10ed5a7f643fada223d85b4e6b3bbf660dab/benchmarks/results/fuzz_campaign.md)
