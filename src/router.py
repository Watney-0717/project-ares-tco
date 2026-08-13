# Copyright 2026 Watney-0717
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Project Ares-TCO: Reservoir Computing Router Core.

This module implements the System 1 routing layer of Project Ares-TCO.

The router maps semantic embedding vectors into a fixed, high-dimensional
reservoir representation and trains only a linear readout layer. The resulting
readout scores are converted into route probabilities and can be used for
confidence-gated delegation to a System 2 fallback.

The implementation supports:

    * fixed input projection;
    * fixed sparse recurrent reservoir;
    * leaky recurrent state transformation;
    * ridge-regression readout training;
    * numerically stable Softmax probabilities;
    * confidence-gated routing;
    * online Recursive Least Squares (RLS) adaptation;
    * hot addition of new routing lanes;
    * deterministic reservoir initialization;
    * diagnostic inspection of reservoir parameters.

Experimental scope
-------------------

This module is an architectural experiment implementation.

It does NOT establish:

    * production routing accuracy;
    * production latency;
    * production cost reduction;
    * calibrated probability estimates;
    * an optimal fallback threshold;
    * production reliability;
    * production scalability.

In particular, ``fallback_threshold`` is an externally supplied operating
parameter. Its numerical value must be evaluated empirically and must not be
interpreted as a validated production threshold.

Reservoir state semantics
-------------------------

Each embedding is processed independently from a zero initial reservoir
state. The ``iterations`` parameter therefore performs a fixed number of
recurrent state transitions for a single embedding; it does not provide
cross-query temporal memory.

Consequently, this implementation should be interpreted as a static semantic
routing transformation rather than a stateful sequence-processing reservoir.
"""

from __future__ import annotations

from typing import Optional

import numpy as np


class RCRouter:
    """Reservoir Computing Router acting as System 1.

    Architecture
    ------------

        Input embedding
              |
              v
        Fixed input projection
              |
              v
        Fixed recurrent reservoir
              |
              v
        Trainable linear readout
              |
              v
        Routing scores
              |
              v
        Numerically stable Softmax
              |
              +---- confidence >= threshold ---> System 1 route
              |
              +---- confidence < threshold ----> System 2

    Only the readout layer is trainable. The input projection and recurrent
    reservoir remain fixed after initialization.

    Parameters
    ----------
    input_dim:
        Dimensionality of the incoming embedding vector.

    reservoir_dim:
        Number of recurrent reservoir units.

    output_dim:
        Number of routing lanes/backends initially available.

    spectral_radius:
        Target spectral radius of the recurrent reservoir matrix.

    leak_rate:
        Leaky integration coefficient in the interval (0, 1].

    sparsity:
        Fraction of recurrent connections that are non-zero.

    ridge:
        Positive regularization coefficient.

    seed:
        Random seed used for deterministic reservoir initialization.

    iterations:
        Number of recurrent state transitions performed for each embedding.

    fallback_threshold:
        Confidence threshold used by ``route()`` for System 2 delegation.

        This is an experimental operating parameter and is not a learned
        or production-validated quantity.

    use_bias:
        Whether to include a trainable intercept term in the readout.

    Notes
    -----
    The router does not maintain reservoir state between separate calls to
    ``_state()``. Every embedding begins from a zero state.
    """

    def __init__(
        self,
        input_dim: int = 384,
        reservoir_dim: int = 300,
        output_dim: int = 4,
        spectral_radius: float = 0.9,
        leak_rate: float = 0.5,
        sparsity: float = 0.1,
        ridge: float = 1e-3,
        seed: Optional[int] = 42,
        iterations: int = 3,
        fallback_threshold: float = 0.65,
        use_bias: bool = True,
    ) -> None:

        # ==============================================================
        # Parameter validation
        # ==============================================================

        if (
            not isinstance(input_dim, (int, np.integer))
            or isinstance(input_dim, bool)
            or input_dim <= 0
        ):
            raise ValueError(
                "input_dim must be a positive integer."
            )

        if (
            not isinstance(reservoir_dim, (int, np.integer))
            or isinstance(reservoir_dim, bool)
            or reservoir_dim <= 0
        ):
            raise ValueError(
                "reservoir_dim must be a positive integer."
            )

        if (
            not isinstance(output_dim, (int, np.integer))
            or isinstance(output_dim, bool)
            or output_dim <= 0
        ):
            raise ValueError(
                "output_dim must be a positive integer."
            )

        if (
            not np.isfinite(spectral_radius)
            or spectral_radius < 0.0
        ):
            raise ValueError(
                "spectral_radius must be finite and non-negative."
            )

        if (
            not np.isfinite(leak_rate)
            or not 0.0 < leak_rate <= 1.0
        ):
            raise ValueError(
                "leak_rate must be in the range (0.0, 1.0]."
            )

        if (
            not np.isfinite(sparsity)
            or not 0.0 <= sparsity <= 1.0
        ):
            raise ValueError(
                "sparsity must be in the range [0.0, 1.0]."
            )

        if (
            not np.isfinite(ridge)
            or ridge <= 0.0
        ):
            raise ValueError(
                "ridge must be finite and strictly positive."
            )

        if (
            not isinstance(iterations, (int, np.integer))
            or isinstance(iterations, bool)
            or iterations <= 0
        ):
            raise ValueError(
                "iterations must be a positive integer."
            )

        if (
            not np.isfinite(fallback_threshold)
            or not 0.0 <= fallback_threshold <= 1.0
        ):
            raise ValueError(
                "fallback_threshold must be in the range [0.0, 1.0]."
            )

        if seed is not None:
            if (
                not isinstance(seed, (int, np.integer))
                or isinstance(seed, bool)
            ):
                raise ValueError(
                    "seed must be an integer or None."
                )

        # ==============================================================
        # Configuration
        # ==============================================================

        self.input_dim = int(input_dim)
        self.reservoir_dim = int(reservoir_dim)
        self.output_dim = int(output_dim)

        self.spectral_radius = float(spectral_radius)
        self.leak_rate = float(leak_rate)
        self.sparsity = float(sparsity)
        self.ridge = float(ridge)
        self.iterations = int(iterations)

        self.fallback_threshold = float(
            fallback_threshold
        )

        self.use_bias = bool(use_bias)
        self.seed = (
            None
            if seed is None
            else int(seed)
        )

        rng = np.random.default_rng(
            self.seed
        )

        # ==============================================================
        # Fixed input-to-reservoir projection
        # ==============================================================

        self.W_in = rng.uniform(
            -0.1,
            0.1,
            size=(
                self.reservoir_dim,
                self.input_dim,
            ),
        ).astype(
            np.float64
        )

        # ==============================================================
        # Fixed recurrent reservoir
        # ==============================================================

        W_res_raw = rng.uniform(
            -0.5,
            0.5,
            size=(
                self.reservoir_dim,
                self.reservoir_dim,
            ),
        ).astype(
            np.float64
        )

        # Apply sparsity mask.
        mask = (
            rng.random(
                size=W_res_raw.shape
            )
            < self.sparsity
        )

        W_res_raw *= mask

        if self.spectral_radius == 0.0:

            self.W_res = np.zeros_like(
                W_res_raw
            )

        else:

            rho = self._spectral_radius(
                W_res_raw
            )

            if (
                rho <= np.finfo(
                    np.float64
                ).eps
            ):
                raise ValueError(
                    "The generated reservoir has zero spectral radius. "
                    "Increase sparsity, reservoir_dim, or change the seed."
                )

            self.W_res = (
                W_res_raw
                * (
                    self.spectral_radius
                    / rho
                )
            ).astype(
                np.float64
            )

        # ==============================================================
        # Readout dimensions
        # ==============================================================

        self.feature_dim = (
            self.reservoir_dim + 1
            if self.use_bias
            else self.reservoir_dim
        )

        # Trainable readout matrix.
        #
        # Shape:
        #
        #     feature_dim x output_dim
        #
        self.W_out = np.zeros(
            (
                self.feature_dim,
                self.output_dim,
            ),
            dtype=np.float64,
        )

        # Initial inverse regularized correlation matrix for RLS.
        self.P = (
            np.eye(
                self.feature_dim,
                dtype=np.float64,
            )
            / self.ridge
        )

        # Indicates whether batch training or an online update has occurred.
        self.is_fitted = False

    # ==================================================================
    # Numerical helpers
    # ==================================================================

    @staticmethod
    def _spectral_radius(
        matrix: np.ndarray,
    ) -> float:
        """Return the spectral radius of a square matrix."""

        matrix = np.asarray(
            matrix,
            dtype=np.float64,
        )

        if matrix.ndim != 2:
            raise ValueError(
                "Spectral-radius calculation requires a 2-D matrix."
            )

        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError(
                "Spectral-radius calculation requires a square matrix."
            )

        if matrix.size == 0:
            return 0.0

        eigenvalues = np.linalg.eigvals(
            matrix
        )

        radius = float(
            np.max(
                np.abs(
                    eigenvalues
                )
            )
        )

        if not np.isfinite(radius):
            raise FloatingPointError(
                "Spectral-radius calculation produced a non-finite value."
            )

        return radius

    @staticmethod
    def _validate_finite(
        array: np.ndarray,
        name: str,
    ) -> None:
        """Reject NaN and infinite values."""

        if not np.all(
            np.isfinite(array)
        ):
            raise ValueError(
                f"{name} contains NaN or infinite values."
            )

    # ==================================================================
    # Input validation
    # ==================================================================

    def _validate_embedding(
        self,
        embedding: np.ndarray,
    ) -> np.ndarray:
        """Validate and normalize one embedding."""

        u = np.asarray(
            embedding,
            dtype=np.float64,
        ).reshape(-1)

        expected_shape = (
            self.input_dim,
        )

        if u.shape != expected_shape:
            raise ValueError(
                "Input dimension mismatch. "
                f"Expected {expected_shape}, got {u.shape}."
            )

        self._validate_finite(
            u,
            "embedding",
        )

        return u

    def _prepare_embeddings(
        self,
        embeddings: np.ndarray,
    ) -> np.ndarray:
        """Validate a single embedding or embedding batch."""

        X = np.asarray(
            embeddings,
            dtype=np.float64,
        )

        if X.ndim == 1:
            X = X.reshape(
                1,
                -1,
            )

        if X.ndim != 2:
            raise ValueError(
                "embeddings must be a 1-D vector or a 2-D matrix."
            )

        if X.shape[1] != self.input_dim:
            raise ValueError(
                "Input dimension mismatch. "
                f"Expected {self.input_dim} features, "
                f"got {X.shape[1]}."
            )

        if X.shape[0] == 0:
            raise ValueError(
                "embeddings must contain at least one sample."
            )

        self._validate_finite(
            X,
            "embeddings",
        )

        return X

    # ==================================================================
    # Reservoir state
    # ==================================================================

    def _state(
        self,
        embedding: np.ndarray,
    ) -> np.ndarray:
        """Transform one embedding into a reservoir state.

        Each call starts from a zero reservoir state.

        The same input embedding is repeatedly injected for the configured
        number of iterations. This creates a nonlinear fixed-point-like
        transformation but does not create temporal memory across separate
        input samples.
        """

        u = self._validate_embedding(
            embedding
        )

        x = np.zeros(
            self.reservoir_dim,
            dtype=np.float64,
        )

        for _ in range(
            self.iterations
        ):

            pre_activation = (
                self.W_in @ u
                + self.W_res @ x
            )

            candidate = np.tanh(
                pre_activation
            )

            x = (
                (1.0 - self.leak_rate)
                * x
                + self.leak_rate
                * candidate
            )

        self._validate_finite(
            x,
            "reservoir state",
        )

        return x

    def _features(
        self,
        embedding: np.ndarray,
    ) -> np.ndarray:
        """Return the feature vector supplied to the readout."""

        state = self._state(
            embedding
        )

        if self.use_bias:
            return np.concatenate(
                [
                    state,
                    np.ones(
                        1,
                        dtype=np.float64,
                    ),
                ]
            )

        return state

    def transform(
        self,
        embeddings: np.ndarray,
    ) -> np.ndarray:
        """Transform embeddings into reservoir/readout features.

        Parameters
        ----------
        embeddings:
            Shape ``(input_dim,)`` or ``(N, input_dim)``.

        Returns
        -------
        np.ndarray
            Shape ``(N, feature_dim)``.
        """

        X = self._prepare_embeddings(
            embeddings
        )

        features = np.empty(
            (
                X.shape[0],
                self.feature_dim,
            ),
            dtype=np.float64,
        )

        for i, embedding in enumerate(X):
            features[i] = self._features(
                embedding
            )

        self._validate_finite(
            features,
            "transformed features",
        )

        return features

    # ==================================================================
    # Target handling
    # ==================================================================

    def _prepare_targets(
        self,
        targets: np.ndarray,
        n_samples: int,
    ) -> np.ndarray:
        """Normalize class labels or target vectors.

        Accepted forms:

        1. Integer class labels:

            shape ``(N,)``

        2. Target matrix:

            shape ``(N, output_dim)``

        Integer class labels are converted to one-hot vectors.
        """

        y = np.asarray(
            targets
        )

        if y.ndim == 0:
            raise ValueError(
                "targets must contain at least one sample."
            )

        if y.shape[0] != n_samples:
            raise ValueError(
                "Number of targets does not match number of embeddings. "
                f"Got {y.shape[0]} targets for {n_samples} samples."
            )

        # --------------------------------------------------------------
        # Integer class labels
        # --------------------------------------------------------------

        if y.ndim == 1:

            if not np.issubdtype(
                y.dtype,
                np.integer,
            ):
                raise ValueError(
                    "1-D targets must contain integer class labels."
                )

            labels = y.astype(
                np.int64,
                copy=False,
            )

            if np.any(
                labels < 0
            ) or np.any(
                labels >= self.output_dim
            ):
                raise ValueError(
                    "Target class index is outside the valid route range "
                    f"[0, {self.output_dim - 1}]."
                )

            result = np.zeros(
                (
                    n_samples,
                    self.output_dim,
                ),
                dtype=np.float64,
            )

            result[
                np.arange(n_samples),
                labels,
            ] = 1.0

            return result

        # --------------------------------------------------------------
        # Matrix target form
        # --------------------------------------------------------------

        if y.ndim != 2:
            raise ValueError(
                "targets must be a 1-D class-label vector or "
                "a 2-D target matrix."
            )

        if y.shape[1] != self.output_dim:
            raise ValueError(
                "Target dimension mismatch. "
                f"Expected {self.output_dim} columns, "
                f"got {y.shape[1]}."
            )

        result = y.astype(
            np.float64,
            copy=False,
        )

        self._validate_finite(
            result,
            "targets",
        )

        return result

    # ==================================================================
    # Training
    # ==================================================================

    def fit(
        self,
        embeddings: np.ndarray,
        targets: np.ndarray,
    ) -> "RCRouter":
        """Fit the readout layer using ridge regression.

        The reservoir weights are never modified.

        Mathematical form:

            W_out =
                (X^T X + lambda I)^(-1) X^T Y

        The inverse is not explicitly calculated. A linear system is solved
        numerically instead.

        Parameters
        ----------
        embeddings:
            Shape ``(N, input_dim)``.

        targets:
            Either:

                * integer class labels, shape ``(N,)``

            or:

                * target matrix, shape ``(N, output_dim)``

        Returns
        -------
        RCRouter
            The fitted router.
        """

        X = self._prepare_embeddings(
            embeddings
        )

        states = self.transform(
            X
        )

        Y = self._prepare_targets(
            targets,
            n_samples=X.shape[0],
        )

        # --------------------------------------------------------------
        # Ridge regression
        # --------------------------------------------------------------

        correlation = (
            states.T @ states
        )

        cross_correlation = (
            states.T @ Y
        )

        regularizer = (
            self.ridge
            * np.eye(
                self.feature_dim,
                dtype=np.float64,
            )
        )

        system_matrix = (
            correlation
            + regularizer
        )

        # Solve:
        #
        #     M W = X^T Y
        #
        # rather than explicitly calculating M^-1.

        self.W_out = np.linalg.solve(
            system_matrix,
            cross_correlation,
        )

        # --------------------------------------------------------------
        # Initialize RLS covariance matrix
        # --------------------------------------------------------------

        identity = np.eye(
            self.feature_dim,
            dtype=np.float64,
        )

        self.P = np.linalg.solve(
            system_matrix,
            identity,
        )

        self.P = 0.5 * (
            self.P
            + self.P.T
        )

        self._validate_finite(
            self.W_out,
            "W_out",
        )

        self._validate_finite(
            self.P,
            "RLS covariance matrix",
        )

        self.is_fitted = True

        return self

    # ==================================================================
    # Prediction
    # ==================================================================

    def _require_fitted(self) -> None:
        """Require the router to have a trained or adapted readout."""

        if not self.is_fitted:
            raise RuntimeError(
                "RCRouter has not been fitted or adapted yet. "
                "Call fit() or rls_update() before prediction."
            )

    def predict_scores(
        self,
        embedding: np.ndarray,
    ) -> np.ndarray:
        """Return raw routing scores for one embedding."""

        self._require_fitted()

        features = self._features(
            embedding
        )

        scores = (
            features
            @ self.W_out
        )

        scores = np.asarray(
            scores,
            dtype=np.float64,
        ).reshape(-1)

        self._validate_finite(
            scores,
            "routing scores",
        )

        return scores

    def predict_scores_batch(
        self,
        embeddings: np.ndarray,
    ) -> np.ndarray:
        """Return raw routing scores for a batch of embeddings."""

        self._require_fitted()

        features = self.transform(
            embeddings
        )

        scores = (
            features
            @ self.W_out
        )

        scores = np.asarray(
            scores,
            dtype=np.float64,
        )

        self._validate_finite(
            scores,
            "batch routing scores",
        )

        return scores

    # ==================================================================
    # Probability conversion
    # ==================================================================

    @staticmethod
    def softmax(
        scores: np.ndarray,
    ) -> np.ndarray:
        """Apply numerically stable Softmax."""

        scores = np.asarray(
            scores,
            dtype=np.float64,
        ).reshape(-1)

        if scores.size == 0:
            raise ValueError(
                "scores must contain at least one value."
            )

        if not np.all(
            np.isfinite(scores)
        ):
            raise ValueError(
                "scores contain NaN or infinite values."
            )

        shifted = (
            scores
            - np.max(scores)
        )

        exp_scores = np.exp(
            shifted
        )

        denominator = np.sum(
            exp_scores
        )

        if (
            not np.isfinite(denominator)
            or denominator <= 0.0
        ):
            raise FloatingPointError(
                "Softmax normalization failed."
            )

        probabilities = (
            exp_scores
            / denominator
        )

        # Defensive normalization against tiny floating-point accumulation
        # error.
        probabilities /= np.sum(
            probabilities
        )

        return probabilities

    def predict_proba(
        self,
        embedding: np.ndarray,
    ) -> np.ndarray:
        """Return route probabilities for one embedding."""

        return self.softmax(
            self.predict_scores(
                embedding
            )
        )

    def predict_proba_batch(
        self,
        embeddings: np.ndarray,
    ) -> np.ndarray:
        """Return route probabilities for a batch of embeddings."""

        scores = self.predict_scores_batch(
            embeddings
        )

        shifted = (
            scores
            - np.max(
                scores,
                axis=1,
                keepdims=True,
            )
        )

        exp_scores = np.exp(
            shifted
        )

        denominator = np.sum(
            exp_scores,
            axis=1,
            keepdims=True,
        )

        if not np.all(
            np.isfinite(
                denominator
            )
        ) or np.any(
            denominator <= 0.0
        ):
            raise FloatingPointError(
                "Batch Softmax normalization failed."
            )

        probabilities = (
            exp_scores
            / denominator
        )

        return probabilities

    # ==================================================================
    # Routing
    # ==================================================================

    def route(
        self,
        embedding: np.ndarray,
    ) -> tuple[int, float, np.ndarray]:
        """Execute confidence-gated dynamic routing.

        Returns
        -------
        tuple
            ``(selected_route, confidence, probabilities)``

        selected_route:
            Backend route index.

            ``-1`` means System 1 confidence was below the configured
            threshold and the query should be delegated to System 2.

        confidence:
            Maximum Softmax probability.

        probabilities:
            Complete route probability distribution.

        Important
        ---------
        Softmax confidence is treated here as a routing score, not as a
        statistically calibrated probability of correctness.
        """

        probabilities = self.predict_proba(
            embedding
        )

        route_index = int(
            np.argmax(
                probabilities
            )
        )

        confidence = float(
            probabilities[
                route_index
            ]
        )

        if (
            confidence
            < self.fallback_threshold
        ):
            return (
                -1,
                confidence,
                probabilities,
            )

        return (
            route_index,
            confidence,
            probabilities,
        )

    def route_batch(
        self,
        embeddings: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Execute confidence-gated routing for a batch.

        Returns
        -------
        routes:
            Integer route indices. ``-1`` indicates System 2 delegation.

        confidences:
            Maximum probability for each sample.

        probabilities:
            Full probability matrix.
        """

        probabilities = self.predict_proba_batch(
            embeddings
        )

        routes = np.argmax(
            probabilities,
            axis=1,
        ).astype(
            np.int64
        )

        confidences = np.max(
            probabilities,
            axis=1,
        ).astype(
            np.float64
        )

        fallback_mask = (
            confidences
            < self.fallback_threshold
        )

        routes[
            fallback_mask
        ] = -1

        return (
            routes,
            confidences,
            probabilities,
        )

    # ==================================================================
    # Expert Slot Expansion
    # ==================================================================

    def add_route(self) -> int:
        """Add a new routing lane without changing the reservoir.

        Only the readout matrix is expanded.

        The new route initially contains zero readout weights. It therefore
        has no learned routing behavior until additional training or RLS
        updates provide information for that route.

        Returns
        -------
        int
            Index of the newly created route.
        """

        new_column = np.zeros(
            (
                self.feature_dim,
                1,
            ),
            dtype=np.float64,
        )

        self.W_out = np.hstack(
            [
                self.W_out,
                new_column,
            ]
        )

        self.output_dim += 1

        return (
            self.output_dim - 1
        )

    # ==================================================================
    # Online Recursive Least Squares
    # ==================================================================

    def rls_update(
        self,
        embedding: np.ndarray,
        target: np.ndarray,
        forgetting_factor: float = 0.98,
    ) -> "RCRouter":
        """Update the readout online using Recursive Least Squares.

        The reservoir is fixed. Only ``W_out`` and ``P`` are modified.

        Standard update:

            K_t =
                P_(t-1) x_t /
                (lambda + x_t^T P_(t-1) x_t)

            e_t =
                y_t - x_t^T W_(t-1)

            W_t =
                W_(t-1) + K_t e_t

            P_t =
                [P_(t-1) - K_t x_t^T P_(t-1)] / lambda

        Parameters
        ----------
        embedding:
            Semantic embedding vector, shape ``(input_dim,)``.

        target:
            Desired routing target, shape ``(output_dim,)``.

        forgetting_factor:
            RLS forgetting factor in ``(0, 1]``.

        Returns
        -------
        RCRouter
            Updated router instance.
        """

        if (
            not np.isfinite(
                forgetting_factor
            )
            or not 0.0
            < forgetting_factor
            <= 1.0
        ):
            raise ValueError(
                "forgetting_factor must be in the range (0.0, 1.0]."
            )

        features = self._features(
            embedding
        ).reshape(
            -1,
            1,
        )

        target_array = np.asarray(
            target,
            dtype=np.float64,
        ).reshape(-1)

        expected_shape = (
            self.output_dim,
        )

        if target_array.shape != expected_shape:
            raise ValueError(
                "Target dimension mismatch. "
                f"Expected {expected_shape}, "
                f"got {target_array.shape}."
            )

        self._validate_finite(
            target_array,
            "target",
        )

        # --------------------------------------------------------------
        # Ensure covariance matrix is valid before update.
        # --------------------------------------------------------------

        if self.P.shape != (
            self.feature_dim,
            self.feature_dim,
        ):
            raise RuntimeError(
                "Internal RLS covariance matrix has an invalid shape."
            )

        if not np.all(
            np.isfinite(self.P)
        ):
            raise FloatingPointError(
                "Internal RLS covariance matrix contains "
                "NaN or infinite values."
            )

        # Enforce symmetry before calculation.
        self.P = 0.5 * (
            self.P
            + self.P.T
        )

        # --------------------------------------------------------------
        # RLS gain
        # --------------------------------------------------------------

        P_features = (
            self.P
            @ features
        )

        denominator = (
            forgetting_factor
            + features.T
            @ P_features
        )

        denominator_value = float(
            denominator[0, 0]
        )

        if (
            not np.isfinite(
                denominator_value
            )
            or denominator_value <= 0.0
        ):
            raise FloatingPointError(
                "RLS denominator became invalid."
            )

        K = (
            P_features
            / denominator_value
        )

        # --------------------------------------------------------------
        # Prediction error
        # --------------------------------------------------------------

        prediction = (
            features.T
            @ self.W_out
        )

        target_row = (
            target_array.reshape(
                1,
                -1,
            )
        )

        error = (
            target_row
            - prediction
        )

        # --------------------------------------------------------------
        # Readout update
        # --------------------------------------------------------------

        self.W_out += (
            K
            @ error
        )

        # --------------------------------------------------------------
        # Covariance update
        # --------------------------------------------------------------

        self.P = (
            self.P
            - K
            @ features.T
            @ self.P
        ) / forgetting_factor

        # Exact arithmetic preserves symmetry. Floating-point arithmetic
        # may introduce tiny asymmetry, so correct it explicitly.
        self.P = 0.5 * (
            self.P
            + self.P.T
        )

        if not np.all(
            np.isfinite(
                self.W_out
            )
        ):
            raise FloatingPointError(
                "RLS update produced non-finite W_out values."
            )

        if not np.all(
            np.isfinite(
                self.P
            )
        ):
            raise FloatingPointError(
                "RLS update produced non-finite covariance values."
            )

        self.is_fitted = True

        return self

    # ==================================================================
    # Diagnostics
    # ==================================================================

    def reservoir_spectral_radius(
        self,
    ) -> float:
        """Return the actual spectral radius of the fixed reservoir."""

        return self._spectral_radius(
            self.W_res
        )

    def route_count(
        self,
    ) -> int:
        """Return the number of currently available routing lanes."""

        return self.output_dim

    def reservoir_parameters(
        self,
    ) -> dict:
        """Return reservoir configuration and diagnostic metadata."""

        return {
            "input_dim": self.input_dim,
            "reservoir_dim": self.reservoir_dim,
            "output_dim": self.output_dim,
            "feature_dim": self.feature_dim,
            "spectral_radius_target": self.spectral_radius,
            "spectral_radius_actual": (
                self.reservoir_spectral_radius()
            ),
            "leak_rate": self.leak_rate,
            "sparsity": self.sparsity,
            "ridge": self.ridge,
            "iterations": self.iterations,
            "seed": self.seed,
            "use_bias": self.use_bias,
            "fallback_threshold": (
                self.fallback_threshold
            ),
            "is_fitted": self.is_fitted,
        }

    def reservoir_state_norm(
        self,
        embedding: np.ndarray,
    ) -> float:
        """Return the L2 norm of the reservoir state for one embedding."""

        state = self._state(
            embedding
        )

        return float(
            np.linalg.norm(
                state
            )
        )

    def readout_norm(
        self,
    ) -> float:
        """Return the Frobenius norm of the current readout matrix."""

        return float(
            np.linalg.norm(
                self.W_out
            )
        )

    def covariance_norm(
        self,
    ) -> float:
        """Return the Frobenius norm of the RLS covariance matrix."""

        return float(
            np.linalg.norm(
                self.P
            )
        )

    def reset_readout(
        self,
    ) -> "RCRouter":
        """Reset readout weights and RLS covariance.

        The fixed input projection and recurrent reservoir are untouched.

        This is useful for controlled architectural experiments where the
        same reservoir realization must be evaluated across multiple
        independent readout-training conditions.
        """

        self.W_out = np.zeros(
            (
                self.feature_dim,
                self.output_dim,
            ),
            dtype=np.float64,
        )

        self.P = (
            np.eye(
                self.feature_dim,
                dtype=np.float64,
            )
            / self.ridge
        )

        self.is_fitted = False

        return self
