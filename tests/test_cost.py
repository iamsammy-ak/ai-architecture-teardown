from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from teardown import cost
from teardown.cost import Knobs


def test_routing_mixes_are_distributions(inputs) -> None:
    for router in cost.ROUTERS:
        mix = cost.routing_mix(inputs, router)
        assert sum(mix.values()) == pytest.approx(1.0)
        assert all(0 <= v <= 1 for v in mix.values())
    logistic = cost.routing_mix(inputs, "logistic")
    assert logistic["small"] == pytest.approx(1790 / 3000)
    assert logistic["large"] == pytest.approx(385 / 3000)


def test_support_answer_matches_a_hand_calculation(inputs) -> None:
    task = cost.support_answer(inputs)
    priced = cost.estimate(task, Knobs(price_table="gateway-illustrative", router="all-large"), inputs)
    generation = next(line for line in priced.lines if line.component == "grounded generation")
    assert generation.usd == pytest.approx((3072 * 3.0 + 250 * 15.0) / 1e6)
    rewrite = next(line for line in priced.lines if line.component == "query rewrite")
    assert rewrite.calls == pytest.approx(29 / 69, rel=1e-4)
    memory = next(line for line in priced.lines if line.component.startswith("memory"))
    assert memory.tier == "small"
    assert memory.calls == pytest.approx(2 / (7568 / 500 / 2))


@settings(max_examples=40, deadline=None)
@given(h=st.floats(min_value=0, max_value=1))
def test_cache_only_discounts_cacheable_calls(inputs, h: float) -> None:
    task = cost.support_answer(inputs)
    cold = cost.estimate(task, Knobs(price_table="gateway-illustrative"), inputs)
    warm = cost.estimate(task, Knobs(price_table="gateway-illustrative", cache_hit_rate=h), inputs)
    for c, w, call in zip(cold.lines, warm.lines, task.calls, strict=True):
        expected = c.usd * (1 - h) if call.cacheable else c.usd
        assert w.usd == pytest.approx(expected, abs=1e-15)
        assert w.input_tokens == pytest.approx(w.billed_calls * call.input_tokens)


def test_flat_price_table_makes_routing_irrelevant(inputs) -> None:
    task = cost.support_answer(inputs)
    values = {cost.estimate(task, Knobs(price_table="trajectory-flat", router=r), inputs).usd for r in cost.ROUTERS}
    assert max(values) == pytest.approx(min(values))


def test_cheaper_routing_never_costs_more_on_the_illustrative_table(inputs) -> None:
    task = cost.support_answer(inputs)
    usd = {r: cost.estimate(task, Knobs(price_table="gateway-illustrative", router=r), inputs).usd
           for r in cost.ROUTERS}
    assert usd["all-small"] < usd["logistic"] < usd["rules"] < usd["all-large"]


def test_coding_task_uses_measured_calls_and_success(inputs) -> None:
    task = cost.coding_task(inputs, reviewers=3, accuracy=0.8)
    call = task.calls[0]
    assert call.count == pytest.approx(9.0967)
    total_payload = call.count * (call.input_tokens - 800) + call.count * call.output_tokens
    assert total_payload == pytest.approx(5287)
    assert task.success_rate == pytest.approx(0.9433)
    priced = cost.estimate(task, Knobs(price_table="gateway-illustrative"), inputs)
    assert priced.usd_per_success == pytest.approx(priced.usd / 0.9433)


@pytest.mark.parametrize("reviewers,accuracy", [(2, 0.8), (3, 0.75), (0, 0.8)])
def test_coding_task_refuses_unmeasured_configurations(inputs, reviewers: int, accuracy: float) -> None:
    with pytest.raises(ValueError):
        cost.coding_task(inputs, reviewers=reviewers, accuracy=accuracy)


def test_coding_baseline_topologies(inputs) -> None:
    single = cost.coding_task(inputs, topology="single")
    assert single.success_rate == pytest.approx(0.62)
    assert single.calls[0].count == pytest.approx(2.165)


def test_more_reviewers_cost_more_per_task(inputs) -> None:
    sweep = cost.sweep_reviewers(inputs, "gateway-illustrative")
    for values in sweep.values():
        assert values["usd"] == sorted(values["usd"])
        assert all(s > 0 for s in values["success_rate"])


@pytest.mark.parametrize("steps", [1, 2, 5, 15])
@pytest.mark.parametrize("p", [0.0, 0.05, 0.3])
def test_expected_executions_closed_forms(steps: int, p: float) -> None:
    durable = cost.expected_executions(steps, p, durable=True)
    restart = cost.expected_executions(steps, p, durable=False)
    assert all(x == pytest.approx(1 / (1 - p)) for x in durable)
    expected_total = steps if p == 0 else ((1 - p) ** -steps - 1) / p
    assert sum(restart) == pytest.approx(expected_total)
    assert sum(restart) >= sum(durable) - 1e-9


@given(steps=st.integers(min_value=1, max_value=30), p=st.floats(min_value=0, max_value=0.5))
def test_restarting_never_beats_resuming(steps: int, p: float) -> None:
    durable = cost.expected_executions(steps, p, durable=True)
    restart = cost.expected_executions(steps, p, durable=False)
    assert restart[0] >= restart[-1] - 1e-9  # earlier steps are repeated at least as often
    assert sum(restart) >= sum(durable) * (1 - 1e-9)


@pytest.mark.parametrize("steps,p", [(0, 0.1), (3, 1.0), (3, -0.1)])
def test_expected_executions_rejects_bad_arguments(steps: int, p: float) -> None:
    with pytest.raises(ValueError):
        cost.expected_executions(steps, p, durable=True)


def test_research_workflow_crash_sweep_is_monotone(inputs) -> None:
    series = cost.sweep_crashes(inputs, "gateway-illustrative", [0.0, 0.1, 0.2, 0.3])
    for values in series.values():
        assert values[0] == pytest.approx(1.0)
        assert values == sorted(values)
    assert series["research, restart"][-1] > series["research, durable"][-1]
    assert series["15 steps, restart"][-1] > series["research, restart"][-1]


def test_pr_gate_counts_candidate_and_amortised_baseline_runs(inputs) -> None:
    gate = cost.pr_gate(inputs)
    candidate, baseline = gate.calls
    llm_calls = inputs.value("trajectory.run.llm_calls")
    assert candidate.count == pytest.approx(15 * llm_calls)
    assert baseline.count == pytest.approx(100 / 20 * llm_calls)
    flat = cost.estimate(gate, Knobs(price_table="trajectory-flat"), inputs)
    per_run = (inputs.value("trajectory.run.tokens_in") * 0.5 + inputs.value("trajectory.run.tokens_out") * 1.5) / 1e6
    assert flat.usd == pytest.approx(20 * per_run)
    judged = cost.estimate(cost.pr_gate(inputs, llm_judge=True), Knobs(price_table="trajectory-flat"), inputs)
    assert judged.usd > flat.usd
    assert not any(call.cacheable for call in gate.calls)


def test_headline_scenarios_and_price_matrix(inputs) -> None:
    scenarios = cost.headline_scenarios(inputs)
    assert len({s.id for s in scenarios}) == 5
    matrix = cost.price_matrix(inputs, scenarios)
    for row in matrix.values():
        assert set(row) == {t.id for t in inputs.price_tables}
        assert all(c.usd > 0 for c in row.values())
    assert matrix["support-cache-aligned"]["gateway-illustrative"].usd < \
        matrix["support-as-composed"]["gateway-illustrative"].usd
    premium, base = (matrix["coding-swarm"]["scenario-premium-large"].usd,
                     matrix["coding-swarm"]["gateway-illustrative"].usd)
    assert premium == pytest.approx(5 * base)


def test_scenario_rejects_a_hit_rate_without_cacheable_calls(inputs) -> None:
    with pytest.raises(ValueError):
        cost.Scenario(id="x", label="x", task=cost.coding_task(inputs), cache_hit_rate=0.3, router="logistic")


def test_cache_sweep_shapes(inputs) -> None:
    sweep = cost.sweep_cache(inputs, "gateway-illustrative", [0.0, 0.5, 1.0])
    assert set(sweep) == set(cost.ROUTERS)
    for values in sweep.values():
        assert values[0] > values[1] > values[2] > 0  # memory consolidation is never cached
