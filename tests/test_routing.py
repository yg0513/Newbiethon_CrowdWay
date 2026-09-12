import networkx as nx
import pytest
from shapely.geometry import LineString
from app.routing.router import calculate_routes, find_route
from app.routing.evaluator import evaluate_route, compare_routes

def test_no_congestion(graph):
    shortest, recommended = calculate_routes(graph, 1, 4, 'comfortable')
    assert shortest.edges == recommended.edges

def test_avoid_and_detour(graph):
    graph[1][2][0]['congestion'] = graph[2][4][0]['congestion'] = 1
    shortest, recommended = calculate_routes(graph, 1, 4, 'comfortable')
    assert shortest.nodes == [1, 2, 4]
    assert recommended.nodes == [1, 3, 4]
    assert recommended.distance_m <= shortest.distance_m * 1.30
    comparison = compare_routes(evaluate_route(graph, shortest), evaluate_route(graph, recommended))
    assert comparison.extra_distance_m == 40
    assert comparison.congestion_reduction_percent == 100

def test_detour_fallback(graph):
    graph[1][2][0]['congestion'] = graph[2][4][0]['congestion'] = 1
    graph[1][3][0]['length'] = graph[3][4][0]['length'] = 200
    shortest, recommended = calculate_routes(graph, 1, 4, 'comfortable')
    assert shortest.edges == recommended.edges
    assert recommended.alpha <= 1

def test_alpha_decreases(graph):
    graph[1][2][0]['congestion'] = graph[2][4][0]['congestion'] = .5
    graph[1][3][0]['length'] = graph[3][4][0]['length'] = 160
    _, recommended = calculate_routes(graph, 1, 4, 'comfortable')
    assert recommended.alpha == 2
    assert recommended.nodes == [1, 2, 4]

def test_parallel_edge_geometry(graph):
    graph[1][2][0]['congestion'] = 1
    geometry = LineString([(126.925, 37.521), (126.9245, 37.5211), (126.924, 37.521)])
    key = graph.add_edge(1, 2, length=110, congestion=0, geometry=geometry)
    shortest, recommended = calculate_routes(graph, 1, 4, 'comfortable')
    assert shortest.edges[0][2] == 0
    assert recommended.edges[0][2] == key
    result = evaluate_route(graph, recommended)
    assert result.distance_m == 210
    assert result.geometry[0] == (126.924, 37.521)
    assert (126.9245, 37.5211) in result.geometry

def test_same_node_and_zero_exposure(graph):
    a, b = calculate_routes(graph, 1, 1, 'comfortable')
    result = evaluate_route(graph, a)
    assert result.distance_m == 0
    assert len(result.geometry) == 2
    assert compare_routes(result, evaluate_route(graph, b)).congestion_reduction_percent == 0

def test_disconnected(graph):
    with pytest.raises(nx.NetworkXNoPath):
        find_route(graph, 4, 1, 3)

def test_metrics_weighted_and_distinct_zone(graph):
    graph[1][2][0].update(congestion=.8, high_congestion_zones={'a'})
    graph[2][4][0].update(congestion=.2, high_congestion_zones={'a', 'b'})
    route = find_route(graph, 1, 4, 0)
    result = evaluate_route(graph, route)
    assert result.average_congestion == .5
    assert result.max_congestion == .8
    assert result.congested_distance_m == 100
    assert result.high_congestion_zone_count == 2
    assert result.estimated_time_min == pytest.approx(200 / 75)

def test_astar_matches_dijkstra(graph):
    graph.add_edge(1, 4, length=1, congestion=0)
    assert find_route(graph, 1, 4, 3).distance_m == nx.shortest_path_length(graph, 1, 4, weight='length')
