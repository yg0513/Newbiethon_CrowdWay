"""Project once into meters, then query only nearby polygons using STRtree."""
import geopandas as gpd
import networkx as nx
from shapely.strtree import STRtree
from shapely.geometry import LineString
from app.congestion.provider import CongestionZone
from app.utils.geo import edge_geometry

def calculate_edge_congestion(line: LineString, zones: list[CongestionZone]) -> float:
    """Inputs must share a metric CRS. Max influence avoids double counting."""
    if line.length == 0:
        return 0.0
    return min(1.0, max((line.intersection(z.geometry).length / line.length * z.score for z in zones), default=0.0))

def map_congestion(graph: nx.MultiDiGraph, zones: tuple[CongestionZone, ...] | list[CongestionZone], threshold: float = 0.7) -> nx.MultiDiGraph:
    """Return a request-local graph so concurrent preferences never mutate cache."""
    result = graph.copy()
    edges = list(result.edges(keys=True, data=True))
    if not edges:
        return result
    lines = gpd.GeoSeries([edge_geometry(result, u, v, d) for u, v, _, d in edges], crs=result.graph['crs'])
    metric_crs = lines.estimate_utm_crs()
    projected = lines.to_crs(metric_crs)
    polygons = gpd.GeoSeries([z.geometry for z in zones], crs='EPSG:4326').to_crs(metric_crs) if zones else []
    tree = STRtree(list(polygons))
    for (u, v, key, data), original, line in zip(edges, lines, projected):
        score = 0.0
        high_zones = set()
        for index in tree.query(line, predicate='intersects'):
            overlap = line.intersection(polygons.iloc[index]).length
            if overlap <= 1e-8 or line.length == 0:
                continue
            score = max(score, overlap / line.length * zones[index].score)
            if zones[index].score >= threshold:
                high_zones.add(zones[index].name)
        data['geometry'] = original
        data['congestion'] = min(1.0, max(0.0, score))
        data['high_congestion_zones'] = high_zones
    return result
