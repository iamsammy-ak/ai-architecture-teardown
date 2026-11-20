"""Cost-per-task model for four representative tasks on the composed platform.

Each task is a list of LLM calls. A call has an expected count per task, a size in input and output tokens, a tier
(or ``routed``, meaning it goes through the gateway's router) and a flag saying whether the gateway cache may serve
it. Every count and size is computed from a measurement or a stated assumption in ``bench/cost_inputs.yaml``, and
each call records which ones it used (``basis``), so every figure in the output traces back to a file at a pinned
commit or to a written-down assumption.

Price = sum over calls of count x (1 - cache hit rate, if cacheable) x price(tier, input, output).
For a routed call, price(tier, ...) is averaged over the routing mix.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .inputs import TIERS, CostInputs, PriceTable, Tier

CallTier = Literal["small", "medium", "large", "routed"]
Router = Literal["all-large", "all-small", "rules", "logistic"]
ROUTERS: tuple[Router, ...] = ("all-large", "rules", "logistic", "all-small")
REVIEWER_COUNTS: tuple[int, ...] = (1, 3, 5)
REVIEWER_ACCURACIES: tuple[float, ...] = (0.6, 0.7, 0.8, 0.9)


class Call(BaseModel):
    """Expected LLM calls of one kind within a task."""

    model_config = ConfigDict(frozen=True)

    component: str
    system: str
    count: float = Field(ge=0)
    input_tokens: float = Field(ge=0)
    output_tokens: float = Field(ge=0)
    tier: CallTier
    cacheable: bool
    basis: tuple[str, ...]


class LatencyItem(BaseModel):
    """A measured non-LLM time on the task's path."""

    model_config = ConfigDict(frozen=True)

    label: str
    system: str
    measurement: str
    ms: float


class TaskSpec(BaseModel):
    """A representative task: its LLM calls, measured non-LLM latencies and caveats."""

    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    summary: str
    systems: tuple[str, ...]
    calls: tuple[Call, ...]
    latency: tuple[LatencyItem, ...] = ()
    success_rate: float | None = Field(default=None, gt=0, le=1)
    notes: tuple[str, ...] = ()


class Knobs(BaseModel):
    """The settings a task is priced under."""

    model_config = ConfigDict(frozen=True)

    price_table: str
    cache_hit_rate: float = Field(default=0.0, ge=0, le=1)
    router: Router = "logistic"


class CallCost(BaseModel):
    """What one kind of call costs per task."""

    model_config = ConfigDict(frozen=True)

    component: str
    system: str
    tier: CallTier
    calls: float
    billed_calls: float
    input_tokens: float
    output_tokens: float
    usd: float


class TaskCost(BaseModel):
    """The price of one task under one set of knobs."""

    model_config = ConfigDict(frozen=True)

    task: str
    knobs: Knobs
    lines: tuple[CallCost, ...]
    success_rate: float | None = None

    @property
    def usd(self) -> float:
        """Expected USD per task."""
        return sum(line.usd for line in self.lines)

    @property
    def billed_calls(self) -> float:
        """Expected calls that reach a model (cache misses)."""
        return sum(line.billed_calls for line in self.lines)

    @property
    def input_tokens(self) -> float:
        """Expected billed input tokens per task."""
        return sum(line.input_tokens for line in self.lines)

    @property
    def output_tokens(self) -> float:
        """Expected billed output tokens per task."""
        return sum(line.output_tokens for line in self.lines)

    @property
    def usd_per_success(self) -> float | None:
        """Expected USD per successful task, when the task has a measured success rate."""
        return None if self.success_rate is None else self.usd / self.success_rate


class Scenario(BaseModel):
    """A named task + knobs combination used in the headline table."""

    model_config = ConfigDict(frozen=True)

    id: str
    label: str
    task: TaskSpec
    cache_hit_rate: float = Field(ge=0, le=1)
    router: Router

    @model_validator(mode="after")
    def _cacheable(self) -> Scenario:
        if self.cache_hit_rate > 0 and not any(c.cacheable for c in self.task.calls):
            raise ValueError(f"{self.id}: a cache hit rate only applies to cacheable calls")
        return self


# ------------------------------------------------------------------------------------------------ routing


def routing_mix(inputs: CostInputs, router: Router) -> dict[Tier, float]:
    """Share of routed calls per tier: fixed for ``all-*``, measured on the gateway's support workload otherwise."""
    if router == "all-large":
        return {"small": 0.0, "medium": 0.0, "large": 1.0}
    if router == "all-small":
        return {"small": 1.0, "medium": 0.0, "large": 0.0}
    counts = {tier: inputs.value(f"gateway.support.routed.{router}.{tier}") for tier in TIERS}
    total = sum(counts.values())
    return {tier: counts[tier] / total for tier in TIERS}


def call_price(table: PriceTable, tier: CallTier, mix: dict[Tier, float], input_tokens: float,
               output_tokens: float) -> float:
    """USD for one call, averaged over the routing mix when the call is routed."""
    if tier == "routed":
        return sum(share * table.cost(t, input_tokens, output_tokens) for t, share in mix.items())
    return table.cost(tier, input_tokens, output_tokens)


def estimate(task: TaskSpec, knobs: Knobs, inputs: CostInputs) -> TaskCost:
    """Price a task under the given knobs."""
    table = inputs.price_table(knobs.price_table)
    mix = routing_mix(inputs, knobs.router)
    lines = []
    for call in task.calls:
        billed = call.count * ((1 - knobs.cache_hit_rate) if call.cacheable else 1.0)
        unit = call_price(table, call.tier, mix, call.input_tokens, call.output_tokens)
        lines.append(
            CallCost(
                component=call.component,
                system=call.system,
                tier=call.tier,
                calls=call.count,
                billed_calls=billed,
                input_tokens=billed * call.input_tokens,
                output_tokens=billed * call.output_tokens,
                usd=billed * unit,
            )
        )
    return TaskCost(task=task.id, knobs=knobs, lines=tuple(lines), success_rate=task.success_rate)


# ------------------------------------------------------------------------------------------------ tasks


def support_answer(inputs: CostInputs) -> TaskSpec:
    """A customer-support answer: gateway -> security proxy -> memory recall -> agentic RAG -> context assembler.

    LLM calls: the agentic RAG rewrite loop (measured mean rounds per question), one generation over a prompt
    assembled to the budget at which the assembler kept every planted fact, and memory consolidation amortised over
    the answers of a session.
    """
    v = inputs.value
    sessions_turns = v("memory.turns") / v("memory.sessions")  # turns per session (user + assistant)
    answers_per_session = sessions_turns / 2
    raw_per_session = v("memory.consolidation_raw_tokens") / v("memory.sessions")
    consolidation_input = raw_per_session + v("memory.prompt_overhead_tokens")
    calls = (
        Call(component="query rewrite", system="self-correcting-agentic-rag", count=v("rag.rewrite_rounds_mean"),
             input_tokens=v("support.rewrite_input_tokens"), output_tokens=v("support.rewrite_output_tokens"),
             tier="routed", cacheable=True,
             basis=("rag.rewrite_rounds_mean", "support.rewrite_input_tokens", "support.rewrite_output_tokens")),
        Call(component="grounded generation", system="self-correcting-agentic-rag", count=1.0,
             input_tokens=v("support.prompt_tokens"), output_tokens=v("support.answer_tokens"),
             tier="routed", cacheable=True,
             basis=("support.prompt_tokens", "assembler.retention_at_3072", "support.answer_tokens")),
        Call(component="memory consolidation (amortised)", system="three-tier-agent-memory",
             count=v("memory.llm_calls_per_session") / answers_per_session,
             input_tokens=consolidation_input, output_tokens=v("memory.output_tokens"),
             tier="small", cacheable=False,
             basis=("memory.llm_calls_per_session", "memory.turns", "memory.sessions",
                    "memory.consolidation_raw_tokens", "memory.prompt_overhead_tokens", "memory.output_tokens")),
    )
    latency = (
        LatencyItem(label="gateway, cache miss", system="semantic-cache-gateway",
                    measurement="gateway.overhead.miss_p50_ms", ms=v("gateway.overhead.miss_p50_ms")),
        LatencyItem(label="proxy screening (hashing classifier)", system="inter-agent-security-proxy",
                    measurement="proxy.screen_hashing_short_p50_ms", ms=v("proxy.screen_hashing_short_p50_ms")),
        LatencyItem(label="memory recall (retrieval)", system="three-tier-agent-memory",
                    measurement="memory.recall_p50_ms", ms=v("memory.recall_p50_ms")),
        LatencyItem(label="memory query embedding", system="three-tier-agent-memory",
                    measurement="memory.embed_p50_ms", ms=v("memory.embed_p50_ms")),
        LatencyItem(label="agentic RAG pipeline, mean (offline writer)", system="self-correcting-agentic-rag",
                    measurement="rag.latency_agentic_mean_ms", ms=v("rag.latency_agentic_mean_ms")),
        LatencyItem(label="context assembly", system="context-assembler-engine",
                    measurement="assembler.latency_p50_ms", ms=v("assembler.latency_p50_ms")),
    )
    return TaskSpec(
        id="support-answer",
        title="Support answer",
        summary="One answer through the gateway, the proxy, memory recall, agentic RAG and the context assembler.",
        systems=("semantic-cache-gateway", "inter-agent-security-proxy", "three-tier-agent-memory",
                 "self-correcting-agentic-rag", "hybrid-rerank-retrieval", "context-assembler-engine"),
        calls=calls,
        latency=latency,
        notes=(
            "The agentic RAG generator calls the model at temperature 0.1 and the gateway caches only requests at or "
            "below cache.max_temperature (0.0 by default), so as composed today the cache never serves this task. "
            "The 'cache aligned' scenario assumes the generator is moved to temperature 0.",
            "Routing shares are the gateway's measured routing of its synthetic support workload, applied to these "
            "prompts by assumption.",
        ),
    )


def coding_task(inputs: CostInputs, reviewers: int = 3, accuracy: float = 0.8, tier: Tier = "large",
                topology: Literal["swarm", "single", "coder-executor"] = "swarm") -> TaskSpec:
    """A coding task through the typed swarm, sized by the swarm benchmark's measured calls and payload tokens."""
    v = inputs.value
    if topology == "swarm":
        if reviewers not in REVIEWER_COUNTS or accuracy not in REVIEWER_ACCURACIES:
            raise ValueError(f"no measurement for {reviewers} reviewers at accuracy {accuracy}")
        key = f"swarm.r{reviewers}.a{accuracy}"
        label = f"{reviewers} reviewer{'s' if reviewers > 1 else ''} @ {accuracy}"
    else:
        key = "swarm.single" if topology == "single" else "swarm.coder_executor"
        label = "single coder" if topology == "single" else "coder + executor"
    calls_per_task, payload = v(f"{key}.calls"), v(f"{key}.tokens")
    out_share, system_prompt = v("swarm.output_share"), v("swarm.system_prompt_tokens")
    call = Call(
        component=f"agent calls ({label})",
        system="typed-multi-agent-swarm",
        count=calls_per_task,
        input_tokens=payload * (1 - out_share) / calls_per_task + system_prompt,
        output_tokens=payload * out_share / calls_per_task,
        tier=tier,
        cacheable=False,
        basis=(f"{key}.calls", f"{key}.tokens", "swarm.output_share", "swarm.system_prompt_tokens"),
    )
    return TaskSpec(
        id="coding-task",
        title=f"Coding task ({label})",
        summary="A programming task through the supervisor, researcher, coder, sandboxed executor and reviewers.",
        systems=("typed-multi-agent-swarm", "inter-agent-security-proxy", "raw-mcp-tool-server"),
        calls=(call,),
        latency=(
            LatencyItem(label="proxy screening per hand-off (hashing)", system="inter-agent-security-proxy",
                        measurement="proxy.screen_hashing_short_p50_ms", ms=v("proxy.screen_hashing_short_p50_ms")),
            LatencyItem(label="MCP tools/call round trip", system="raw-mcp-tool-server",
                        measurement="mcp.calculate_p50_ms", ms=v("mcp.calculate_p50_ms")),
            LatencyItem(label="MCP run_python sandbox", system="raw-mcp-tool-server",
                        measurement="mcp.run_python_p50_ms", ms=v("mcp.run_python_p50_ms")),
        ),
        success_rate=v(f"{key}.success"),
        notes=(
            "Calls and payload tokens are the swarm's offline measurements with simulated agent competence; the "
            "success rate is measured by running the accepted code against hidden tests.",
            "Swarm agents call models at temperature 0.2 and every task is different, so no cache hit is assumed.",
        ),
    )


def expected_executions(steps: int, crash_probability: float, durable: bool) -> list[float]:
    """Expected executions of each of ``steps`` sequential steps when each attempt crashes with probability p.

    Durable (journal + checkpoints): only the interrupted step is repeated, so each step runs 1 / (1 - p) times.
    Restart from scratch: a run attempt reaches step j with probability q^(j-1) and the number of attempts is
    geometric with success probability q^S, so step j runs q^(j-1) / q^S times (q = 1 - p).
    """
    if steps < 1:
        raise ValueError("steps must be >= 1")
    if not 0 <= crash_probability < 1:
        raise ValueError("crash_probability must be in [0, 1)")
    q = 1 - crash_probability
    if durable:
        return [1 / q] * steps
    return [q ** (j - 1) / q**steps for j in range(1, steps + 1)]


#: The research workflow's states in execution order, with the index of the LLM-calling ones.
RESEARCH_STEPS: tuple[str, ...] = ("plan", "gather", "draft", "approval", "publish")


def research_workflow(inputs: CostInputs, crash_probability: float = 0.0, durable: bool = True) -> TaskSpec:
    """The durable runtime's research workflow: plan (LLM), gather, draft (LLM), human approval, publish."""
    v = inputs.value
    per_step = expected_executions(len(RESEARCH_STEPS), crash_probability, durable)
    executions = dict(zip(RESEARCH_STEPS, per_step, strict=True))
    calls = (
        Call(component="plan", system="durable-agent-state-machine", count=executions["plan"],
             input_tokens=v("research.plan_input_tokens"), output_tokens=v("research.plan_output_tokens"),
             tier="medium", cacheable=False, basis=("research.plan_input_tokens", "research.plan_output_tokens")),
        Call(component="draft", system="durable-agent-state-machine", count=executions["draft"],
             input_tokens=v("research.draft_input_tokens"), output_tokens=v("research.draft_output_tokens"),
             tier="large", cacheable=False,
             basis=("research.draft_input_tokens", "research.draft_output_tokens")),
    )
    mode = "durable" if durable else "restart from scratch"
    return TaskSpec(
        id="research-workflow",
        title=f"Research workflow ({mode}, crash p={crash_probability:g})",
        summary="Plan, gather sources (GraphRAG local search, no LLM offline), draft, wait for approval, publish once.",
        systems=("durable-agent-state-machine", "graphrag-knowledge-pipeline", "context-assembler-engine",
                 "inter-agent-security-proxy"),
        calls=calls,
        latency=(
            LatencyItem(label="one durable step (SQLite WAL, checkpoint every transition)",
                        system="durable-agent-state-machine", measurement="durable.step_overhead_ms",
                        ms=v("durable.step_overhead_ms")),
        ),
        notes=(
            "The crash model assumes every step attempt crashes independently with the same probability and that a "
            "crash wastes the tokens of the interrupted attempt.",
            "In the chaos benchmark, 200 kills over 756 runs caused 89 re-run attempts and no completed step ran "
            "twice.",
        ),
    )


def pr_gate(inputs: CostInputs, llm_judge: bool = False) -> TaskSpec:
    """One pull request through the trajectory gate: candidate runs plus the amortised baseline."""
    v = inputs.value
    llm_calls = v("trajectory.run.llm_calls")
    per_call_in = v("trajectory.run.tokens_in") / llm_calls
    per_call_out = v("trajectory.run.tokens_out") / llm_calls
    candidate_runs = v("gate.cases") * v("gate.candidate_runs_per_case")
    baseline_runs = v("gate.cases") * v("gate.baseline_runs_per_case") / v("gate.prs_per_baseline")
    run_basis = ("trajectory.run.llm_calls", "trajectory.run.tokens_in", "trajectory.run.tokens_out", "gate.cases")
    calls = [
        Call(component="agent runs, candidate", system="trajectory-eval-gate", count=candidate_runs * llm_calls,
             input_tokens=per_call_in, output_tokens=per_call_out, tier="routed", cacheable=False,
             basis=(*run_basis, "gate.candidate_runs_per_case")),
        Call(component="agent runs, baseline (amortised)", system="trajectory-eval-gate",
             count=baseline_runs * llm_calls, input_tokens=per_call_in, output_tokens=per_call_out, tier="routed",
             cacheable=False, basis=(*run_basis, "gate.baseline_runs_per_case", "gate.prs_per_baseline")),
    ]
    if llm_judge:
        calls.append(
            Call(component="LLM judge", system="trajectory-eval-gate", count=candidate_runs + baseline_runs,
                 input_tokens=v("gate.judge_input_tokens"), output_tokens=v("gate.judge_output_tokens"),
                 tier="medium", cacheable=False,
                 basis=("gate.judge_input_tokens", "gate.judge_output_tokens", "gate.cases",
                        "gate.candidate_runs_per_case", "gate.baseline_runs_per_case", "gate.prs_per_baseline")))
    return TaskSpec(
        id="pr-gate",
        title=f"Pull-request gate ({'LLM judge' if llm_judge else 'offline judge'})",
        summary="Re-run the agent on every eval case, grade each run against its golden DAG, compare with the "
                "baseline.",
        systems=("trajectory-eval-gate",),
        calls=tuple(calls),
        latency=(
            LatencyItem(label="grade one trajectory", system="trajectory-eval-gate",
                        measurement="trajectory.grade_ms_mean", ms=v("trajectory.grade_ms_mean")),
        ),
        notes=(
            "Eval runs must bypass the response cache: a temperature-0 cache would replay the baseline and hide both "
            "regressions and flakiness.",
            "Token counts are the scripted travel-desk agent's simulated usage, not a live model's.",
        ),
    )


# ------------------------------------------------------------------------------------------------ scenarios


def headline_scenarios(inputs: CostInputs) -> list[Scenario]:
    """The five task settings shown in the headline table."""
    support = support_answer(inputs)
    return [
        Scenario(id="support-as-composed", label="Support answer, cache bypassed (as composed)", task=support,
                 cache_hit_rate=0.0, router="logistic"),
        Scenario(id="support-cache-aligned", label="Support answer, cache aligned", task=support,
                 cache_hit_rate=inputs.value("gateway.support.hit_rate.exact_semantic"), router="logistic"),
        Scenario(id="coding-swarm", label="Coding task, 3 reviewers @ 0.8", task=coding_task(inputs),
                 cache_hit_rate=0.0, router="logistic"),
        Scenario(id="research-durable", label="Research workflow, durable", task=research_workflow(inputs),
                 cache_hit_rate=0.0, router="logistic"),
        Scenario(id="pr-gate", label="Pull-request gate, offline judge", task=pr_gate(inputs),
                 cache_hit_rate=0.0, router="logistic"),
    ]


def price_matrix(inputs: CostInputs, scenarios: Sequence[Scenario]) -> dict[str, dict[str, TaskCost]]:
    """``{scenario id: {price table id: cost}}``."""
    return {
        s.id: {
            t.id: estimate(s.task, Knobs(price_table=t.id, cache_hit_rate=s.cache_hit_rate, router=s.router), inputs)
            for t in inputs.price_tables
        }
        for s in scenarios
    }


def sweep_cache(inputs: CostInputs, table: str, hit_rates: Sequence[float],
                routers: Sequence[Router] = ROUTERS) -> dict[str, list[float]]:
    """USD per support answer over cache hit rates, one series per router."""
    task = support_answer(inputs)
    return {
        router: [estimate(task, Knobs(price_table=table, cache_hit_rate=h, router=router), inputs).usd
                 for h in hit_rates]
        for router in routers
    }


def sweep_reviewers(inputs: CostInputs, table: str, tier: Tier = "large") -> dict[str, dict[str, list[float]]]:
    """Per reviewer accuracy: USD per task and per correct solution for 1, 3 and 5 reviewers."""
    result: dict[str, dict[str, list[float]]] = {}
    for accuracy in REVIEWER_ACCURACIES:
        costs = [estimate(coding_task(inputs, n, accuracy, tier), Knobs(price_table=table), inputs)
                 for n in REVIEWER_COUNTS]
        result[f"{accuracy}"] = {
            "usd": [c.usd for c in costs],
            "usd_per_success": [c.usd_per_success or 0.0 for c in costs],
            "success_rate": [c.success_rate or 0.0 for c in costs],
        }
    return result


def baseline_topologies(inputs: CostInputs, table: str, tier: Tier = "large") -> dict[str, TaskCost]:
    """The swarm benchmark's single-coder and coder + executor topologies, priced the same way."""
    return {
        topology: estimate(coding_task(inputs, tier=tier, topology=topology), Knobs(price_table=table), inputs)
        for topology in ("single", "coder-executor")
    }


def sweep_crashes(inputs: CostInputs, table: str, probabilities: Sequence[float],
                  long_steps: int = 15) -> dict[str, list[float]]:
    """Expected cost multiplier of crashes, durable versus restart-from-scratch.

    Two workflows: the research workflow (five steps, LLM cost in plan and draft) and a longer workflow of
    ``long_steps`` equally expensive steps.
    """
    knobs = Knobs(price_table=table)
    base = estimate(research_workflow(inputs), knobs, inputs).usd
    series: dict[str, list[float]] = {"research, durable": [], "research, restart": [],
                                      f"{long_steps} steps, durable": [], f"{long_steps} steps, restart": []}
    for p in probabilities:
        series["research, durable"].append(estimate(research_workflow(inputs, p, True), knobs, inputs).usd / base)
        series["research, restart"].append(estimate(research_workflow(inputs, p, False), knobs, inputs).usd / base)
        series[f"{long_steps} steps, durable"].append(sum(expected_executions(long_steps, p, True)) / long_steps)
        series[f"{long_steps} steps, restart"].append(sum(expected_executions(long_steps, p, False)) / long_steps)
    return series
