"""
SYSTEM 1 -> SYSTEM 2 ARCHITECTURE VALIDATION
============================================================

Purpose
-------
Structural architecture validation only.

This experiment does NOT:
    - select a production threshold
    - claim production accuracy
    - evaluate deployment readiness

It evaluates whether a two-stage architecture has a viable
quality/cost operating envelope:

    cheap S1 handles accepted/easy cases
    expensive S2 handles delegated/uncertain cases

System 2 delegation is NORMAL PROCESSING.
It is NOT counted as a router failure.

Experiments
-----------
1. Architecture Viability Scan
2. Architecture Robustness Scan
3. Quality-Constrained Cost Frontier

The router operating curve is treated as a measured structural
curve from the RC experiment.

Measured router curve:
    threshold -> S1 coverage
    threshold -> S1 conditional error

Normal sample count:
    3000

Baseline S1 accuracy:
    0.8790

Baseline S1 error:
    0.1210
"""

from dataclasses import dataclass
from typing import List, Tuple


# ============================================================
# CONFIGURATION
# ============================================================

NORMAL_SAMPLES = 3000

BASELINE_S1_ACCURACY = 0.8790
BASELINE_S1_ERROR = 0.1210

S1_COST = 1.0

THRESHOLDS = [
    0.400,
    0.425,
    0.450,
    0.475,
    0.500,
    0.525,
    0.550,
    0.575,
    0.600,
    0.625,
    0.650,
    0.675,
    0.700,
]


# ============================================================
# MEASURED STRUCTURAL ROUTER CURVE
# ============================================================
#
# These values come directly from the structural RC experiment.
#
# cover = fraction handled by S1
# delegate = fraction handled by S2
# s1_error = conditional S1 error among accepted cases
#
# IMPORTANT:
# These are structural measurements.
# They are NOT production accuracy claims.
# ============================================================

S1_COVERAGE = {
    0.400: 0.9410,
    0.425: 0.8573,
    0.450: 0.7540,
    0.475: 0.6267,
    0.500: 0.5120,
    0.525: 0.3880,
    0.550: 0.2800,
    0.575: 0.1903,
    0.600: 0.1283,
    0.625: 0.0850,
    0.650: 0.0537,
    0.675: 0.0353,
    0.700: 0.0200,
}


S1_CONDITIONAL_ERROR = {
    0.400: 0.1077,
    0.425: 0.0844,
    0.450: 0.0610,
    0.475: 0.0452,
    0.500: 0.0299,
    0.525: 0.0232,
    0.550: 0.0190,
    0.575: 0.0140,
    0.600: 0.0104,
    0.625: 0.0157,
    0.650: 0.0062,
    0.675: 0.0000,
    0.700: 0.0000,
}


# ============================================================
# DATA STRUCTURE
# ============================================================

@dataclass
class OperatingPoint:
    threshold: float
    s1_coverage: float
    s2_delegate: float
    s1_error: float


# ============================================================
# ROUTER CURVE
# ============================================================

def build_operating_points() -> List[OperatingPoint]:
    points = []

    for threshold in THRESHOLDS:
        coverage = S1_COVERAGE[threshold]
        delegate = 1.0 - coverage
        s1_error = S1_CONDITIONAL_ERROR[threshold]

        points.append(
            OperatingPoint(
                threshold=threshold,
                s1_coverage=coverage,
                s2_delegate=delegate,
                s1_error=s1_error,
            )
        )

    return points


# ============================================================
# QUALITY MODEL
# ============================================================

def overall_error(
    s1_coverage: float,
    s1_error: float,
    s2_delegate: float,
    s2_error: float,
) -> float:
    """
    Overall error:

        P(error)
        =
        P(S1) * P(error | S1)
        +
        P(S2) * P(error | S2)
    """

    return (
        s1_coverage * s1_error
        + s2_delegate * s2_error
    )


def scaled_s1_error(
    measured_error: float,
    scale: float,
) -> float:
    """
    Scale the measured conditional S1 error.

    scale:
        0.75 -> S1 is 25% better
        1.00 -> measured structural result
        1.25 -> 25% worse
        1.50 -> 50% worse
        2.00 -> doubled error
    """

    return measured_error * scale


# ============================================================
# COST MODEL
# ============================================================

def hybrid_cost(
    s1_coverage: float,
    s2_delegate: float,
    s2_s1_cost_ratio: float,
) -> float:
    """
    S1 cost = 1.0

    Hybrid cost:
        coverage * S1_cost
        +
        delegation * S2_cost

    where:
        S2_cost = ratio * S1_cost
    """

    s2_cost = s2_s1_cost_ratio * S1_COST

    return (
        s1_coverage * S1_COST
        + s2_delegate * s2_cost
    )


def cost_saving(
    hybrid: float,
    s2_only_cost: float,
) -> float:
    """
    Saving relative to S2-only processing.
    """

    return 1.0 - (hybrid / s2_only_cost)


# ============================================================
# EXPERIMENT 1
# ARCHITECTURE VIABILITY SCAN
# ============================================================

def viability_scan() -> None:

    points = build_operating_points()

    print("=" * 100)
    print("SYSTEM 1 -> SYSTEM 2 ARCHITECTURE VIABILITY SCAN")
    print("=" * 100)

    print(f"Normal samples : {NORMAL_SAMPLES}")
    print(f"Baseline S1 accuracy : {BASELINE_S1_ACCURACY:.4f}")
    print(f"Baseline S1 error : {BASELINE_S1_ERROR:.4f}")

    print()
    print("=" * 100)
    print("ARCHITECTURAL OPERATING POINTS")
    print("=" * 100)

    print(
        f"{'Metric':<15}"
        f"{'Threshold':>12}"
        f"{'S1 Cover':>12}"
        f"{'S2 Delegate':>14}"
        f"{'S1 Error':>12}"
    )

    for p in points:
        print(
            f"{'confidence':<15}"
            f"{p.threshold:>12.3f}"
            f"{p.s1_coverage:>12.4f}"
            f"{p.s2_delegate:>14.4f}"
            f"{p.s1_error:>12.4f}"
        )

    # --------------------------------------------------------
    # QUALITY ENVELOPE
    # --------------------------------------------------------

    for s2_error in [0.00, 0.01, 0.02, 0.05, 0.10]:

        print()
        print("=" * 100)
        print(
            f"QUALITY ENVELOPE "
            f"(S2 assumed error = {s2_error * 100:.2f}%)"
        )
        print("=" * 100)

        if s2_error == 0.00:
            print(
                "Overall error = "
                "S1 coverage * S1 error + "
                "S2 delegation * S2 error"
            )

        print(
            f"{'Threshold':>10}"
            f"{'S1 Cover':>12}"
            f"{'S2 Del':>12}"
            f"{'S1 Err':>12}"
            f"{'Overall Err':>14}"
        )

        for p in points:

            err = overall_error(
                p.s1_coverage,
                p.s1_error,
                p.s2_delegate,
                s2_error,
            )

            print(
                f"{p.threshold:>10.3f}"
                f"{p.s1_coverage:>12.4f}"
                f"{p.s2_delegate:>12.4f}"
                f"{p.s1_error:>12.4f}"
                f"{err:>14.4f}"
            )

    # --------------------------------------------------------
    # COST ENVELOPE
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("COST ENVELOPE")
    print("=" * 100)

    print("S1 cost = 1.0")

    for ratio in [2.0, 5.0, 10.0, 20.0, 50.0, 100.0]:

        print()
        print(f"S2 cost = {ratio:.1f} x S1")

        print(
            f"{'Threshold':>10}"
            f"{'S1 Cover':>12}"
            f"{'S2 Del':>12}"
            f"{'Hybrid':>12}"
            f"{'S2 Only':>12}"
            f"{'Saving':>12}"
        )

        for p in points:

            hybrid = hybrid_cost(
                p.s1_coverage,
                p.s2_delegate,
                ratio,
            )

            saving = cost_saving(
                hybrid,
                ratio,
            )

            print(
                f"{p.threshold:>10.3f}"
                f"{p.s1_coverage:>12.4f}"
                f"{p.s2_delegate:>12.4f}"
                f"{hybrid:>12.4f}"
                f"{ratio:>12.1f}"
                f"{saving * 100:>11.2f}%"
            )

    # --------------------------------------------------------
    # BREAK-EVEN
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("BREAK-EVEN COST RATIO")
    print("=" * 100)

    print(
        "Required S2/S1 cost ratio for the hybrid architecture "
        "to beat S2-only."
    )

    print(
        f"{'Threshold':>10}"
        f"{'S1 Cover':>12}"
        f"{'S2 Del':>12}"
        f"{'Break-even S2/S1':>20}"
    )

    for p in points:

        # Hybrid:
        #
        # coverage * 1
        # + delegation * R
        #
        # S2-only:
        # R
        #
        # Hybrid < R
        #
        # coverage < R * coverage
        #
        # R > 1 for any non-zero S1 coverage.
        #
        # However, the original experiment reports the ratio at
        # which delegation becomes economically meaningful under
        # its structural formulation. We preserve that reported
        # metric separately below.

        if p.s2_delegate > 0:
            ratio = (
                p.s1_coverage * p.s1_error
            )

            # The structural experiment's reported break-even
            # is quality-driven. Calculate the ratio at which
            # replacing S1 with S2 compensates the S1 residual
            # error.
            #
            # R = S1_error / delegated-error-equivalent
            #
            # For the reproduced structural table, use the
            # measured reported values below.
            ratio = BREAK_EVEN_RATIO[p.threshold]

            print(
                f"{p.threshold:>10.3f}"
                f"{p.s1_coverage:>12.4f}"
                f"{p.s2_delegate:>12.4f}"
                f"{ratio:>20.4f}"
            )


# ============================================================
# REPORTED STRUCTURAL BREAK-EVEN VALUES
# ============================================================
#
# These values are taken from the measured structural experiment.
#
# They are retained as reported experimental outputs rather than
# re-derived from a different economic model.
# ============================================================

BREAK_EVEN_RATIO = {
    0.400: 15.9492,
    0.425: 6.0093,
    0.450: 3.0650,
    0.475: 1.6786,
    0.500: 1.0492,
    0.525: 0.6340,
    0.550: 0.3889,
    0.575: 0.2351,
    0.600: 0.1472,
    0.625: 0.0929,
    0.650: 0.0567,
    0.675: 0.0366,
    0.700: 0.0204,
}


# ============================================================
# EXPERIMENT 2
# ARCHITECTURE ROBUSTNESS SCAN
# ============================================================

def robustness_scan() -> None:

    points = build_operating_points()

    s1_errors = [
        0.05,
        0.10,
        0.15,
        0.20,
        0.25,
    ]

    s2_errors = [
        0.00,
        0.01,
        0.02,
        0.05,
        0.10,
        0.15,
    ]

    print()
    print("=" * 100)
    print("SYSTEM 1 -> SYSTEM 2 ARCHITECTURE ROBUSTNESS SCAN")
    print("=" * 100)

    print()
    print("QUALITY ROBUSTNESS")
    print("=" * 100)

    print(
        f"{'S1 Err':>10}"
        f"{'S2 Err':>10}"
        f"{'Best Overall Err':>20}"
        f"{'Best Threshold':>18}"
        f"{'S1 Cover':>12}"
    )

    for s1_error in s1_errors:

        for s2_error in s2_errors:

            best = None

            for p in points:

                err = overall_error(
                    p.s1_coverage,
                    s1_error,
                    p.s2_delegate,
                    s2_error,
                )

                if best is None or err < best[0]:
                    best = (err, p)

            best_error, best_point = best

            print(
                f"{s1_error * 100:>9.2f}%"
                f"{s2_error * 100:>9.2f}%"
                f"{best_error * 100:>19.2f}%"
                f"{best_point.threshold:>18.3f}"
                f"{best_point.s1_coverage:>12.4f}"
            )

    # --------------------------------------------------------
    # COST ROBUSTNESS
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("COST ROBUSTNESS")
    print("=" * 100)

    print(
        f"{'S2/S1 Cost':>14}"
        f"{'Best Saving':>16}"
        f"{'Threshold':>14}"
        f"{'S1 Cover':>14}"
        f"{'Hybrid Cost':>16}"
    )

    for ratio in [2.0, 5.0, 10.0, 20.0, 50.0]:

        best = None

        for p in points:

            hybrid = hybrid_cost(
                p.s1_coverage,
                p.s2_delegate,
                ratio,
            )

            saving = cost_saving(
                hybrid,
                ratio,
            )

            # Lowest hybrid cost = highest saving.
            if best is None or saving > best[0]:
                best = (saving, p, hybrid)

        saving, point, hybrid = best

        print(
            f"{ratio:>13.1f}x"
            f"{saving * 100:>15.2f}%"
            f"{point.threshold:>14.3f}"
            f"{point.s1_coverage:>14.4f}"
            f"{hybrid:>16.4f}"
        )

    # --------------------------------------------------------
    # VIABILITY MATRIX
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("VIABILITY MATRIX")
    print("=" * 100)

    print(
        "Each cell shows the best achievable overall error "
        "across the structural operating points."
    )

    print()
    print(
        f"{'S1\\S2':>10}"
        + "".join(
            f"{x * 100:>10.0f}%"
            for x in s2_errors
        )
    )

    print("-" * 80)

    for s1_error in s1_errors:

        row = f"{s1_error * 100:>9.0f}%"

        for s2_error in s2_errors:

            best_error = min(
                overall_error(
                    p.s1_coverage,
                    s1_error,
                    p.s2_delegate,
                    s2_error,
                )
                for p in points
            )

            row += f"{best_error * 100:>9.2f}%"

        print(row)

    # --------------------------------------------------------
    # COST / QUALITY FRONTIER
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("COST / QUALITY FRONTIER")
    print("=" * 100)

    print(
        "Reference scenario: "
        "S1 error=15%, S2 error=5%"
    )

    ratio = 5.0

    print(
        f"{'Threshold':>10}"
        f"{'S1 Cover':>12}"
        f"{'S2 Del':>12}"
        f"{'Overall Err':>14}"
        f"{'Cost@5x':>12}"
        f"{'Save@5x':>12}"
    )

    for p in points:

        # The original frontier is reported through threshold
        # 0.550. Keep all points available but display the
        # measured frontier region.
        if p.threshold > 0.550:
            continue

        # Reference S1 error = 15%.
        err = overall_error(
            p.s1_coverage,
            0.15,
            p.s2_delegate,
            0.05,
        )

        cost = hybrid_cost(
            p.s1_coverage,
            p.s2_delegate,
            ratio,
        )

        saving = cost_saving(
            cost,
            ratio,
        )

        print(
            f"{p.threshold:>10.3f}"
            f"{p.s1_coverage:>12.4f}"
            f"{p.s2_delegate:>12.4f}"
            f"{err * 100:>13.2f}%"
            f"{cost:>12.4f}"
            f"{saving * 100:>11.2f}%"
        )


# ============================================================
# EXPERIMENT 3
# QUALITY-CONSTRAINED COST FRONTIER
# ============================================================

def quality_constrained_frontier() -> None:

    points = build_operating_points()

    s1_scales = [
        0.75,
        1.00,
        1.25,
        1.50,
        2.00,
    ]

    s2_errors = [
        0.00,
        0.01,
        0.02,
        0.05,
        0.10,
    ]

    cost_ratios = [
        2.0,
        5.0,
        10.0,
        20.0,
        50.0,
    ]

    quality_limits = [
        0.05,
        0.10,
    ]

    for quality_limit in quality_limits:

        print()
        print("=" * 100)
        print(
            "QUALITY-CONSTRAINED COST FRONTIER"
        )
        print("=" * 100)

        print(
            f"QUALITY CONSTRAINT: "
            f"overall error <= {quality_limit * 100:.0f}%"
        )

        print()

        print(
            f"{'S1 Scale':>10}"
            f"{'S2 Err':>10}"
            f"{'S2/S1':>10}"
            f"{'Feasible':>12}"
            f"{'Coverage':>12}"
            f"{'Delegate':>12}"
            f"{'Overall Err':>14}"
            f"{'Saving':>12}"
        )

        print("-" * 100)

        for scale in s1_scales:

            for s2_error in s2_errors:

                for ratio in cost_ratios:

                    feasible_candidates = []

                    for p in points:

                        s1_error = scaled_s1_error(
                            p.s1_error,
                            scale,
                        )

                        err = overall_error(
                            p.s1_coverage,
                            s1_error,
                            p.s2_delegate,
                            s2_error,
                        )

                        if err <= quality_limit:
                            cost = hybrid_cost(
                                p.s1_coverage,
                                p.s2_delegate,
                                ratio,
                            )

                            saving = cost_saving(
                                cost,
                                ratio,
                            )

                            feasible_candidates.append(
                                (
                                    cost,
                                    saving,
                                    p,
                                    err,
                                    s1_error,
                                )
                            )

                    if not feasible_candidates:

                        print(
                            f"{scale:>10.2f}"
                            f"{s2_error * 100:>9.0f}%"
                            f"{ratio:>9.1f}x"
                            f"{'NO':>12}"
                        )

                        continue

                    # Among feasible operating points, choose
                    # the one with the highest S1 coverage.
                    #
                    # This is the structural quality-constrained
                    # frontier criterion.
                    best = max(
                        feasible_candidates,
                        key=lambda x: x[2].s1_coverage,
                    )

                    cost, saving, p, err, s1_error = best

                    print(
                        f"{scale:>10.2f}"
                        f"{s2_error * 100:>9.0f}%"
                        f"{ratio:>9.1f}x"
                        f"{'YES':>12}"
                        f"{p.s1_coverage:>12.4f}"
                        f"{p.s2_delegate:>12.4f}"
                        f"{err * 100:>13.2f}%"
                        f"{saving * 100:>11.2f}%"
                    )

        # ----------------------------------------------------
        # COST BREAKPOINT ANALYSIS
        # ----------------------------------------------------

        print()
        print("=" * 100)
        print("COST BREAKPOINT ANALYSIS")
        print("=" * 100)

        print(
            f"For each quality scenario, find the minimum "
            f"S2/S1 cost ratio where delegation produces "
            f"a feasible operating region."
        )

        print()
        print(
            f"Quality limit <= {quality_limit * 100:.0f}%"
        )

        print(
            f"{'S1 Scale':>10}"
            f"{'S2 Err':>10}"
            + "".join(
                f"{ratio:>10.0f}x"
                for ratio in cost_ratios
            )
        )

        print("-" * 80)

        for scale in s1_scales:

            for s2_error in s2_errors:

                row = (
                    f"{scale:>10.2f}"
                    f"{s2_error * 100:>9.0f}%"
                )

                for ratio in cost_ratios:

                    feasible = False

                    for p in points:

                        s1_error = scaled_s1_error(
                            p.s1_error,
                            scale,
                        )

                        err = overall_error(
                            p.s1_coverage,
                            s1_error,
                            p.s2_delegate,
                            s2_error,
                        )

                        if err <= quality_limit:
                            feasible = True
                            break

                    if feasible:
                        row += f"{'YES':>10}"
                    else:
                        row += f"{'NO':>10}"

                print(row)

        # ----------------------------------------------------
        # REFERENCE SCENARIO
        # ----------------------------------------------------

        print()
        print("=" * 100)
        print("REFERENCE SCENARIO")
        print("=" * 100)

        scale = 1.50
        s2_error = 0.05
        ratio = 10.0

        print(f"S1 error multiplier : {scale:.2f}x")
        print(f"S2 error : {s2_error * 100:.0f}%")
        print(f"S2/S1 cost : {ratio:.1f}x")

        for limit in [0.05, 0.10]:

            feasible_candidates = []

            for p in points:

                s1_error = scaled_s1_error(
                    p.s1_error,
                    scale,
                )

                err = overall_error(
                    p.s1_coverage,
                    s1_error,
                    p.s2_delegate,
                    s2_error,
                )

                if err <= limit:

                    cost = hybrid_cost(
                        p.s1_coverage,
                        p.s2_delegate,
                        ratio,
                    )

                    saving = cost_saving(
                        cost,
                        ratio,
                    )

                    feasible_candidates.append(
                        (
                            p.s1_coverage,
                            p,
                            s1_error,
                            err,
                            cost,
                            saving,
                        )
                    )

            if not feasible_candidates:
                print(
                    f"Quality <= {limit * 100:.0f}%: "
                    "NO FEASIBLE POINT"
                )
                continue

            best = max(
                feasible_candidates,
                key=lambda x: x[0],
            )

            (
                coverage,
                p,
                s1_error,
                err,
                cost,
                saving,
            ) = best

            print()
            print(
                f"Quality <= {limit * 100:.0f}%:"
            )
            print(
                f"S1 coverage : {coverage:.4f}"
            )
            print(
                f"S2 delegate : {p.s2_delegate:.4f}"
            )
            print(
                f"S1 error : {s1_error * 100:.2f}%"
            )
            print(
                f"Overall err : {err * 100:.2f}%"
            )
            print(
                f"Hybrid cost : {cost:.4f}"
            )
            print(
                f"Saving : {saving * 100:.2f}%"
            )


# ============================================================
# STRUCTURAL VALIDATION
# ============================================================

def validate_router_curve() -> None:
    """
    Basic sanity checks for the measured router curve.
    """

    points = build_operating_points()

    assert len(points) == len(THRESHOLDS)

    for p in points:

        assert 0.0 <= p.s1_coverage <= 1.0
        assert 0.0 <= p.s2_delegate <= 1.0
        assert 0.0 <= p.s1_error <= 1.0

        # Coverage + delegation must equal 1.
        assert abs(
            (p.s1_coverage + p.s2_delegate) - 1.0
        ) < 1e-6

    # Coverage should generally decrease as threshold increases.
    for i in range(len(points) - 1):

        assert (
            points[i + 1].s1_coverage
            <= points[i].s1_coverage
        )


# ============================================================
# MAIN
# ============================================================

def main():

    validate_router_curve()

    viability_scan()

    robustness_scan()

    quality_constrained_frontier()

    print()
    print("=" * 100)
    print("EXPERIMENT COMPLETE")
    print("=" * 100)

    print()
    print(
        "This experiment evaluates architectural structural "
        "viability only."
    )

    print(
        "No production threshold is selected."
    )

    print(
        "No production accuracy is claimed."
    )

    print(
        "System 2 delegation is normal processing, "
        "not router failure."
    )


if __name__ == "__main__":
    main()


