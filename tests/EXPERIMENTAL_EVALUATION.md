System 1 → System 2 Architecture Viability Experiment
Overview

This repository contains a structural validation experiment for a two-stage inference architecture:

                    ┌──────────────┐
Input ─────────────►│   System 1   │
                    │ cheap / fast │
                    └──────┬───────┘
                           │
                    confidence gate
                           │
                 ┌─────────┴─────────┐
                 │                   │
              accepted            delegated
                 │                   │
                 ▼                   ▼
             S1 result         ┌──────────────┐
                                │   System 2   │
                                │ expensive    │
                                │ / stronger   │
                                └──────┬───────┘
                                       │
                                       ▼
                                   S2 result

The purpose of this experiment is not to select a production threshold or predict production performance.

The purpose is to determine whether the architecture has a structurally viable operating region in which:

inexpensive S1 handles sufficiently many easy cases,
uncertain cases are delegated to S2,
overall quality remains within a specified constraint,
and the hybrid system can reduce cost relative to running S2 on every sample.

System 2 delegation is considered normal processing, not a router failure.

Experimental Principle

The architecture is evaluated using a measured S1 operating curve.

For each confidence threshold, the experiment records:

S1 coverage
S2 delegation rate
conditional S1 error

The overall error is then modeled as:

E
overall
	​

=C
S1
	​

E
S1
	​

+D
S2
	​

E
S2
	​


where:

C
S1
	​

 = fraction processed by S1
D
S2
	​

 = fraction delegated to S2
E
S1
	​

 = conditional error of S1
E
S2
	​

 = assumed error of S2

The cost model is:

Cost
hybrid
	​

=C
S1
	​

C
S1
cost
	​

+D
S2
	​

C
S2
cost
	​


with:

C
S1
cost
	​

=1

and S2 cost expressed as a multiple of S1 cost.

Experimental Scope
Included

The experiment evaluates:

S1 → S2 delegation behavior
quality envelope
cost envelope
break-even S2/S1 cost ratio
robustness to S1 degradation
robustness to non-zero S2 error
quality-constrained cost frontier
Explicitly excluded

This experiment does not attempt to determine:

production threshold
production accuracy
production latency
production reliability
real-world user behavior
production traffic distribution
operational monitoring requirements
deployment configuration

The measured RC is treated as a structural probe, not as a production-performance estimate.

Dataset / Baseline

Normal samples:

3000

S1-only baseline:

Accuracy : 87.90%
Error    : 12.10%

This baseline is used as the reference point for the architecture experiments.

S1 Operating Curve

The measured structural operating points are:

Threshold	S1 Coverage	S2 Delegation	S1 Error
0.400	94.10%	5.90%	10.77%
0.425	85.73%	14.27%	8.44%
0.450	75.40%	24.60%	6.10%
0.475	62.67%	37.33%	4.52%
0.500	51.20%	48.80%	2.99%
0.525	38.80%	61.20%	2.32%
0.550	28.00%	72.00%	1.90%
0.575	19.03%	80.97%	1.40%
0.600	12.83%	87.17%	1.04%
0.625	8.50%	91.50%	1.57%
0.650	5.37%	94.63%	0.62%
0.675	3.53%	96.47%	0.00%
0.700	2.00%	98.00%	0.00%

This curve is the structural input to the subsequent robustness experiments.

Quality Envelope

The experiment evaluates multiple assumed S2 error levels:

0%
1%
2%
5%
10%

The important observation is that the architecture does not depend on an idealized perfect S2.

For example, with S2 error = 5%, several operating points remain below 5% overall error.

Representative results:

Threshold	S1 Coverage	S2 Delegation	Overall Error
0.475	62.67%	37.33%	4.70%
0.500	51.20%	48.80%	3.97%
0.525	38.80%	61.20%	3.96%
0.550	28.00%	72.00%	4.13%

This demonstrates a non-empty quality-feasible region under a non-zero S2 error assumption.

Cost Model

S1 cost is normalized to:

S1 cost = 1.0

S2 is evaluated at:

2x
5x
10x
20x
50x
100x

relative to S1.

The hybrid cost is:

C
hybrid
	​

=C
S1
	​

+D
S2
	​

(R−1)

where R is the S2/S1 cost ratio.

S2-only cost is simply:

C
S2−only
	​

=R
Cost Results

At threshold 0.400, where S1 covers 94.10% of samples:

S2/S1 Cost	Hybrid Cost	Saving
2×	1.059	47.05%
5×	1.236	75.28%
10×	1.531	84.69%
20×	2.121	89.39%
50×	3.891	92.22%
100×	6.841	93.16%

The cost advantage increases as S2 becomes more expensive.

Break-even Analysis

The minimum S2/S1 cost ratio required for the hybrid architecture to outperform S2-only depends strongly on S1 coverage.

Threshold	S1 Coverage	Break-even Ratio
0.400	94.10%	15.95×
0.425	85.73%	6.01×
0.450	75.40%	3.07×
0.475	62.67%	1.68×
0.500	51.20%	1.05×
0.525	38.80%	0.63×
0.550	28.00%	0.39×
0.575	19.03%	0.24×
0.600	12.83%	0.15×

This illustrates the fundamental economic trade-off of the architecture.

Higher S1 coverage provides greater cost savings, but places more responsibility on S1.

Robustness Experiment

The architecture was tested against degraded S1 and S2 assumptions.

S1 error was scaled by:

0.75x
1.00x
1.25x
1.50x
2.00x

S2 error was varied over:

0%
1%
2%
5%
10%
15%

Two quality constraints were evaluated:

overall error <= 5%
overall error <= 10%
Viability Matrix

The best achievable overall error across the structural operating points was:

S1 Error	S2 0%	S2 1%	S2 2%	S2 5%	S2 10%	S2 15%
5%	1.40%	2.12%	2.84%	5.00%	5.30%	5.59%
10%	2.80%	3.52%	4.24%	6.40%	10.00%	10.30%
15%	4.20%	4.92%	5.64%	7.80%	11.40%	15.00%
20%	5.60%	6.32%	7.04%	9.20%	12.80%	16.40%
25%	7.00%	7.72%	8.44%	10.60%	14.20%	17.80%

The matrix shows that the architecture retains a meaningful feasible region across a range of degraded assumptions, but eventually becomes infeasible when both S1 and S2 quality deteriorate sufficiently.

Reference Scenario

The primary reference scenario used in the quality-constrained frontier analysis is:

S1 error multiplier : 1.50x
S2 error            : 5%
S2/S1 cost          : 10x
Quality constraint: ≤ 5%

Result:

S1 coverage       : 51.20%
S2 delegation     : 48.80%
S1 conditional err: 4.49%
Overall error     : 4.74%
Hybrid cost       : 5.392
Saving            : 46.08%
Quality constraint: ≤ 10%

Result:

S1 coverage       : 75.40%
S2 delegation     : 24.60%
S1 conditional err: 9.15%
Overall error     : 8.13%
Hybrid cost       : 3.214
Saving            : 67.86%

This reference scenario demonstrates the central architecture trade-off:

Stricter quality
       ↓
more S2 delegation
       ↓
lower S1 coverage
       ↓
higher cost

Conversely:

Relaxed quality
       ↓
less S2 delegation
       ↓
higher S1 coverage
       ↓
lower cost
Main Findings
Finding 1 — A structural operating curve exists

The confidence gate produces a controllable transition between S1-heavy and S2-heavy operation.

This provides the fundamental mechanism required for a two-stage architecture.

Finding 2 — The architecture does not require a perfect S2

Useful quality regions remain under non-zero S2 error assumptions.

Therefore the structural argument does not depend on treating S2 as an ideal oracle.

Finding 3 — The architecture tolerates S1 degradation within a range

Even after scaling S1 error above the measured value, feasible operating points remain under both 5% and 10% quality constraints for a meaningful subset of assumptions.

Finding 4 — Cost advantage increases with S2 cost

When S2 becomes substantially more expensive than S1, selective delegation produces increasingly large savings relative to S2-only processing.

Finding 5 — Quality and cost form a frontier

There is no single universally optimal threshold in this experiment.

Instead, different quality constraints correspond to different S1 coverage / S2 delegation / cost operating points.

Interpretation

The experiment supports the following architectural hypothesis:

A cheap first-stage system can handle sufficiently easy cases while a more capable second-stage system handles uncertain cases, producing a viable quality/cost envelope under a meaningful range of assumptions.

The experiment does not establish:

"Threshold X should be used in production."

Nor does it establish a production accuracy estimate.

The threshold values are structural operating points extracted from the experimental RC.

Limitations

The current experiment intentionally leaves several production questions outside its scope.

1. No production calibration

Confidence values are used as the routing signal, but production calibration of confidence is not evaluated.

2. No production distribution claim

The experiment uses the experimental sample distribution and does not claim that production traffic will have the same distribution.

3. No production accuracy claim

The measured S1 results are used as structural inputs.

They should not be interpreted as production accuracy predictions.

4. S2 error is modeled

Several S2 error rates are assumed rather than established as a production benchmark.

5. Cost is normalized

S1 cost = 1.0 and S2 cost ratios are structural parameters, not measured infrastructure costs.

6. Threshold selection is intentionally deferred

The experiment demonstrates the existence of operating regions.

It does not select a production operating point.

Final Conclusion

The experiments provide evidence that the System 1 → System 2 architecture is structurally viable.

The strongest evidence is the simultaneous existence of:

a measurable S1/S2 delegation curve,
quality-feasible operating regions,
robustness to degraded S1 and non-zero S2 error,
substantial cost savings relative to S2-only processing.

The architecture therefore passes the intended structural viability test.

The next stage should be treated separately from this experiment:

production validation is a future experiment, not a conclusion of this one.

Repository Structure

The final repository should contain the experiment artifacts in approximately the following form:

.
├── README.md
├── code/
│   └── ...
├── results/
│   ├── architecture_viability.txt
│   ├── architecture_robustness.txt
│   └── quality_constrained_cost_frontier.txt
└── ...

The exact filenames can be adjusted when the code is consolidated.


