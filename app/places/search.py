"""Official Seoul area search, optionally enriched by Kakao Local place/address search."""
from collections import OrderedDict
from threading import Lock
from time import monotonic
import httpx
from app.config import Settings
from app.congestion.seoul_provider import get_boundaries

class PlaceSearchError(RuntimeError):
    pass

class PlaceSearch:
    def __init__(self, config: Settings):
        self.config = config
        self._lock = Lock()
        self._cache = OrderedDict()

    def search(self, query: str) -> dict:
        query = ' '.join(query.split())
        if not 2 <= len(query) <= 100: raise ValueError('검색어를 2~100자로 입력하세요.')
        with self._lock:
            cached = self._cache.get(query)
            if cached and monotonic() < cached[0]:
                self._cache.move_to_end(query)
                return cached[1]
            results = []
            normalized = query.replace(' ','').casefold()
            for zone in get_boundaries(self.config):
                if normalized in zone['name'].replace(' ','').casefold():
                    point = zone['geometry'].representative_point()
                    results.append({'id':zone['area_code'],'name':zone['name'],
                        'address':'서울시 공식 관측지역 · 대표 위치 (지도에서 조정 가능)',
                        'position':{'lat':point.y,'lng':point.x}, 'source':'seoul_area'})
            warning = None
            if self.config.kakao_rest_api_key:
                try:
                    with httpx.Client(timeout=12,headers={'Authorization':f'KakaoAK {self.config.kakao_rest_api_key}'}) as client:
                        r = client.get('https://dapi.kakao.com/v2/local/search/keyword.json',params={'query':query,'rect':'126.70,37.35,127.25,37.75','size':8})
                        r.raise_for_status()
                        documents = r.json()['documents']
                        if not documents:
                            r = client.get('https://dapi.kakao.com/v2/local/search/address.json',params={'query':query,'size':8})
                            r.raise_for_status(); documents = r.json()['documents']
                        external = []
                        for i, row in enumerate(documents):
                            lat,lon = float(row['y']),float(row['x'])
                            if not (37.35<=lat<=37.75 and 126.70<=lon<=127.25):continue
                            external.append({'id':'kakao-'+str(row.get('id',i)), 'name':row.get('place_name') or row['address_name'],
                                'address':row.get('road_address_name') or row.get('address_name',''),
                                'position':{'lat':lat,'lng':lon},'source':'kakao'})
                        results = external + results
                except (httpx.HTTPError, ValueError, KeyError, TypeError):
                    warning = '상세 장소 검색에 실패했습니다. 카카오 키와 Local API 사용 설정을 확인하세요. 공식 관측지역 검색과 지도 선택은 사용할 수 있습니다.'
            else:
                warning = '현재는 서울시 121개 관측지역 이름을 검색합니다. 상세 상호·주소 검색은 카카오 키 연결 후 사용할 수 있습니다.'
            data = {'results':results[:12],'warning':warning,'attribution':'서울특별시 · Kakao' if self.config.kakao_rest_api_key else '서울특별시 공식 장소 영역', 'scope':'서울 및 인접 지역'}
            self._cache[query] = (monotonic()+(60 if warning else 3600),data)
            while len(self._cache)>256:self._cache.popitem(last=False)
            return data
