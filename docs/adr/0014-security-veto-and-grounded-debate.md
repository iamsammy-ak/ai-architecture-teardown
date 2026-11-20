# ADR-0014: A security veto and evidence-grounded debate in reviewer consensus

- **Status:** accepted
- **Date:** 2026-11-20
- **Decider:** Abhishek Kumar
- **Applies to:** [Typed multi-agent swarm](../systems/typed-multi-agent-swarm.md)

## Context and problem statement

Several reviewers vote on a code submission. Majority voting lets insecure code through when most reviewers miss the issue; plain re-voting after reading each other's arguments rewards confidence, not correctness.

## Decision drivers

- Accepting insecure code costs far more than another revision round.
- Persuasion should rest on reproducible evidence.
- Bounded extra cost.

## Considered options

1. Majority only
2. Security as just another vote
3. A veto for one credible security finding at major severity or above; on split votes one round of debate in which the Executor runs reviewers' counterexamples

## Decision outcome

Chosen option 3, **A veto for one credible security finding at major severity or above; on split votes one round of debate in which the Executor runs reviewers' counterexamples**, because the costs of the two errors are asymmetric, and execution is a better arbiter than rhetoric.

### Consequences

- Good, because insecure approvals 20.4% → 5.4% of reviews.
- Good, because debate raised decision accuracy on split votes from 64.8% to 78.0% for three reviewers.
- Bad, because for five reviewers debate fixed 42 split decisions and broke 36: herding and bogus counterexamples.
- Bad, because about 3-4 extra agent calls per task when debate runs.

### Confirmation

Paired benchmark (same seeds, identical independent votes) with debate on and off; veto on and off on the three security tasks.

## Pros and cons of the options

### 1. Majority only

- Good, because simple
- Bad, because 20.4% of insecure submissions approved (3 @ 0.6)

### 2. Security as just another vote

- Good, because uniform
- Bad, because same as majority for a lone correct reviewer

### 3. A veto for one credible security finding at major severity or above; on split votes one round of debate in which the Executor runs reviewers' counterexamples

- Good, because closes the gap majority leaves
- Good, because debate grounded in execution
- Bad, because false security alarms block good code
- Bad, because no oracle for counterexamples' expected values

## More information

- Veto and log-odds weights: [`consensus.py L28-L50`](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/src/agent_swarm/consensus.py#L28-L50)
- Results: [`swarm_benchmark.md`](https://github.com/iamsammy-ak/typed-multi-agent-swarm/blob/37b44ec34961f5d3879863a284f203e79d06c1c3/benchmarks/results/swarm_benchmark.md)
