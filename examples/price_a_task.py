"""Price two tasks with the cost model: the support answer at two cache hit rates, and a one-reviewer coding task.

    PYTHONPATH=src python examples/price_a_task.py
"""

from __future__ import annotations

from teardown.cost import Knobs, coding_task, estimate, support_answer
from teardown.inputs import load_inputs

inputs = load_inputs()  # bench/cost_inputs.yaml: measurements at pinned commits + stated assumptions

task = support_answer(inputs)
for hit_rate in (0.0, inputs.value("gateway.support.hit_rate.exact_semantic")):
    knobs = Knobs(price_table="gateway-illustrative", cache_hit_rate=hit_rate, router="logistic")
    print(f"support answer, cache hit rate {hit_rate:.0%}: ${1000 * estimate(task, knobs, inputs).usd:.2f} per 1,000")

swarm = estimate(coding_task(inputs, reviewers=1, accuracy=0.8), Knobs(price_table="gateway-illustrative"), inputs)
print(f"coding task, 1 reviewer @ 0.8: ${swarm.usd:.4f} per task, ${swarm.usd_per_success:.4f} per correct solution")
