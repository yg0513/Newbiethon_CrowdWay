from math import asin, cos, radians, sin, sqrt
import networkx as nx
from shapely.geometry import LineString

def great_circle_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Spherical distance in meters, using OSMnx's earth radius."""
    p1, p2 = radians(lat1), radians(lat2)
    a = sin((p2-p1)/2)**2 + cos(p1)*cos(p2)*sin(radians(lon2-lon1)/2)**2
    return 2 * 6371009 * asin(sqrt(min(1.0, max(0.0, a))))

def edge_geometry(graph: nx.MultiDiGraph, u: int, v: int, data: dict) -> LineString:
    geometry = data.get('geometry')
    if geometry is None or geometry.is_empty:
        geometry = LineString([(graph.nodes[u]['x'], graph.nodes[u]['y']),
                               (graph.nodes[v]['x'], graph.nodes[v]['y'])])
    if not isinstance(geometry, LineString):
        raise ValueError('도로 geometry는 LineString이어야 합니다.')
    return geometry
