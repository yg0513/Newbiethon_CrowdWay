import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import httpx
import pytest
from shapely.geometry import box
from app.config import Settings, ROOT
from app.congestion.provider import CongestionProvider
from app.congestion.seoul_provider import adapt_seoul_response, get_boundaries, load_seoul_zones, SeoulDataError

@pytest.mark.parametrize('filename', ['seoul_population_sample.json','seoul_city_sample.xml'])
def test_captured_official_sample(filename):
    text = (ROOT / 'tests/fixtures' / filename).read_text()
    payload = json.loads(text) if filename.endswith('json') else text
    zone = adapt_seoul_response(payload, '광화문·덕수궁', box(126.97,37.56,126.98,37.58), 'POI009')
    assert zone.area_code == 'POI009' and zone.observed_at
    assert 0 <= zone.score <= 1
    with pytest.raises(SeoulDataError): adapt_seoul_response(payload, '여의도한강공원', zone.geometry, 'POI105')

def test_official_boundaries_and_region_filter():
    all_zones = get_boundaries(Settings())
    assert len(all_zones) == 121
    assert all(z['geometry'].is_valid for z in all_zones)
    local = get_boundaries(Settings(), (126.92,37.52,126.94,37.54))
    assert 0 < len(local) < 121
    assert any(z['area_code']=='POI105' for z in local)

def test_api_key_missing_and_not_exposed():
    snapshot = CongestionProvider(Settings(use_mock_congestion=False)).get_snapshot()
    assert snapshot.source == 'fallback_empty'
    assert 'SEOUL_API_KEY' in snapshot.warnings[0]
    assert 'secret-value' not in repr(Settings(seoul_api_key='secret-value'))

def test_sample_wrong_region_rejected():
    with pytest.raises(SeoulDataError, match='sample'):
        load_seoul_zones(Settings(seoul_api_key='sample'),(126.92,37.52,126.94,37.54))

@pytest.mark.parametrize('observed', ['2000-01-01 00:00', None])
def test_stale_or_missing_timestamp(monkeypatch, observed):
    original = httpx.Client
    transport = httpx.MockTransport(lambda request: httpx.Response(200,json={'SeoulRtd.citydata_ppltn':[{'AREA_CD':'POI105','AREA_CONGEST_LVL':'붐빔','PPLTN_TIME':observed}]}))
    monkeypatch.setattr(httpx,'Client',lambda **kw: original(transport=transport,**kw))
    with pytest.raises(SeoulDataError):load_seoul_zones(Settings(seoul_api_key='test',seoul_area_codes='POI105'))

def test_region_cache_isolation(monkeypatch):
    import app.congestion.seoul_provider as module
    calls=[]
    monkeypatch.setattr(module,'load_seoul_zones',lambda config,bounds: calls.append(bounds) or [])
    p=CongestionProvider(Settings(use_mock_congestion=False,seoul_api_key='test'))
    a=(126.92,37.52,126.94,37.54);b=(126.97,37.56,126.99,37.58)
    p.get_snapshot(a);p.get_snapshot(b);p.get_snapshot(a)
    assert calls == [a,b]

def test_population_range_is_preserved_for_ui():
    payload = {'SeoulRtd.citydata_ppltn': [{
        'AREA_CD': 'POI105',
        'AREA_CONGEST_LVL': '약간 붐빔',
        'AREA_PPLTN_MIN': '16000',
        'AREA_PPLTN_MAX': '18000',
        'PPLTN_TIME': '2026-09-12 18:10',
    }]}
    zone = adapt_seoul_response(payload, '여의도한강공원', box(126.92, 37.52, 126.94, 37.54), 'POI105')
    assert zone.population_min == 16000
    assert zone.population_max == 18000
