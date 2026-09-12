import pytest
from app.routing.cost import calculate_edge_cost

def test_cost_increases():
    assert calculate_edge_cost(100, 0, 3) < calculate_edge_cost(100, .5, 3) < calculate_edge_cost(100, 1, 3)

@pytest.mark.parametrize('congestion', [0, .3, .5, 1])
def test_fastest(congestion):
    assert calculate_edge_cost(100, congestion, 0) == 100

@pytest.mark.parametrize('args', [(-1, 0, 1), (1, -1, 1), (1, 2, 1), (1, 0, -1), (float('nan'), 0, 1)])
def test_invalid(args):
    with pytest.raises(ValueError):
        calculate_edge_cost(*args)
