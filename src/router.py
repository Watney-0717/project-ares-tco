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

The router uses a fixed recurrent reservoir to transform semantic input
embeddings into a higher-dimensional state representation. Only the readout
layer is trained. Routing decisions are obtained from the readout scores and
converted into probabilities using a numerically stable softmax.

The module also supports:

    * confidence-gated delegation to System 2;
    * fixed-reservoir training with ridge regression;
    * online readout adaptation using Recursive Least Squares (RLS);
    * hot addition of new routing lanes ("Expert Slot Expansion");
    * deterministic initialization through an explicit random seed.

Important experimental scope
----------------------------

This implementation provides the routing mechanism required for architectural
experiments. It does NOT establish production accuracy, production latency,
or a production routing threshold.

In particular, ``fallback_threshold`` is an externally supplied operating
parameter. Its numerical value must be evaluated separately from the
structural validity of the architecture.
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
    Softmax probabilities
        |
        +---- confidence >= threshold --> System 1 route
        |
        +---- confidence < threshold ---> System 2 delegation

    The reservoir weights remain fixed after initialization. Training and
    online adaptation modify the readout only.

    Parameters
    ----------
    input_dim:
        Dimensionality of the incoming embedding vector.

    reservoir_dim:
        Number of recurrent reservoir units.

    output_dim:
        Number of routing lanes/backends initially available.

    spectral_radius:
        Target spectral radius of the recurrent reservoir matrix before
        application of the leaky state update.

    leak_rate:
        Leaky integration coefficient in the range (0, 1].

    sparsity:
        Fraction of recurrent connections that are non-zero.
        For example, 0.1 means approximately 10% non-zero connections.

    ridge:
        Positive ridge regularization coefficient.

    seed:
        Random seed used for deterministic reservoir initialization.

    iterations:
        Number of recurrent state transitions performed for each embedding.

    fallback_threshold:
        Confidence threshold used by ``route()`` to determine whether the
        query is accepted by System 1 or delegated to System 2.

        This is an operating parameter, not a learned quantity and not a
        production-performance claim.

    use_bias:
        Whether to include a trainable intercept term in the readout.
        Enabling this improves the generality of the linear readout without
        changing the fixed-reservoir principle.
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
        seed: int = 42,
        iterations: int = 3,
        fallback_threshold: float = 0.65,
        use_bias: bool = True,
    ) -> None:

        # ---------------------------------------------------------------
        # Parameter validation
        # ---------------------------------------------------------------

        if not isinstance(input_dim, (int, np.integer)) or input_dim <= 0:
            raise ValueError("input_dim must be a positive integer.")

        if not isinstance(reservoir_dim, (int, np.integer)):
            raise ValueError("reservoir_dim must be an integer.")

        if reservoir_dim <= 0:
            raise ValueError("reservoir_dim must be positive.")

        if not isinstance(output_dim, (int, np.integer)):
            raise ValueError("output_dim must be an integer.")

        if output_dim <= 0:
            raise ValueError("output_dim must be positive.")

        if not np.isfinite(spectral_radius) or spectral_radius < 0.0:
            raise ValueError(
                "spectral_radius must be finite and non-negative."
            )

        if not np.isfinite(leak_rate) or not 0.0 < leak_rate <= 1.0:
            raise ValueError(
                "leak_rate must be in the range (0.0, 1.0]."
            )

        if not np.isfinite(sparsity) or not 0.0 <= sparsity <= 1.0:
            raise ValueError(
                "sparsity must be in the range [0.0, 1.0]."
            )

        if not np.isfinite(ridge) or ridge <= 0.0:
            raise ValueError("ridge must be finite and strictly positive.")

        if not isinstance(iterations, (int, np.integer)) or iterations <= 0:
            raise ValueError("iterations must be a positive integer.")

        if (
            not np.isfinite(fallback_threshold)
            or not 0.0 <= fallback_threshold <= 1.0
        ):
            raise ValueError(
                "fallback_threshold must be in the range [0.0, 1.0]."
            )

        self.input_dim = int(input_dim)
        self.reservoir_dim = int(reservoir_dim)
        self.output_dim = int(output_dim)

        self.spectral_radius = float(spectral_radius)
        self.leak_rate = float(leak_rate)
        self.sparsity = float(sparsity)
        self.ridge = float(ridge)
        self.iterations = int(iterations)
        self.fallback_threshold = float(fallback_threshold)
        self.use_bias = bool(use_bias)

        self.seed = seed

        rng = np.random.default_rng(seed)

        # ---------------------------------------------------------------
        # Fixed input-to-reservoir projection
        # ---------------------------------------------------------------

        self.W_in = rng.uniform(
            -0.1,
            0.1,
            size=(self.reservoir_dim, self.input_dim),
        ).astype(np.float64)

        # ---------------------------------------------------------------
        # Fixed recurrent reservoir
        # ---------------------------------------------------------------

        W_res_raw = rng.uniform(
            -0.5,
            0.5,
            size=(self.reservoir_dim, self.reservoir_dim),
        ).astype(np.float64)

        # Apply recurrent sparsity mask.
        mask = rng.random(
            size=W_res_raw.shape
        ) < self.sparsity

        W_res_raw *= mask

        # Scale to requested spectral radius.
        #
        # The reservoir remains fixed after this point.
        if self.spectral_radius == 0.0:
            self.W_res = np.zeros_like(W_res_raw)

        else:
            rho = self._spectral_radius(W_res_raw)

            if rho <= np.finfo(np.float64).eps:
                raise ValueError(
                    "Reservoir matrix has zero spectral radius. "
                    "Increase sparsity or use a non-zero reservoir."
                )

            self.W_res = (
                W_res_raw * (self.spectral_radius / rho)
            ).astype(np.float64)

        # ---------------------------------------------------------------
        # Readout dimensions
        # ---------------------------------------------------------------

        self.feature_dim = (
            self.reservoir_dim + 1
            if self.use_bias
            else self.reservoir_dim
        )

        # Trainable readout.
        self.W_out = np.zeros(
            (self.feature_dim, self.output_dim),
            dtype=np.float64,
        )

        # Inverse regularized correlation matrix used by RLS.
        self.P = (
            np.eye(
                self.feature_dim,
                dtype=np.float64,
            )
            / self.ridge
        )

        self.is_fitted = False

    # ------------------------------------------------------------------
    # Numerical helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _spectral_radius(matrix: np.ndarray) -> float:
        """Returns the spectral radius of a square matrix."""

        matrix = np.asarray(matrix, dtype=np.float64)

        if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
            raise ValueError(
                "Spectral-radius calculation requires a square matrix."
            )

        if matrix.size == 0:
            return 0.0

        eigenvalues = np.linalg.eigvals(matrix)

        return float(np.max(np.abs(eigenvalues)))

    @staticmethod
    def _validate_finite(
        array: np.ndarray,
        name: str,
    ) -> None:
        """Rejects NaN and infinite values."""

        if not np.all(np.isfinite(array)):
            raise ValueError(
                f"{name} contains NaN or infinite values."
            )

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def _validate_embedding(
        self,
        embedding: np.ndarray,
    ) -> np.ndarray:
        """Validates and normalizes a single embedding."""

        u = np.asarray(
            embedding,
            dtype=np.float64,
        ).reshape(-1)

        expected_shape = (self.input_dim,)

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
        """Validates a batch or single embedding matrix."""

        X = np.asarray(
            embeddings,
            dtype=np.float64,
        )

        if X.ndim == 1:
            X = X.reshape(1, -1)

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

    # ------------------------------------------------------------------
    # Reservoir state
    # ------------------------------------------------------------------

    def _state(
        self,
        embedding: np.ndarray,
    ) -> np.ndarray:
        """Maps one embedding into a fixed reservoir state."""

        u = self._validate_embedding(
            embedding
        )

        x = np.zeros(
            self.reservoir_dim,
            dtype=np.float64,
        )

        for _ in range(self.iterations):
            pre_activation = (
                self.W_in @ u
                + self.W_res @ x
            )

            candidate = np.tanh(
                pre_activation
            )

            x = (
                (1.0 - self.leak_rate) * x
                + self.leak_rate * candidate
            )

        return x

    def _features(
        self,
        embedding: np.ndarray,
    ) -> np.ndarray:
        """Returns the readout feature vector."""

        state = self._state(
            embedding
        )

        if self.use_bias:
            return np.concatenate(
                [
                    state,
                    np.ones(1, dtype=np.float64),
                ]
            )

        return state

    def transform(
        self,
        embeddings: np.ndarray,
    ) -> np.ndarray:
        """Transforms embeddings into reservoir/readout features.

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

        states = np.empty(
            (X.shape[0], self.feature_dim),
            dtype=np.float64,
        )

        for i, embedding in enumerate(X):
            states[i] = self._features(
                embedding
            )

        return states

    # ------------------------------------------------------------------
    # Target handling
    # ------------------------------------------------------------------

    def _prepare_targets(
        self,
        targets: np.ndarray,
        n_samples: int,
    ) -> np.ndarray:
        """Normalizes training targets into a 2-D readout matrix.

        Accepted forms
        --------------
        1. Integer class labels:

            shape ``(N,)``

        2. One-hot / soft target matrix:

            shape ``(N, output_dim)``

        Integer class labels are converted into one-hot vectors.
        """

        y = np.asarray(targets)

        if y.ndim == 0:
            raise ValueError(
                "targets must contain at least one sample."
            )

        if y.shape[0] != n_samples:
            raise ValueError(
                "Number of targets does not match number of embeddings. "
                f"Got {y.shape[0]} targets for {n_samples} samples."
            )

        # ---------------------------------------------------------------
        # Class-label form: [0, 1, 2, 1, ...]
        # ---------------------------------------------------------------

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

            if np.any(labels < 0) or np.any(
                labels >= self.output_dim
            ):
                raise ValueError(
                    "Target class index is outside the valid route range "
                    f"[0, {self.output_dim - 1}]."
                )

            result = np.zeros(
                (n_samples, self.output_dim),
                dtype=np.float64,
            )

            result[
                np.arange(n_samples),
                labels,
            ] = 1.0

            return result

        # ---------------------------------------------------------------
        # Matrix target form
        # ---------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(
        self,
        embeddings: np.ndarray,
        targets: np.ndarray,
    ) -> "RCRouter":
        """Fits the readout using ridge regression.

        The reservoir itself is never modified.

        Parameters
        ----------
        embeddings:
            Input embeddings with shape ``(N, input_dim)``.

        targets:
            Either integer class labels with shape ``(N,)`` or target
            vectors with shape ``(N, output_dim)``.

        Returns
        -------
        RCRouter
            The fitted router instance.
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

        # Regularized normal equation:
        #
        # W = (X^T X + lambda I)^(-1) X^T Y
        #
        # We solve the linear system directly rather than explicitly
        # calculating the inverse.
        A = states.T @ states
        B = states.T @ Y

        regularizer = (
            self.ridge
            * np.eye(
                self.feature_dim,
                dtype=np.float64,
            )
        )

        system_matrix = (
            A + regularizer
        )

        self.W_out = np.linalg.solve(
            system_matrix,
            B,
        )

        # RLS initialization uses the same regularized inverse correlation
        # matrix as the batch ridge solution.
        #
        # Solve M X = I instead of np.linalg.inv(M).
        identity = np.eye(
            self.feature_dim,
            dtype=np.float64,
        )

        self.P = np.linalg.solve(
            system_matrix,
            identity,
        )

        self.is_fitted = True

        return self

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict_scores(
        self,
        embedding: np.ndarray,
    ) -> np.ndarray:
        """Returns raw readout scores for one embedding."""

        features = self._features(
            embedding
        )

        scores = features @ self.W_out

        return np.asarray(
            scores,
            dtype=np.float64,
        ).reshape(-1)

    def predict_scores_batch(
        self,
        embeddings: np.ndarray,
    ) -> np.ndarray:
        """Returns raw readout scores for a batch of embeddings."""

        features = self.transform(
            embeddings
        )

        return features @ self.W_out

    @staticmethod
    def softmax(
        scores: np.ndarray,
    ) -> np.ndarray:
        """Applies numerically stable Softmax."""

        scores = np.asarray(
            scores,
            dtype=np.float64,
        ).reshape(-1)

        if scores.size == 0:
            raise ValueError(
                "scores must contain at least one value."
            )

        if not np.all(np.isfinite(scores)):
            raise ValueError(
                "scores contain NaN or infinite values."
            )

        shifted = scores - np.max(scores)

        exp_scores = np.exp(
            shifted
        )

        denominator = np.sum(
            exp_scores
        )

        if not np.isfinite(denominator) or denominator <= 0.0:
            raise FloatingPointError(
                "Softmax normalization failed."
            )

        probabilities = (
            exp_scores / denominator
        )

        return probabilities

    def predict_proba(
        self,
        embedding: np.ndarray,
    ) -> np.ndarray:
        """Returns route probabilities for one embedding."""

        return self.softmax(
            self.predict_scores(
                embedding
            )
        )

    # ------------------------------------------------------------------
    # Routing / System 2 delegation
    # ------------------------------------------------------------------

    def route(
        self,
        embedding: np.ndarray,
    ) -> tuple[int, float, np.ndarray]:
        """Executes confidence-gated dynamic routing.

        Returns
        -------
        tuple
            ``(selected_route, confidence, probabilities)``

        selected_route:
            Selected backend lane index.

            ``-1`` means that System 1 did not meet the configured
            confidence threshold and the query should be delegated to
            System 2.

        confidence:
            Maximum route probability.

        probabilities:
            Complete probability distribution over all available routes.
        """

        probabilities = self.predict_proba(
            embedding
        )

        route_index = int(
            np.argmax(probabilities)
        )

        confidence = float(
            probabilities[route_index]
        )

        if confidence < self.fallback_threshold:
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

    # ------------------------------------------------------------------
    # Expert Slot Expansion
    # ------------------------------------------------------------------

    def add_route(self) -> int:
        """Adds a new routing lane without retraining the reservoir.

        The recurrent reservoir and input projection remain completely
        unchanged. Only the readout matrix is expanded by one column.

        The new route initially has zero readout weights and therefore
        requires subsequent supervised training or RLS updates before it
        can make meaningful routing decisions.

        Returns
        -------
        int
            Index of the newly added route.
        """

        new_column = np.zeros(
            (self.feature_dim, 1),
            dtype=np.float64,
        )

        self.W_out = np.hstack(
            [
                self.W_out,
                new_column,
            ]
        )

        self.output_dim += 1

        return self.output_dim - 1

    # ------------------------------------------------------------------
    # Online Recursive Least Squares
    # ------------------------------------------------------------------

    def rls_update(
        self,
        embedding: np.ndarray,
        target: np.ndarray,
        forgetting_factor: float = 0.98,
    ) -> "RCRouter":
        """Updates the readout online using Recursive Least Squares.

        The reservoir is fixed. Only ``W_out`` and ``P`` are updated.

        Parameters
        ----------
        embedding:
            Semantic embedding vector with shape ``(input_dim,)``.

        target:
            Target vector with shape ``(output_dim,)``.

        forgetting_factor:
            RLS forgetting factor in the interval ``(0, 1]``.

        Returns
        -------
        RCRouter
            The updated router instance.
        """

        if (
            not np.isfinite(forgetting_factor)
            or not 0.0 < forgetting_factor <= 1.0
        ):
            raise ValueError(
                "forgetting_factor must be in the range (0.0, 1.0]."
            )

        features = self._features(
            embedding
        ).reshape(-1, 1)

        target_array = np.asarray(
            target,
            dtype=np.float64,
        ).reshape(-1)

        if target_array.shape != (
            self.output_dim,
        ):
            raise ValueError(
                "Target dimension mismatch. "
                f"Expected {(self.output_dim,)}, "
                f"got {target_array.shape}."
            )

        self._validate_finite(
            target_array,
            "target",
        )

        target_row = target_array.reshape(
            1,
            -1,
        )

        # ---------------------------------------------------------------
        # Standard RLS update
        #
        # K_t = P_{t-1} x_t /
        #       (lambda + x_t^T P_{t-1} x_t)
        #
        # W_t = W_{t-1} + K_t e_t
        #
        # P_t = (P_{t-1} - K_t x_t^T P_{t-1}) / lambda
        # ---------------------------------------------------------------

        P_features = self.P @ features

        denominator = (
            forgetting_factor
            + features.T @ P_features
        )

        denominator_value = float(
            denominator[0, 0]
        )

        if (
            not np.isfinite(denominator_value)
            or denominator_value <= 0.0
        ):
            raise FloatingPointError(
                "RLS denominator became invalid."
            )

        K = (
            P_features
            / denominator_value
        )

        prediction = (
            features.T @ self.W_out
        )

        error = (
            target_row - prediction
        )

        self.W_out += (
            K @ error
        )

        self.P = (
            self.P
            - K @ features.T @ self.P
        ) / forgetting_factor

        # Numerical symmetry correction.
        #
        # In exact arithmetic P remains symmetric. Floating-point
        # accumulation can introduce small asymmetry.
        self.P = 0.5 * (
            self.P + self.P.T
        )

        self.is_fitted = True

        return self

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def reservoir_spectral_radius(self) -> float:
        """Returns the actual spectral radius of the fixed reservoir."""

        return self._spectral_radius(
            self.W_res
        )

    def route_count(self) -> int:
        """Returns the number of currently available routing lanes."""

        return self.output_dim

    def reservoir_parameters(self) -> dict:
        """Returns immutable reservoir configuration metadata."""

        return {
            "input_dim": self.input_dim,
            "reservoir_dim": self.reservoir_dim,
            "output_dim": self.output_dim,
            "spectral_radius_target": self.spectral_radius,
            "spectral_radius_actual": self.reservoir_spectral_radius(),
            "leak_rate": self.leak_rate,
            "sparsity": self.sparsity,
            "ridge": self.ridge,
            "iterations": self.iterations,
            "seed": self.seed,
            "use_bias": self.use_bias,
        }



