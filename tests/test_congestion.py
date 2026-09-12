import pytest
from shapely.geometry import box, LineString, MultiPolygon
from app.congestion.provider import normalize_congestion, CongestionZone
from app.congestion.mapper import calculate_edge_congestion, map_congestion

@pytest.mark.parametrize('level, score', [('여유', 0), ('보통', .3), ('약간 붐빔', .7), ('붐빔', 1), ('오류', .3), (None, .3)])
def test_normalize(level, score):
    assert normalize_congestion(level) == score

@pytest.mark.parametrize('polygon, expected', [(box(20, 20, 30, 30), 0), (box(-1, -1, 11, 1), .8), (box(0, -1, 4, 1), .32)])
def test_overlap(polygon, expected):
    assert calculate_edge_congestion(LineString([(0, 0), (10, 0)]), [CongestionZone('zone', .8, polygon)]) == pytest.approx(expected)

def test_overlapping_zones_max():
    zones = [CongestionZone('a', .7, box(-1, -1, 11, 1)), CongestionZone('b', 1, box(0, -1, 5, 1))]
    assert calculate_edge_congestion(LineString([(0, 0), (10, 0)]), zones) == pytest.approx(.7)

def test_mapper_missing_geometry_and_no_mutation(graph):
    zones = [CongestionZone('high', 1, box(126.923, 37.5209, 126.9255, 37.5211))]
    mapped = map_congestion(graph, zones)
    assert mapped[1][2][0]['congestion'] == pytest.approx(1)
    assert 'geometry' in mapped[1][2][0]
    assert graph[1][2][0]['congestion'] == 0
    assert 'geometry' not in graph[1][2][0]

def test_empty_and_multipolygon(graph):
    assert all(d['congestion'] == 0 for *_, d in map_congestion(graph, []).edges(data=True))
    zone = CongestionZone('multi', 1, MultiPolygon([box(126.923, 37.520, 126.927, 37.522)]))
    assert map_congestion(graph, [zone])[1][2][0]['congestion'] == pytest.approx(1)
