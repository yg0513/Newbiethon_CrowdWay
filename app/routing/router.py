"""A* with explicit parallel-edge resolution and bounded alpha fallback."""
from dataclasses import dataclass
import networkx as nx
from app.config import ALPHAS
from app.routing.cost import calculate_edge_cost
from app.utils.geo import great_circle_distance

@dataclass
class EdgeRoute:
    nodes: list[int]
    edges: list[tuple[int, int, int]]
    alpha: float
    distance_m: float


def find_route(graph: nx.MultiDiGraph, start: int, end: int, alpha: float) -> EdgeRoute:
    def cost(data: dict) -> float:
        return calculate_edge_cost(float(data['length']), data.get('congestion', 0.0), alpha)

    # Same selected edge drives both A* weight and final route metrics/geometry.
    selected = {(u, v): min(choices, key=lambda k: cost(choices[k]))
                for u in graph for v, choices in graph[u].items()}
    def weight(u, v, choices):
        return cost(choices[selected[u, v]])

    # OSM lengths can be rounded or fixtures can use arbitrary lengths. Scale the
    # straight-line lower bound down to preserve admissibility for every edge.
    scale = 1.0
    for u, v, data in graph.edges(data=True):
        a, b = graph.nodes[u], graph.nodes[v]
        straight = great_circle_distance(a['y'], a['x'], b['y'], b['x'])
        if straight > 0:
            scale = min(scale, float(data['length']) / straight)
    def heuristic(u, v):
        a, b = graph.nodes[u], graph.nodes[v]
        return scale * great_circle_distance(a['y'], a['x'], b['y'], b['x'])

    nodes = nx.astar_path(graph, start, end, heuristic=heuristic, weight=weight)
    edges = [(u, v, selected[u, v]) for u, v in zip(nodes, nodes[1:])]
    return EdgeRoute(nodes, edges, alpha, sum(float(graph[u][v][k]['length']) for u, v, k in edges))


def calculate_routes(graph: nx.MultiDiGraph, start: int, end: int, preference: str, max_detour_ratio: float = 1.30) -> tuple[EdgeRoute, EdgeRoute]:
    if max_detour_ratio < 1:
        raise ValueError('우회 비율은 1 이상이어야 합니다.')
    shortest = find_route(graph, start, end, 0.0)
    alpha = ALPHAS[preference]
    candidates = [a for a in (3.0, 2.0, 1.0) if a <= alpha]
    for candidate in candidates:
        route = find_route(graph, start, end, candidate)
        if route.distance_m <= shortest.distance_m * max_detour_ratio + 1e-8:
            return shortest, route
    return shortest, shortest
