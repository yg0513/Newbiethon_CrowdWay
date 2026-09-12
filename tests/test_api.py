import pytest
from fastapi.testclient import TestClient
from app.main import app
import app.main as main
from app.routing.graph import GraphUnavailable, GraphService
from app.config import Settings
from app.models.request import Coordinate

PAYLOAD = {'start': {'lat': 37.521, 'lon': 126.924}, 'end': {'lat': 37.521, 'lon': 126.926}, 'preference': 'comfortable'}

def test_api_end_to_end_mock(graph, monkeypatch):
    monkeypatch.setattr(main.graph_service, 'get_graph', lambda *args: graph)
    # Real node snapping, provider, polygon mapping, routing and JSON serialization.
    with TestClient(app) as client:
        assert client.get('/health').status_code == 200
        response = client.post('/route', json=PAYLOAD)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['shortest']['distance_m'] == 200
    assert body['recommended']['distance_m'] <= 260
    assert body['metadata']['congestion_source'] == 'mock'
    assert body['shortest']['geometry'][0] == [126.924, 37.521]

def test_invalid_request():
    with TestClient(app) as client:
        assert client.post('/route', json={**PAYLOAD, 'preference': 'wrong'}).status_code == 422
        assert client.post('/route', json={**PAYLOAD, 'start': {'lat': 99, 'lon': 126}}).status_code == 422

def test_upstream_failure(monkeypatch):
    def fail(*args):
        raise GraphUnavailable('OSM unavailable')
    monkeypatch.setattr(main.graph_service, 'get_graph', fail)
    with TestClient(app) as client:
        assert client.post('/route', json=PAYLOAD).status_code == 503
        assert client.get('/health').status_code == 200

def test_dynamic_region_and_cache(graph, monkeypatch):
    import app.routing.graph as module
    calls = []
    monkeypatch.setattr(module.ox, 'graph_from_point', lambda *args, **kwargs: calls.append(kwargs) or graph)
    service = GraphService(Settings())
    start, end = Coordinate(lat=37.521, lon=126.924), Coordinate(lat=37.57, lon=126.98)
    assert service.request_region(start, end)[2] > 3000
    assert service.get_graph(start, end) is service.get_graph(start, end)
    assert len(calls) == 1
    assert calls[0]['network_type'] == 'walk'

def test_route_includes_exact_congestion_boundaries(graph, monkeypatch):
    from shapely.geometry import mapping
    from app.congestion.provider import CongestionProvider
    provider = CongestionProvider(Settings())
    monkeypatch.setattr(main, 'congestion_provider', provider)
    monkeypatch.setattr(main.graph_service, 'get_graph', lambda *args: graph)
    with TestClient(app) as client:
        body = client.post('/route', json=PAYLOAD).json()
    snapshot = provider.get_snapshot()
    assert len(body['congestion_zones']) == len(snapshot.zones)
    for feature, zone in zip(body['congestion_zones'], snapshot.zones):
        from shapely.geometry import shape
        assert shape(feature['geometry']).equals(zone.geometry)
        assert feature['properties']['score'] == zone.score


def test_website_deep_links_and_api_not_shadowed(tmp_path, monkeypatch):
    (tmp_path / 'index.html').write_text('<html><body>CrowdWay</body></html>')
    monkeypatch.setattr(main, 'FRONTEND_DIST', tmp_path)
    with TestClient(app) as client:
        for path in ['/', '/search', '/result']:
            response = client.get(path)
            assert response.status_code == 200
            assert 'text/html' in response.headers['content-type']
        assert client.get('/health').json() == {'status': 'ok'}
        assert client.post('/route', json={}).status_code == 422
        assert client.get('/does-not-exist').status_code == 404


@pytest.fixture(autouse=True)
def mock_provider_for_api_tests(monkeypatch):
    from app.congestion.provider import CongestionProvider
    monkeypatch.setattr(main, 'congestion_provider', CongestionProvider(Settings(use_mock_congestion=True)))
