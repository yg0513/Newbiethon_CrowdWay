"""Bounded LRU graph cache. Only raw topology is shared between requests."""
from collections import OrderedDict
from math import ceil, isfinite
from pathlib import Path
from threading import Lock
import networkx as nx
import osmnx as ox
from app.config import ROOT, Settings
from app.models.request import Coordinate
from app.utils.geo import great_circle_distance

class GraphUnavailable(RuntimeError):
    pass

class GraphService:
    def __init__(self, config: Settings):
        self.config = config
        self._cache: OrderedDict[tuple, nx.MultiDiGraph] = OrderedDict()
        self._lock = Lock()
        ox.settings.use_cache = True
        ox.settings.cache_folder = str(ROOT / 'cache' / 'osmnx')
        ox.settings.requests_timeout = config.osm_timeout_seconds

    def request_region(self, start: Coordinate, end: Coordinate) -> tuple[float, float, int]:
        # Seoul-focused MVP also bounds polar/antimeridian and oversized queries.
        for point in (start, end):
            if not (37.35 <= point.lat <= 37.75 and 126.70 <= point.lon <= 127.25):
                raise ValueError('MVP 지원 범위는 서울 및 인접 지역(위도 37.35~37.75, 경도 126.70~127.25)입니다.')
        lat = round((start.lat + end.lat) / 2, 2)
        lon = round((start.lon + end.lon) / 2, 2)
        furthest = max(great_circle_distance(lat, lon, p.lat, p.lon) for p in (start, end))
        radius = ceil(max(self.config.graph_min_radius_m, furthest + self.config.graph_buffer_m) / 500) * 500
        if radius > self.config.graph_max_radius_m:
            raise ValueError('요청 범위가 너무 큽니다. 출발지와 목적지를 더 가깝게 지정하세요.')
        return lat, lon, radius

    def get_graph(self, start: Coordinate, end: Coordinate) -> nx.MultiDiGraph:
        region = self.request_region(start, end)
        key = ('file', self.config.graphml_path) if self.config.graphml_path else region
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            try:
                if self.config.graphml_path:
                    path = Path(self.config.graphml_path)
                    graph = ox.load_graphml(path if path.is_absolute() else ROOT / path)
                else:
                    lat, lon, radius = region
                    graph = ox.graph_from_point((lat, lon), dist=radius, network_type='walk', retain_all=True)
                if not graph.nodes or not graph.edges:
                    raise ValueError('도보 그래프가 비어 있습니다.')
                if str(graph.graph.get('crs')).lower() not in ('epsg:4326', '4326'):
                    graph = ox.project_graph(graph, to_crs='EPSG:4326')
                for _, _, d in graph.edges(data=True):
                    if not isfinite(float(d['length'])) or float(d['length']) < 0:
                        raise ValueError('유효하지 않은 도로 길이입니다.')
            except Exception as exc:
                raise GraphUnavailable('OSM 도보 그래프를 불러오지 못했습니다. 네트워크 또는 GRAPHML_PATH를 확인하세요.') from exc
            self._cache[key] = graph
            while len(self._cache) > self.config.graph_cache_size:
                self._cache.popitem(last=False)
            return graph

    def snap(self, graph: nx.MultiDiGraph, point: Coordinate) -> tuple[int, float]:
        # STRtree nearest in a metric CRS avoids OSMnx's optional scipy/sklearn.
        import geopandas as gpd
        from shapely.geometry import Point
        from shapely.strtree import STRtree
        nodes = list(graph.nodes)
        points = gpd.GeoSeries([Point(graph.nodes[n]['x'], graph.nodes[n]['y']) for n in nodes], crs='EPSG:4326')
        metric_crs = points.estimate_utm_crs()
        projected = points.to_crs(metric_crs)
        target = gpd.GeoSeries([Point(point.lon, point.lat)], crs='EPSG:4326').to_crs(metric_crs).iloc[0]
        node = nodes[int(STRtree(list(projected)).nearest(target))]
        data = graph.nodes[node]
        distance = great_circle_distance(point.lat, point.lon, data['y'], data['x'])
        if distance > self.config.max_snap_distance_m:
            raise ValueError('가까운 도보 노드가 없습니다. 위치 또는 저장된 그래프 범위를 확인하세요.')
        return node, distance
