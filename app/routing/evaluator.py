import networkx as nx
from app.models.response import RouteMetrics, RouteSegment, Comparison
from app.routing.router import EdgeRoute
from app.utils.geo import edge_geometry


def evaluate_route(graph: nx.MultiDiGraph, route: EdgeRoute, walking_speed_kmh: float = 4.5, threshold: float = 0.7) -> RouteMetrics:
    """Length-weighted metrics use exactly the edge keys chosen by the router."""
    distance = exposure = congested = maximum = 0.0
    zones: set[str] = set()
    coordinates: list[tuple[float, float]] = []
    segments: list[RouteSegment] = []

    for u, v, key in route.edges:
        data = graph[u][v][key]
        length, score = float(data['length']), float(data.get('congestion', 0))
        distance += length
        exposure += length * score
        maximum = max(maximum, score)
        if score >= threshold:
            congested += length
        zones.update(data.get('high_congestion_zones', set()))

        points = [(float(p[0]), float(p[1])) for p in edge_geometry(graph, u, v, data).coords]
        origin = graph.nodes[u]
        if ((points[-1][0] - origin['x']) ** 2 + (points[-1][1] - origin['y']) ** 2 <
                (points[0][0] - origin['x']) ** 2 + (points[0][1] - origin['y']) ** 2):
            points.reverse()

        if coordinates and coordinates[-1] == points[0]:
            coordinates.extend(points[1:])
        else:
            coordinates.extend(points)

        if len(points) >= 2:
            segments.append(RouteSegment(congestion=score, geometry=points))

    if not coordinates:
        node = graph.nodes[route.nodes[0]]
        coordinates = [(node['x'], node['y'])] * 2

    return RouteMetrics(
        distance_m=distance,
        estimated_time_min=distance / (walking_speed_kmh * 1000 / 60),
        average_congestion=exposure / distance if distance else 0,
        max_congestion=maximum,
        congested_distance_m=congested,
        high_congestion_zone_count=len(zones),
        congestion_exposure_m=exposure,
        geometry=coordinates,
        segments=segments,
    )


def compare_routes(shortest: RouteMetrics, recommended: RouteMetrics) -> Comparison:
    extra = recommended.distance_m - shortest.distance_m
    exposure = shortest.congestion_exposure_m
    return Comparison(
        extra_distance_m=extra,
        extra_distance_percent=extra / shortest.distance_m * 100 if shortest.distance_m else 0,
        extra_time_min=recommended.estimated_time_min - shortest.estimated_time_min,
        congestion_reduction_percent=(exposure - recommended.congestion_exposure_m) / exposure * 100 if exposure else 0,
    )
