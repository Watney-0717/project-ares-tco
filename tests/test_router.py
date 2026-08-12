python#

import numpy as np
import pytest

from src.router import RCRouter


def make_router():
    return RCRouter(
        input_dim=4,
        reservoir_dim=8,
        output_dim=3,
        seed=42,
    )


def test_state_accepts_correct_input_dimension():
    router = make_router()
    embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64)

    state = router._state(embedding)

    assert state.shape == (8,)


def test_state_rejects_wrong_input_dimension():
    router = make_router()
    embedding = np.array([0.1, 0.2, 0.3], dtype=np.float64)

    with pytest.raises(ValueError, match="Input dimension mismatch"):
        router._state(embedding)


def test_rls_update_accepts_correct_target_dimension():
    router = make_router()
    embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64)
    target = np.array([1.0, 0.0, 0.0], dtype=np.float64)

    router.rls_update(embedding, target)


def test_rls_update_rejects_wrong_target_dimension():
    router = make_router()
    embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64)
    target = np.array([1.0, 0.0], dtype=np.float64)

    with pytest.raises(ValueError, match="Target dimension"):
        router.rls_update(embedding, target)
