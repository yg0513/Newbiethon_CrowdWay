import networkx as nx
import pytest
from app.utils.geo import great_circle_distance

@pytest.fixture
def graph():
    g = nx.MultiDiGraph(crs='EPSG:4326')
    for node, x, y in [(1, 126.924, 37.521), (2, 126.925, 37.521),
                       (3, 126.925, 37.5215), (4, 126.926, 37.521)]:
        g.add_node(node, x=x, y=y)
    for u, v, length in [(1, 2, 100), (2, 4, 100), (1, 3, 120), (3, 4, 120)]:
        g.add_edge(u, v, length=length, congestion=0.0)
    return g
