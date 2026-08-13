markdown# 
# System 1 → System 2 Architecture Robustness Test

## Purpose

This experiment evaluates the structural viability of the
System 1 → System 2 architecture.

It does not estimate production performance or select a production
threshold.

The experiment tests whether a viable quality/cost operating region
remains when S1 error, S2 error, S1 coverage, and S2/S1 relative cost
are varied.

## Method

System 1 handles accepted queries.

System 2 handles delegated queries. Delegation is normal System 2
processing, not a routing failure.

Overall error:

    Overall Error =
        S1 Coverage × S1 Error
        + S2 Delegation × S2 Error

Hybrid normalized cost:

    Hybrid Cost =
        S1 Coverage
        + S2 Delegation × (S2/S1 Cost)

Cost saving:

    Saving =
        1 - Hybrid Cost / (S2/S1 Cost)

The robustness scan varies:

- S1 error: 5–25%
- S2 error: 0–15%
- S1 scaling: 0.75–2.00x
- S2/S1 cost: 2–50x
- Router operating points: measured structural router curve

## Results

### Quality robustness

Best achievable overall error across the tested structural operating
points:

| S1 \ S2 | 0% | 1% | 2% | 5% | 10% | 15% |
|---:|---:|---:|---:|---:|---:|---:|
| 5%  | 1.40% | 2.12% | 2.84% | 5.00% | 5.30% | 5.59% |
| 10% | 2.80% | 3.52% | 4.24% | 6.40% | 10.00% | 10.30% |
| 15% | 4.20% | 4.92% | 5.64% | 7.80% | 11.40% | 15.00% |
| 20% | 5.60% | 6.32% | 7.04% | 9.20% | 12.80% | 16.40% |
| 25% | 7.00% | 7.72% | 8.44% | 10.60% | 14.20% | 17.80% |

### Cost robustness

| S2/S1 Cost | Saving |
|---:|---:|
| 2x  | 47.05% |
| 5x  | 75.28% |
| 10x | 84.69% |
| 20x | 89.39% |
| 50x | 92.22% |

### Quality-constrained robustness

Under an overall-error constraint of 5%, feasible operating points
remain even when S1 error is scaled to 2.00x, provided S2 error is 5%.

At that point:

- S1 coverage: 38.80%
- S2 delegation: 61.20%
- Overall error: 4.86%

Under a 10% overall-error constraint, feasible regions remain across
the full tested S1 scaling range and S2 error through 10%.

## Conclusion

The tested System 1 → System 2 architecture retains a non-trivial
quality/cost feasibility region across a broad range of S1 error,
S2 error, and relative cost assumptions.

The experiment therefore supports the structural viability of the
architecture.

No production accuracy, production cost, or production threshold is
claimed by this experiment.



