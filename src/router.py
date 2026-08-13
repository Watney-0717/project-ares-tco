# Copyright 2026 Watney-0717
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://apache.org
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Project Ares-TCO: Reservoir Computing Router Core Module.

This module maps low-cost semantic embedding vectors into a high-dimensional
dynamical reservoir state space, providing sub-millisecond linear readout routing.
It supports hot-swappable 'Expert Slot Expansion' and real-time online adaptation
via Recursive Least Squares (RLS) without requiring system downtime or full
backpropagation.
"""

import numpy as np


class RCRouter:
    """Autonomous Reservoir Computing Router acting as System 1 (Intuitive Layer).

    Extracts non-linear contextual features from continuous or transient input
    embeddings to predict the optimal computation lane (Backend AI) under
    sub-millisecond latencies.
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
    ):
        """Initializes the RCRouter and scales the fixed internal reservoir weights.

        Parameters
        ----------
        input_dim : int
            Dimensionality of incoming semantic vectors.
        reservoir_dim : int
            Size of the high-dimensional hidden dynamical state space.
        output_dim : int
            Initial number of available backend routing targets.
        spectral_radius : float
            Spectral radius of the reservoir matrix.
        leak_rate : float
            Leaking rate of the reservoir state update.
        sparsity : float
            Ratio of non-zero recurrent connections.
        ridge : float
            Regularization constant for the inverse correlation matrix.
        seed : int
            Random seed for reproducibility.
        iterations : int
            Number of recurrent state transitions per input embedding.
        fallback_threshold : float
            Confidence threshold below which queries escalate to System 2.
        """
        rng = np.random.default_rng(seed)

        self.input_dim = input_dim
        self.reservoir_dim = reservoir_dim
        self.output_dim = output_dim
        self.leak_rate = leak_rate
        self.ridge = ridge
        self.iterations = iterations
        self.fallback_threshold = fallback_threshold

        # Fixed input-to-reservoir weight matrix.
        self.W_in = rng.uniform(
            -0.1,
            0.1,
            size=(reservoir_dim, input_dim),
        )

        # Fixed recurrent reservoir weight matrix.
        W_res_raw = rng.uniform(
            -0.5,
            0.5,
            size=(reservoir_dim, reservoir_dim),
        )

        # Apply network sparsity mask.
        mask = rng.random(W_res_raw.shape) < sparsity
        W_res_raw *= mask

        # Scale the recurrent matrix to the requested spectral radius.
        eigvals = np.linalg.eigvals(W_res_raw)
        rho = np.max(np.abs(eigvals))

        if rho > 0:
            self.W_res = (
                W_res_raw * (spectral_radius / rho)
            ).astype(np.float64)
        else:
            self.W_res = W_res_raw.astype(np.float64)

        # Trainable readout weight matrix.
        self.W_out = np.zeros(
            (reservoir_dim, output_dim),
            dtype=np.float64,
        )

        # Inverse correlation matrix used by online RLS.
        self.P = np.eye(
            reservoir_dim,
            dtype=np.float64,
        ) / ridge

    def _state(self, embedding: np.ndarray) -> np.ndarray:
        """Projects a single input embedding into reservoir state space."""
        u = np.asarray(embedding, dtype=np.float64).reshape(-1)

        if u.shape != (self.input_dim,):
            raise ValueError(
                f"Input dimension mismatch. "
                f"Expected {(self.input_dim,)}, got {u.shape}"
            )

        x = np.zeros(
            self.reservoir_dim,
            dtype=np.float64,
        )

        for _ in range(self.iterations):
            pre_activation = self.W_in @ u + self.W_res @ x
            candidate = np.tanh(pre_activation)
            x = (
                (1.0 - self.leak_rate) * x
                + self.leak_rate * candidate
            )

        return x

    def transform(self, embeddings: np.ndarray) -> np.ndarray:
        """Transforms input embeddings into reservoir states."""
        embeddings = np.asarray(
            embeddings,
            dtype=np.float64,
        )

        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        return np.vstack([
            self._state(embedding)
            for embedding in embeddings
        ])

    def fit(
        self,
        embeddings: np.ndarray,
        targets: np.ndarray,
    ):
        """Initializes the readout layer using ridge regression."""
        states = self.transform(embeddings)
        targets = np.asarray(
            targets,
            dtype=np.float64,
        )

        A = states.T @ states
        B = states.T @ targets
        regularizer = (
            self.ridge
            * np.eye(self.reservoir_dim)
        )

        self.W_out = np.linalg.solve(
            A + regularizer,
            B,
        )
        self.P = np.linalg.inv(
            A + regularizer
        )

    def predict_scores(
        self,
        embedding: np.ndarray,
    ) -> np.ndarray:
        """Calculates raw routing logits."""
        state = self._state(embedding)
        return state @ self.W_out

    @staticmethod
    def softmax(scores: np.ndarray) -> np.ndarray:
        """Applies numerically stable Softmax."""
        scores = scores - np.max(scores)
        exp_scores = np.exp(scores)
        return exp_scores / np.sum(exp_scores)

    def route(self, embedding: np.ndarray) -> tuple:
        """Executes confidence-based dynamic routing.

        Returns
        -------
        tuple
            (selected_route, confidence, probabilities)

            selected_route:
                Index of the selected backend lane, or -1 when
                confidence is below the fallback threshold.

            confidence:
                Peak Softmax probability.

            probabilities:
                Full probability distribution across lanes.
        """
        scores = self.predict_scores(embedding)
        probabilities = self.softmax(scores)

        route = int(np.argmax(probabilities))
        confidence = float(probabilities[route])

        if confidence < self.fallback_threshold:
            route = -1

        return route, confidence, probabilities

    def add_route(self) -> int:
        """Appends a new output routing lane to the readout layer.

        Allows adding a new specialized model (Expert) without
        reservoir retraining.

        Returns
        -------
        int
            The newly assigned route lane index.
        """
        self.W_out = np.hstack(
            [
                self.W_out,
                np.zeros(
                    (self.reservoir_dim, 1),
                    dtype=np.float64,
                ),
            ]
        )

        self.output_dim += 1

        return self.output_dim - 1

    def rls_update(
        self,
        embedding: np.ndarray,
        target: np.ndarray,
        forgetting_factor: float = 0.98,
    ):
        """Applies Recursive Least Squares tracking to update readout weights.

        Parameters
        ----------
        embedding : np.ndarray
            Semantic embedding vector.
        target : np.ndarray
            Target vector representing the desired routing output.
        forgetting_factor : float
            Exponential forgetting factor.
        """
        if not 0.0 < forgetting_factor <= 1.0:
            raise ValueError(
                "forgetting_factor must be in the range (0.0, 1.0]."
            )

        state = self._state(embedding).reshape(-1, 1)

        target = np.asarray(
            target,
            dtype=np.float64,
        ).reshape(-1)

        if target.shape != (self.output_dim,):
            raise ValueError(
                f"Target dimension {target.shape} "
                f"does not match output_dim {self.output_dim}"
            )

        target = target.reshape(1, -1)

        P_state = self.P @ state
        denominator = (
            forgetting_factor
            + state.T @ P_state
        )

        K = P_state / denominator

        prediction = state.T @ self.W_out
        error = target - prediction

        # Online adaptation of the readout layer only.
        self.W_out += K @ error

        # Update inverse correlation matrix.
        self.P = (
            self.P
            - K @ state.T @ self.P
        ) / forgetting_factor
       
