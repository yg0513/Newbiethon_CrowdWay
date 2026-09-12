import httpx
import pytest
from app.config import Settings
from app.places.search import PlaceSearch

def test_seoul_region_search():
    p=PlaceSearch(Settings())
    data=p.search('강남역')
    assert any(x['id']=='POI014' for x in data['results'])
    assert '대표 위치' in data['results'][0]['address']
    assert p.search('강남역') is data
    assert p.search('존재하지않는지역1234')['results']==[]

def test_kakao_adapter_and_bounds(monkeypatch):
    original=httpx.Client
    def respond(request):
        assert request.headers['Authorization']=='KakaoAK testing'
        return httpx.Response(200,json={'documents':[{'id':'1','place_name':'강남역','address_name':'서울 강남구','x':'127.027','y':'37.498'},{'id':'2','place_name':'부산','x':'129','y':'35'}]})
    monkeypatch.setattr(httpx,'Client',lambda **kw:original(transport=httpx.MockTransport(respond),**kw))
    data=PlaceSearch(Settings(kakao_rest_api_key='testing')).search('강남역')
    assert data['results'][0]['id']=='kakao-1'
    assert not any(r['id']=='kakao-2' for r in data['results'])

def test_kakao_failure_preserves_local(monkeypatch):
    original=httpx.Client
    monkeypatch.setattr(httpx,'Client',lambda **kw:original(transport=httpx.MockTransport(lambda r:httpx.Response(401)),**kw))
    data=PlaceSearch(Settings(kakao_rest_api_key='do-not-expose')).search('강남역')
    assert data['results'] and data['warning']
    assert 'do-not-expose' not in str(data)

@pytest.mark.parametrize('query',['','a','   ','가'*101])
def test_invalid(query):
    with pytest.raises(ValueError):PlaceSearch(Settings()).search(query)
