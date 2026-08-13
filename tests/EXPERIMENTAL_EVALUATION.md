
# System 1 -> System 2 Architecture Robustness
# Experimental Evaluation

Status: Structural Architecture Validation
Scope: Architecture-level feasibility only
Production Performance Claim: None

================================================================================
1. PURPOSE
================================================================================

This experiment evaluates the structural viability of the proposed System 1
(S1) -> System 2 (S2) architecture.

The purpose of the experiment is NOT to establish a production accuracy
threshold, production cost estimate, or deployment-level performance claim.

Instead, the experiment asks a narrower architectural question:

    Does a useful quality/cost operating region remain available when the
    assumed error rates, S1 coverage, and relative S2 cost are varied?

System 1 handles accepted cases.

System 2 handles delegated cases.

Delegation to System 2 is NORMAL SYSTEM 2 PROCESSING. It is not treated as an
error, failure, fallback defect, or architectural exception.

The experiment therefore evaluates whether the architecture remains
structurally viable when:

    - S1 quality deteriorates,
    - S2 has non-zero error,
    - S1 coverage changes,
    - S2 becomes substantially more expensive than S1,
    - and an explicit overall-quality constraint is imposed.

All reported values are experimental structural results. They must not be
interpreted as production performance predictions.


================================================================================
2. EXPERIMENTAL MODEL
================================================================================

The architecture is modeled as a two-stage routing system.

    Input
      |
      v
    System 1
      |
      +---- Accepted by S1 --------------------> Output
      |
      +---- Delegated -------------------------> System 2
                                                     |
                                                     v
                                                   Output

Let:

    C1 = S1 coverage
    D  = S2 delegation rate
    E1 = S1 conditional error rate
    E2 = S2 conditional error rate

with:

    D = 1 - C1

The overall error is modeled as the coverage-weighted error:

    E_overall = C1 * E1 + D * E2

or equivalently:

    E_overall = C1 * E1 + (1 - C1) * E2

This formulation treats S2 delegation as ordinary processing and evaluates
the quality of the resulting routed system as a whole.

For cost analysis, the normalized cost of S1 is:

    Cost(S1) = 1

and the relative S2 cost is represented as:

    R = Cost(S2) / Cost(S1)

The normalized hybrid cost is therefore:

    Cost_hybrid = C1 + D * R

The normalized all-S2 reference cost is:

    Cost_all_S2 = R

The corresponding normalized saving is:

    Saving = 1 - Cost_hybrid / Cost_all_S2

which is equivalent to:

    Saving = 1 - (C1 + D * R) / R


================================================================================
3. EXPERIMENTAL PRINCIPLE
================================================================================

The router operating curve used in this evaluation is taken from the measured
structural experiment.

The experiment does not assume that one threshold is universally optimal.

Instead, thresholds are treated as operating points that determine the
trade-off between:

    - S1 coverage,
    - S2 delegation,
    - overall quality,
    - and hybrid compute cost.

The measured structural operating points include the following S1 coverage
levels:

    5%
    10%
    15%
    20%
    25%

The cost robustness experiment evaluates S2/S1 cost ratios of:

    2x
    5x
    10x
    20x
    50x

The quality robustness experiment varies S1 and S2 error independently.

The quality-constrained evaluation additionally scales the measured S1 error
using the following multipliers:

    0.75x  = S1 is 25% better than the measured structural result
    1.00x  = measured structural result
    1.25x  = S1 error is 25% worse
    1.50x  = S1 error is 50% worse
    2.00x  = S1 error is doubled

Again, these are stress-test assumptions and are not production estimates.


================================================================================
4. QUALITY ROBUSTNESS
================================================================================

The first experiment evaluates the effect of changing S1 and S2 conditional
error rates while allowing the router to select the best structural operating
point.

The following table reports the best achievable overall error for each
combination of S1 and S2 error.

The corresponding threshold and S1 coverage are also reported.

    S1 Err    S2 Err    Best Overall Err    Best Threshold    S1 Cover
    ------------------------------------------------------------------
     5.00%     0.00%          1.40%            0.550           28.00%
     5.00%     1.00%          2.12%            0.550           28.00%
     5.00%     2.00%          2.84%            0.550           28.00%
     5.00%     5.00%          5.00%            0.400           94.10%
     5.00%    10.00%          5.30%            0.400           94.10%
     5.00%    15.00%          5.59%            0.400           94.10%

    10.00%    0.00%          2.80%            0.550           28.00%
    10.00%    1.00%          3.52%            0.550           28.00%
    10.00%    2.00%          4.24%            0.550           28.00%
    10.00%    5.00%          6.40%            0.550           28.00%
    10.00%   10.00%         10.00%            0.400           94.10%
    10.00%   15.00%         10.30%            0.400           94.10%

    15.00%    0.00%          4.20%            0.550           28.00%
    15.00%    1.00%          4.92%            0.550           28.00%
    15.00%    2.00%          5.64%            0.550           28.00%
    15.00%    5.00%          7.80%            0.550           28.00%
    15.00%   10.00%         11.40%            0.550           28.00%
    15.00%   15.00%         15.00%            0.400           94.10%

    20.00%    0.00%          5.60%            0.550           28.00%
    20.00%    1.00%          6.32%            0.550           28.00%
    20.00%    2.00%          7.04%            0.550           28.00%
    20.00%    5.00%          9.20%            0.550           28.00%
    20.00%   10.00%         12.80%            0.550           28.00%
    20.00%   15.00%         16.40%            0.550           28.00%

    25.00%    0.00%          7.00%            0.550           28.00%
    25.00%    1.00%          7.72%            0.550           28.00%
    25.00%    2.00%          8.44%            0.550           28.00%
    25.00%    5.00%         10.60%            0.550           28.00%
    25.00%   10.00%         14.20%            0.550           28.00%
    25.00%   15.00%         17.80%            0.550           28.00%


The corresponding viability matrix is:

    S1\S2      0%       1%       2%       5%       10%      15%
    ----------------------------------------------------------------
     5%       1.40%    2.12%    2.84%    5.00%    5.30%     5.59%
    10%       2.80%    3.52%    4.24%    6.40%   10.00%    10.30%
    15%       4.20%    4.92%    5.64%    7.80%   11.40%    15.00%
    20%       5.60%    6.32%    7.04%    9.20%   12.80%    16.40%
    25%       7.00%    7.72%    8.44%   10.60%   14.20%    17.80%

The matrix demonstrates that the architecture retains a non-trivial quality
feasibility region under a range of S1/S2 error assumptions.

The experiment also shows the expected structural boundary: as both S1 and S2
errors increase, the achievable overall error eventually exceeds the quality
constraint regardless of the routing operating point.


================================================================================
5. COST ROBUSTNESS
================================================================================

The second experiment evaluates whether delegation remains economically useful
when System 2 becomes increasingly expensive relative to System 1.

The best cost operating point was consistently observed at:

    Threshold = 0.400
    S1 Coverage = 94.10%
    S2 Delegation = 5.90%

The normalized hybrid cost and saving are:

    S2/S1 Cost Ratio    Saving      Hybrid Cost
    ---------------------------------------------
          2x             47.05%       1.0590
          5x             75.28%       1.2360
         10x             84.69%       1.5310
         20x             89.39%       2.1210
         50x             92.22%       3.8910

The result is structurally important because increasing the relative cost of
System 2 does not eliminate the economic value of routing.

Instead, when the router can keep most traffic on S1 and delegate only a small
fraction to S2, the relative saving increases as S2 becomes more expensive.

This result should not be interpreted as a prediction of a particular monetary
saving in production. The costs are normalized relative costs used to test the
architecture's economic structure.


================================================================================
6. COST / QUALITY FRONTIER
================================================================================

A representative stress scenario was evaluated using:

    S1 Error = 15%
    S2 Error = 5%

The following operating points illustrate the quality/cost frontier.

    Threshold    S1 Cover    S2 Delegate    Overall Err    Cost@5x    Saving@5x
    ---------------------------------------------------------------------------
     0.400        0.9410        0.0590         14.41%       1.2360      75.28%
     0.425        0.8573        0.1427         13.57%       1.5708      68.58%
     0.450        0.7540        0.2460         12.54%       1.9840      60.32%
     0.475        0.6267        0.3733         11.27%       2.4932      50.14%
     0.500        0.5120        0.4880         10.12%       2.9520      40.96%
     0.525        0.3880        0.6120          8.88%       3.4480      31.04%
     0.550        0.2800        0.7200          7.80%       3.8800      22.40%

This frontier demonstrates the basic architectural trade-off.

Increasing the threshold causes:

    - S1 coverage to decrease,
    - S2 delegation to increase,
    - overall quality to improve,
    - and hybrid cost to increase.

Therefore, the router exposes a continuous structural trade-off rather than a
single universally optimal point.

The appropriate operating point is consequently dependent on the desired
quality/cost constraint.


================================================================================
7. QUALITY-CONSTRAINED COST FRONTIER
================================================================================

A second experiment explicitly imposes quality constraints.

Two quality limits were evaluated:

    Constraint A:
        Overall Error <= 5%

    Constraint B:
        Overall Error <= 10%

The experiment varies:

    - S1 error scale,
    - S2 error,
    - S2/S1 cost ratio,
    - router operating point.

The purpose is to determine whether feasible regions survive under degraded
assumptions.

--------------------------------------------------------------------------------
7.1 QUALITY LIMIT: OVERALL ERROR <= 5%
--------------------------------------------------------------------------------

S1 error scale:

    0.75x = 25% better than measured S1 error
    1.00x = measured structural S1 error
    1.25x = 25% worse
    1.50x = 50% worse
    2.00x = doubled S1 error

Representative feasible operating points are summarized below.

    S1 Scale    S2 Err    S1 Coverage    S2 Delegate    Overall Err
    ----------------------------------------------------------------
      0.75        0%         75.40%         24.60%          3.45%
      0.75        1%         75.40%         24.60%          3.70%
      0.75        2%         75.40%         24.60%          3.94%
      0.75        5%         75.40%         24.60%          4.68%
      0.75       10%           NO FEASIBLE OPERATING POINT

      1.00        0%         75.40%         24.60%          4.60%
      1.00        1%         75.40%         24.60%          4.85%
      1.00        2%         62.67%         37.33%          3.58%
      1.00        5%         62.67%         37.33%          4.70%
      1.00       10%           NO FEASIBLE OPERATING POINT

      1.25        0%         62.67%         37.33%          3.54%
      1.25        1%         62.67%         37.33%          3.91%
      1.25        2%         62.67%         37.33%          4.29%
      1.25        5%         51.20%         48.80%          4.35%
      1.25       10%           NO FEASIBLE OPERATING POINT

      1.50        0%         62.67%         37.33%          4.25%
      1.50        1%         62.67%         37.33%          4.62%
      1.50        2%         62.67%         37.33%          5.00%
      1.50        5%         51.20%         48.80%          4.74%
      1.50       10%           NO FEASIBLE OPERATING POINT

      2.00        0%         51.20%         48.80%          3.06%
      2.00        1%         51.20%         48.80%          3.55%
      2.00        2%         51.20%         48.80%          4.04%
      2.00        5%         38.80%         61.20%          4.86%
      2.00       10%           NO FEASIBLE OPERATING POINT

The corresponding cost savings across relative S2/S1 cost ratios are:

    S1 Scale   S2 Err     2x      5x      10x     20x     50x
    ----------------------------------------------------------------
     0.75       0%       38%     60%      68%     72%     74%
     0.75       1%       38%     60%      68%     72%     74%
     0.75       2%       38%     60%      68%     72%     74%
     0.75       5%       38%     60%      68%     72%     74%

     1.00       0%       38%     60%      68%     72%     74%
     1.00       1%       38%     60%      68%     72%     74%
     1.00       2%       31%     50%      56%     60%     61%
     1.00       5%       31%     50%      56%     60%     61%

     1.25       0%       31%     50%      56%     60%     61%
     1.25       1%       31%     50%      56%     60%     61%
     1.25       2%       31%     50%      56%     60%     61%
     1.25       5%       26%     41%      46%     49%     50%

     1.50       0%       31%     50%      56%     60%     61%
     1.50       1%       31%     50%      56%     60%     61%
     1.50       2%       31%     50%      56%     60%     61%
     1.50       5%       26%     41%      46%     49%     50%

     2.00       0%       26%     41%      46%     49%     50%
     2.00       1%       26%     41%      46%     49%     50%
     2.00       2%       26%     41%      46%     49%     50%
     2.00       5%       19%     31%      35%     37%     38%

The important result is not any single percentage.

The structural result is that the <=5% quality constraint remains feasible even
under substantial degradation of S1, provided that S2 quality and the routing
operating point remain sufficiently favorable.

The feasible region contracts as S1 and S2 errors increase, but it does not
immediately disappear.


--------------------------------------------------------------------------------
7.2 QUALITY LIMIT: OVERALL ERROR <= 10%
--------------------------------------------------------------------------------

The <=10% constraint produces a substantially wider feasible region.

Representative results:

    S1 Scale    S2 Err    S1 Coverage    S2 Delegate    Overall Err
    ----------------------------------------------------------------
      0.75        0%         94.10%          5.90%          7.60%
      0.75        1%         94.10%          5.90%          7.66%
      0.75        2%         94.10%          5.90%          7.72%
      0.75        5%         94.10%          5.90%          7.90%
      0.75       10%         94.10%          5.90%          8.19%

      1.00        0%         85.73%         14.27%          7.24%
      1.00        1%         85.73%         14.27%          7.38%
      1.00        2%         85.73%         14.27%          7.52%
      1.00        5%         85.73%         14.27%          7.95%
      1.00       10%         85.73%         14.27%          8.66%

      1.25        0%         85.73%         14.27%          9.04%
      1.25        1%         85.73%         14.27%          9.19%
      1.25        2%         85.73%         14.27%          9.33%
      1.25        5%         85.73%         14.27%          9.76%
      1.25       10%         75.40%         24.60%          8.21%

      1.50        0%         75.40%         24.60%          6.90%
      1.50        1%         75.40%         24.60%          7.15%
      1.50        2%         75.40%         24.60%          7.39%
      1.50        5%         75.40%         24.60%          8.13%
      1.50       10%         75.40%         24.60%          9.36%

      2.00        0%         75.40%         24.60%          9.20%
      2.00        1%         75.40%         24.60%          9.44%
      2.00        2%         75.40%         24.60%          9.69%
      2.00        5%         62.67%         37.33%          7.53%
      2.00       10%         62.67%         37.33%          9.40%

Unlike the <=5% constraint, all tested S1/S2 combinations in the <=10%
experiment retain at least one feasible structural operating point.

The corresponding savings remain substantial across the tested S2/S1 cost
ratios.

    S1 Scale   S2 Err     2x      5x      10x     20x     50x
    ----------------------------------------------------------------
     0.75       0%       47%     75%      85%     89%     92%
     0.75       1%       47%     75%      85%     89%     92%
     0.75       2%       47%     75%      85%     89%     92%
     0.75       5%       47%     75%      85%     89%     92%
     0.75      10%       47%     75%      85%     89%     92%

     1.00       0%       43%     69%      77%     81%     84%
     1.00       1%       43%     69%      77%     81%     84%
     1.00       2%       43%     69%      77%     81%     84%
     1.00       5%       43%     69%      77%     81%     84%
     1.00      10%       43%     69%      77%     81%     84%

     1.25       0%       43%     69%      77%     81%     84%
     1.25       1%       43%     69%      77%     81%     84%
     1.25       2%       43%     69%      77%     81%     84%
     1.25       5%       43%     69%      77%     81%     84%
     1.25      10%       38%     60%      68%     72%     74%

     1.50       0%       38%     60%      68%     72%     74%
     1.50       1%       38%     60%      68%     72%     74%
     1.50       2%       38%     60%      68%     72%     74%
     1.50       5%       38%     60%      68%     72%     74%
     1.50      10%       38%     60%      68%     72%     74%

     2.00       0%       38%     60%      68%     72%     74%
     2.00       1%       38%     60%      68%     72%     74%
     2.00       2%       38%     60%      68%     72%     74%
     2.00       5%       31%     50%      56%     60%     61%
     2.00      10%       31%     50%      56%     60%     61%


================================================================================
8. COST BREAKPOINT ANALYSIS
================================================================================

The purpose of the breakpoint analysis is to determine whether delegation
remains economically meaningful at different relative S2/S1 costs.

The experiment reports the resulting savings for each tested cost ratio.

A saving is considered structurally meaningful when the hybrid architecture
cost is below the all-S2 reference cost.

--------------------------------------------------------------------------------
8.1 QUALITY LIMIT <= 5%
--------------------------------------------------------------------------------

    S1 Scale    S2 Err     2x      5x      10x     20x     50x
    ----------------------------------------------------------------
     0.75        0%       38%     60%      68%     72%     74%
     0.75        1%       38%     60%      68%     72%     74%
     0.75        2%       38%     60%      68%     72%     74%
     0.75        5%       38%     60%      68%     72%     74%
     0.75       10%       NO      NO       NO      NO      NO

     1.00        0%       38%     60%      68%     72%     74%
     1.00        1%       38%     60%      68%     72%     74%
     1.00        2%       31%     50%      56%     60%     61%
     1.00        5%       31%     50%      56%     60%     61%
     1.00       10%       NO      NO       NO      NO      NO

     1.25        0%       31%     50%      56%     60%     61%
     1.25        1%       31%     50%      56%     60%     61%
     1.25        2%       31%     50%      56%     60%     61%
     1.25        5%       26%     41%      46%     49%     50%
     1.25       10%       NO      NO       NO      NO      NO

     1.50        0%       31%     50%      56%     60%     61%
     1.50        1%       31%     50%      56%     60%     61%
     1.50        2%       31%     50%      56%     60%     61%
     1.50        5%       26%     41%      46%     49%     50%
     1.50       10%       NO      NO       NO      NO      NO

     2.00        0%       26%     41%      46%     49%     50%
     2.00        1%       26%     41%      46%     49%     50%
     2.00        2%       26%     41%      46%     49%     50%
     2.00        5%       19%     31%      35%     37%     38%
     2.00       10%       NO      NO       NO      NO      NO


--------------------------------------------------------------------------------
8.2 QUALITY LIMIT <= 10%
--------------------------------------------------------------------------------

    S1 Scale    S2 Err     2x      5x      10x     20x     50x
    ----------------------------------------------------------------
     0.75        0%       47%     75%      85%     89%     92%
     0.75        1%       47%     75%      85%     89%     92%
     0.75        2%       47%     75%      85%     89%     92%
     0.75        5%       47%     75%      85%     89%     92%
     0.75       10%       47%     75%      85%     89%     92%

     1.00        0%       43%     69%      77%     81%     84%
     1.00        1%       43%     69%      77%     81%     84%
     1.00        2%       43%     69%      77%     81%     84%
     1.00        5%       43%     69%      77%     81%     84%
     1.00       10%       43%     69%      77%     81%     84%

     1.25        0%       43%     69%      77%     81%     84%
     1.25        1%       43%     69%      77%     81%     84%
     1.25        2%       43%     69%      77%     81%     84%
     1.25        5%       43%     69%      77%     81%     84%
     1.25       10%       38%     60%      68%     72%     74%

     1.50        0%       38%     60%      68%     72%     74%
     1.50        1%       38%     60%      68%     72%     74%
     1.50        2%       38%     60%      68%     72%     74%
     1.50        5%       38%     60%      68%     72%     74%
     1.50       10%       38%     60%      68%     72%     74%

     2.00        0%       38%     60%      68%     72%     74%
     2.00        1%       38%     60%      68%     72%     74%
     2.00        2%       38%     60%      68%     72%     74%
     2.00        5%       31%     50%      56%     60%     61%
     2.00       10%       31%     50%      56%     60%     61%


================================================================================
9. REFERENCE SCENARIO
================================================================================

A representative reference scenario was defined as:

    S1 Error Multiplier = 1.50x
    S2 Error            = 5%
    S2/S1 Cost Ratio    = 10x

The results under the two quality constraints are:

--------------------------------------------------------------------------------
QUALITY CONSTRAINT: OVERALL ERROR <= 5%
--------------------------------------------------------------------------------

    S1 Coverage       = 51.20%
    S2 Delegation     = 48.80%
    S1 Error          = 4.49%
    Overall Error     = 4.74%
    Hybrid Cost       = 5.3920
    Saving            = 46.08%

This operating point satisfies the <=5% overall-error constraint while retaining
more than half of the traffic on S1.

--------------------------------------------------------------------------------
QUALITY CONSTRAINT: OVERALL ERROR <= 10%
--------------------------------------------------------------------------------

    S1 Coverage       = 75.40%
    S2 Delegation     = 24.60%
    S1 Error          = 9.15%
    Overall Error     = 8.13%
    Hybrid Cost       = 3.2140
    Saving            = 67.86%

This operating point satisfies the <=10% overall-error constraint while
retaining 75.40% S1 coverage.


================================================================================
10. STRUCTURAL FINDINGS
================================================================================

The experiments support several architectural observations.

10.1 The architecture has a non-zero feasibility envelope.

The viability matrix does not collapse immediately when S1 or S2 error is
increased.

Instead, the feasible region gradually contracts as the conditional error
rates deteriorate.

This is the expected behavior of a robust two-stage architecture.

10.2 S2 delegation can compensate for degraded S1 quality.

When S1 quality becomes insufficient for a strict overall-quality constraint,
increasing delegation to S2 can restore feasibility.

This is visible in the <=5% experiments, where progressively worse S1
conditions lead to lower S1 coverage and greater S2 delegation.

The architecture therefore provides a structural mechanism for trading
coverage against quality.

10.3 The architecture does not require S1 to solve every case.

A central structural property of the design is that S1 is not required to
achieve the target quality independently on every input.

Instead:

    S1 handles the cases it can handle efficiently.
    S2 handles delegated cases.

This separation is fundamental to the architecture.

10.4 Delegation is not treated as a failure.

S2 processing is a normal component of the architecture.

Consequently, a high delegation rate is not automatically evidence of a
failed router.

The relevant questions are:

    - Is the resulting overall quality acceptable?
    - Is the resulting cost acceptable?
    - Does the architecture retain a useful operating region?

10.5 Cost leverage increases with S2/S1 cost asymmetry.

Across the tested cost ratios, the economic advantage increases as S2 becomes
more expensive relative to S1.

For example, under the cost-robustness operating point:

    2x  -> 47.05% saving
    5x  -> 75.28% saving
    10x -> 84.69% saving
    20x -> 89.39% saving
    50x -> 92.22% saving

This is a structural property of selective delegation, not a production cost
forecast.

10.6 Quality constraints determine the usable operating region.

The <=5% constraint is substantially more restrictive than the <=10%
constraint.

Under the <=10% constraint, all tested combinations retained a feasible
operating point.

Under the <=5% constraint, feasibility disappeared for the tested cases where
S2 error reached 10%.

This identifies a meaningful structural boundary in the tested parameter
space.


================================================================================
11. WHAT THIS EXPERIMENT DOES NOT ESTABLISH
================================================================================

This experiment does NOT establish:

    - production accuracy,
    - production cost,
    - production latency,
    - real-world customer quality,
    - deployment readiness,
    - a universally optimal router threshold,
    - a guaranteed percentage cost reduction,
    - or superiority over a specific production routing system.

The reported threshold values are experimental operating points.

The reported coverage values are structural measurements from the experiment.

The reported cost ratios are normalized assumptions.

The reported error rates are controlled experimental assumptions.

The results should therefore be interpreted as evidence concerning the
architecture's structural feasibility envelope only.


================================================================================
12. INTERPRETATION OF ROBUSTNESS
================================================================================

For this experiment, robustness means that useful operating regions survive
under meaningful perturbations of the model assumptions.

The architecture is considered structurally promising when:

    1. S1 quality can deteriorate without immediately eliminating feasibility.
    2. S2 can have non-zero error while useful quality constraints remain
       achievable.
    3. S1 coverage can remain substantial while meeting quality constraints.
    4. The economic advantage persists across a range of S2/S1 cost ratios.
    5. The quality/cost trade-off remains continuous rather than collapsing to
       a single fragile operating point.

The experiment demonstrates all five properties within the tested parameter
range, subject to the limitations described above.

This does not mean that the architecture is proven universally robust.

It means that the tested structural operating envelope contains meaningful
feasible regions rather than requiring a single idealized parameter setting.


================================================================================
13. EXPERIMENTAL CONCLUSION
================================================================================

The System 1 -> System 2 architecture demonstrates a meaningful structural
viability envelope across the tested quality and cost assumptions.

The most important result is not a single threshold, coverage value, or
savings percentage.

The important result is that the architecture continues to provide feasible
quality/cost operating points when:

    - S1 error is degraded,
    - S2 has non-zero error,
    - S1 coverage changes,
    - S2 becomes substantially more expensive,
    - and explicit overall-quality constraints are imposed.

Under the tested <=5% overall-error constraint, feasible regions remain
available for a substantial portion of the tested parameter space, including
cases where S1 performance is degraded by up to 2x, provided that S2 quality
and delegation are sufficiently favorable.

Under the <=10% overall-error constraint, the feasible region is substantially
larger, with all tested S1/S2 error combinations retaining a feasible
operating point.

The economic experiment likewise shows that selective S2 delegation retains
strong structural cost leverage when S2 is more expensive than S1.

At a 10x S2/S1 cost ratio, the measured structural savings reached:

    84.69%  at the cost-robustness operating point.

In the representative stressed scenario with:

    S1 Error Multiplier = 1.50x
    S2 Error            = 5%
    S2/S1 Cost Ratio    = 10x

the architecture achieved:

    Overall Error = 4.74%
    S1 Coverage   = 51.20%
    S2 Delegation = 48.80%
    Saving        = 46.08%

under the <=5% quality constraint.

Under the <=10% constraint, the same stress assumptions produced:

    Overall Error = 8.13%
    S1 Coverage   = 75.40%
    S2 Delegation = 24.60%
    Saving        = 67.86%

These results support the architectural hypothesis that a selective
System 1 -> System 2 routing design can preserve a useful quality/cost
operating region under non-ideal assumptions.

Again, this is a structural architecture result.

It is not a production-performance claim.


================================================================================
14. REPRODUCIBILITY AND ARTIFACTS
================================================================================

This document records the experimental assumptions, mathematical model,
operating points, robustness results, and interpretation.

The corresponding implementation should be stored separately as the
experiment source code.

Recommended artifact structure:

    EXPERIMENTAL_EVALUATION.md
        |
        +-- architecture_robustness_experiment.py
        |
        +-- [optional generated result files]
        |
        +-- [optional raw experiment data]

The experiment code should reproduce the numerical tables in this document
without requiring any production deployment environment.

The experiment should remain deterministic wherever possible, and all
structural assumptions should be explicitly represented in the code rather
than hidden in undocumented constants.


================================================================================
15. FINAL STATUS
================================================================================

Experiment Type:
    Structural Architecture Robustness Validation

Production Evaluation:
    Not performed

Production Threshold Selection:
    Not performed

Primary Question:
    Whether the S1 -> S2 architecture retains a useful quality/cost
    feasibility envelope under varied structural assumptions.

Result:
    YES, within the tested parameter range.

Interpretation:
    The architecture demonstrates structural viability, with feasible
    quality/cost regions surviving substantial variation in S1 quality,
    S2 quality, S1 coverage, and S2/S1 relative cost.

Final qualification:

    These results validate structural feasibility of the tested architecture.
    They do not constitute a production-performance prediction or deployment
    recommendation.

