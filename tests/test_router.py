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


def test_add_route_expands_readout_without_changing_reservoir():
    router = make_router()

    original_w_res = router.W_res.copy()
    original_output_dim = router.output_dim

    new_route = router.add_route()

    assert new_route == original_output_dim
    assert router.output_dim == original_output_dim + 1
    assert router.W_out.shape == (8, original_output_dim + 1)
    assert np.array_equal(router.W_res, original_w_res)
    assert np.all(router.W_out[:, -1] == 0.0)


def test_route_returns_valid_route_and_confidence():
    router = make_router()
    embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64)

    route, confidence = router.route(embedding)


    def test_route_works_after_adding_route():
    router = make_router()
    embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64)

    new_route = router.add_route()

    route, confidence = router.route(embedding)

    assert route in range(router.output_dim)
    assert 0 <= route <= new_route
    assert 0.0 <= confidence <= 1.0

    assert route in range(router.output_dim)
    assert 0.0 <= confidence <= 1.0



def test_rls_update_does_not_change_reservoir():
    router = make_router()

    embedding = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64)
    target = np.array([1.0, 0.0, 0.0], dtype=np.float64)

    original_w_res = router.W_res.copy()
    original_w_out = router.W_out.copy()

    router.rls_update(embedding, target)

    assert np.array_equal(router.W_res, original_w_res)
    assert not np.array_equal(router.W_out, original_w_out)


def test_route_rejects_wrong_input_dimension():
    router = make_router()
    embedding = np.array([0.1, 0.2, 0.3], dtype=np.float64)

    with pytest.raises(ValueError, match="Input dimension mismatch"):
        router.route(embedding)
