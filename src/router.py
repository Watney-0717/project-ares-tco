python# Copyright 2026 Watney-0717
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
via Recursive Least Squares (RLS) without requiring system downtime or full backpropagation.
"""

import numpy as np


class RCRouter:
    """Autonomous Reservoir Computing Router acting as System 1 (Intuitive Layer).

    Extracts non-linear contextual features from continuous or transient input 
    embeddings to predict the optimal computation lane (Backend AI) under sub-millisecond 
    latencies.
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
            Dimensionality of incoming semantic vectors (e.g., 384 for tiny ONNX embeddings).
        reservoir_dim : int
            Size of the high-dimensional hidden dynamical state space.
        output_dim : int
            Initial number of available backend routing targets (lanes).
        spectral_radius : float
            Spectral radius of the reservoir matrix to guarantee the Echo State Property (ESP).
        leak_rate : float
            Leaking rate of the reservoir state update equations (0.0 < leak_rate <= 1.0).
        sparsity : float
            Ratio of non-zero recurrent connections inside the reservoir network.
        ridge : float
            Regularization constant utilized to initialize the inverse correlation matrix.
        seed : int
            Random seed to ensure strict reproducibility across experimental setups.
        iterations : int
            Number of internal recurrent state transitions per input embedding vector.
        fallback_threshold : float
            Softmax confidence threshold below which queries escalate to System 2.
        """
        rng = np.random.default_rng(seed)

        self.input_dim = input_dim
        self.reservoir_dim = reservoir_dim
        self.output_dim = output_dim
        self.leak_rate = leak_rate
        self.ridge = ridge
        self.iterations = iterations
        self.fallback_threshold = fallback_threshold

        # Input-to-Reservoir fixed weight matrix (W_in)
        self.W_in = rng.uniform(-0.1, 0.1, size=(reservoir_dim, input_dim))

        # Raw recurrent Reservoir weight matrix (W_res)
        W_res_raw = rng.uniform(-0.5, 0.5, size=(reservoir_dim, reservoir_dim))

        # Apply network sparsity mask
        mask = rng.random(W_res_raw.shape) < sparsity
        W_res_raw *= mask

        # Strict spectral radius scaling to isolate and block complex type contagion
        eigvals = np.linalg.eigvals(W_res_raw)
        rho = np.max(np.abs(eigvals))  # Magnitude of the largest eigenvalue (float)

        if rho > 0:
            # Force explicit float64 cast to purge complex type contagion from eigenvalues
            self.W_res = (W_res_raw * (spectral_radius / rho)).astype(np.float64)
        else:
            self.W_res = W_res_raw.astype(np.float64)

        # Trainable Readout weight matrix (W_out)
        self.W_out = np.zeros((reservoir_dim, output_dim), dtype=np.float64)

        # Initialize inverse correlation matrix P for stable online RLS tracking
        self.P = np.eye(reservoir_dim, dtype=np.float64) / ridge

    def _state(self, embedding: np.ndarray) -> np.ndarray:
        """Projects a single input embedding into the recursive reservoir state space."""
        u = np.asarray(embedding, dtype=np.float64).reshape(-1)
      if u.shape != (self.input_dim,):
    raise ValueError(f"Input dimension mismatch. Expected {(self.input_dim,)}, got {u.shape}")

        x = np.zeros(self.reservoir_dim, dtype=np.float64)

        # Evolve the internal state trajectory through recurrent iterations
        for _ in range(self.iterations):
            pre_activation = self.W_in @ u + self.W_res @ x
            candidate = np.tanh(pre_activation)
            x = (1.0 - self.leak_rate) * x + self.leak_rate * candidate

        return x

    def transform(self, embeddings: np.ndarray) -> np.ndarray:
        """Transforms a batch of input embeddings into a matrix of reservoir states."""
        embeddings = np.asarray(embeddings, dtype=np.float64)

        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        return np.vstack([self._state(e) for e in embeddings])

    def fit(self, embeddings: np.ndarray, targets: np.ndarray):
        """Executes a closed-form ridge regression to initialize the readout layer (W_out)."""
        states = self.transform(embeddings)
        targets = np.asarray(targets, dtype=np.float64)

        A = states.T @ states
        B = states.T @ targets
        regularizer = self.ridge * np.eye(self.reservoir_dim)

        # Solve linear system equations securely: (A + lambda*I) * W_out = B
        self.W_out = np.linalg.solve(A + regularizer, B)
        self.P = np.linalg.inv(A + regularizer)

    def predict_scores(self, embedding: np.ndarray) -> np.ndarray:
        """Calculates raw, unnormalized routing logits for a given input vector."""
        state = self._state(embedding)
        return state @ self.W_out

    @staticmethod
    def softmax(scores: np.ndarray) -> np.ndarray:
        """Applies stable Softmax activation over logs with mathematical overflow protection."""
        scores = scores - np.max(scores)  # Stabilize by offsetting max logit
        exp_scores = np.exp(scores)
        return exp_scores / np.sum(exp_scores)

    def route(self, embedding: np.ndarray) -> tuple:
        """Executes the confidence-based dynamic routing assignment.

        Returns
        -------
        tuple
            (selected_route, confidence, probabilities)
            - selected_route (int): Index of chosen backend lane. Returns `-1`
              if confidence drops below threshold (System 2 Escalation).
            - confidence (float): Peak Softmax probability matching the chosen route.
            - probabilities (np.ndarray): Full probability distribution across lanes.
        """
        scores = self.predict_scores(embedding)
        probabilities = self.softmax(scores)

        route = int(np.argmax(probabilities))
        confidence = float(probabilities[route])

        # Confidence-based dynamic fallback loop to System 2
        if confidence < self.fallback_threshold:
            route = -1

        return route, confidence, probabilities

    def add_route(self) -> int:
        """Appends a new output routing lane to the readout layer with zero downtime.

        Allows instant scaling for newly added specialized models (Experts) under O(1).

        Returns
        -------
        int
            The newly assigned route lane index.
        """
        self.W_out = np.hstack([self.W_out, np.zeros((self.reservoir_dim, 1), dtype=np.float64)])
        self.output_dim += 1
        return self.output_dim - 1

    def rls_update(self, embedding: np.ndarray, target: np.ndarray, forgetting_factor: float = 0.98):
        """Applies Recursive Least Squares (RLS) tracking to update weights online.

        Parameters
        ----------
        embedding : np.ndarray
            Semantic embedding vector of the processed query.
        target : np.ndarray
            Target vector representing idealized optimal lane weights.
        forgetting_factor : float
            Exponential forgetting memory weights factor (0.9 <= forgetting_factor <= 1.0).
        """
        state = self._state(embedding).reshape(-1, 1)
        target = np.asarray(target, dtype=np.float64).reshape(1, -1)

        if target.shape != (self.output_dim,):
   　　　 raise ValueError( f"Target dimension {target.shape} does not match output_dim {self.output_dim}")

        P_state = self.P @ state
        denominator = forgetting_factor + (state.T @ P_state)
        K = P_state / denominator  # Kalman gain vector

        prediction = state.T @ self.W_out
        error = target - prediction

        # Online iterative adaptation of readout matrix and error covariance
        self.W_out += K @ error
        self.P = (self.P - K @ state.T @ self.P) / forgetting_factor
