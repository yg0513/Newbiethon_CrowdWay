import json
import httpx
import pytest
from shapely.geometry import box, mapping
from app.config import Settings
from app.congestion.provider import CongestionProvider
from app.congestion.seoul_provider import adapt_seoul_response, load_seoul_zones

def test_adapter():
    zone = adapt_seoul_response({'SeoulRtd.citydata_ppltn': [{'AREA_CONGEST_LVL': '붐빔'}]}, 'a', box(0, 0, 1, 1))
    assert zone.score == 1
    with pytest.raises(ValueError):
        adapt_seoul_response({'RESULT': {'CODE': 'ERROR-300'}}, 'a', box(0, 0, 1, 1))

@pytest.mark.parametrize('fallback', ['mock', 'empty'])
def test_fallback(fallback):
    provider = CongestionProvider(Settings(use_mock_congestion=False, congestion_fallback=fallback))
    snapshot = provider.get_snapshot()
    assert snapshot.source == f'fallback_{fallback}'
    assert snapshot.warnings
    assert bool(snapshot.zones) == (fallback == 'mock')

def test_ttl(monkeypatch):
    import app.congestion.mock_provider as mock
    calls = []
    monkeypatch.setattr(mock, 'get_mock_zones', lambda: calls.append(1) or [])
    provider = CongestionProvider(Settings())
    assert provider.get_snapshot() is provider.get_snapshot()
    assert len(calls) == 1
    provider._expires = 0
    provider.get_snapshot()
    assert len(calls) == 2

def test_seoul_http_adapter(tmp_path, monkeypatch):
    path = tmp_path / 'zones.geojson'
    path.write_text(json.dumps({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'name': 'zone', 'area_code': 'POI001'}, 'geometry': mapping(box(126.92, 37.52, 126.93, 37.53))}]}))
    original_client = httpx.Client
    def handler(request):
        assert request.url.path.endswith('/citydata_ppltn/1/5/POI001')
        return httpx.Response(200, json={'SeoulRtd.citydata_ppltn': [{'AREA_CONGEST_LVL': '보통', 'AREA_CD': 'POI001', 'PPLTN_TIME': __import__('datetime').datetime.now(__import__('zoneinfo').ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M')}]})
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs))
    zones = load_seoul_zones(Settings(seoul_api_key='test', seoul_zones_file=str(path)))
    assert zones[0].score == .3
