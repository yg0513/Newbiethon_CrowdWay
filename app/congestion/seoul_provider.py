"""Official population JSON / citydata XML adapters, joined by official area code."""
import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo
import httpx
from shapely.geometry import shape, box
from app.config import ROOT, Settings
from app.congestion.provider import CongestionZone, LEVELS, normalize_congestion

class SeoulDataError(ValueError):
    """Safe diagnostic: never include a request URL or API key."""

@lru_cache(maxsize=4)
def read_boundaries(filename: str, modified: int) -> tuple[dict, ...]:
    data = json.loads(Path(filename).read_text(encoding='utf-8'))
    if data.get('type') != 'FeatureCollection' or not data.get('features'):
        raise SeoulDataError('공식 장소 경계 FeatureCollection이 필요합니다.')
    features = []
    for feature in data['features']:
        props = feature['properties']
        geometry = shape(feature['geometry'])
        CongestionZone(props['name'], 0, geometry)
        if not (126 < geometry.bounds[0] < geometry.bounds[2] < 128 and 37 < geometry.bounds[1] < geometry.bounds[3] < 38):
            raise SeoulDataError('경계 좌표계는 서울 지역의 EPSG:4326이어야 합니다.')
        features.append({'name': props['name'], 'area_code': props.get('area_code'), 'geometry': geometry})
    return tuple(features)

def get_boundaries(config: Settings, bounds: tuple | None = None) -> list[dict]:
    path = Path(config.seoul_zones_file)
    if not path.is_absolute(): path = ROOT / path
    try:
        features = read_boundaries(str(path.resolve()), path.stat().st_mtime_ns)
    except OSError as exc:
        raise SeoulDataError('SEOUL_ZONES_FILE 경계 파일을 확인하세요.') from exc
    selected = {code.strip() for code in config.seoul_area_codes.split(',') if code.strip()}
    candidates = [f for f in features if not selected or f['area_code'] in selected]
    region = box(*bounds) if bounds else None
    if region is None:
        return candidates

    nearby = [f for f in candidates if f['geometry'].intersects(region)]
    # The UI shows up to five route-nearby crowding spots. If the graph bounds
    # touch fewer official areas, fill the list with the geographically nearest
    # official areas rather than querying all 121 places.
    if not selected and len(nearby) < 5:
        seen = {f['area_code'] or f['name'] for f in nearby}
        for feature in sorted(candidates, key=lambda f: f['geometry'].distance(region)):
            key = feature['area_code'] or feature['name']
            if key in seen:
                continue
            nearby.append(feature)
            seen.add(key)
            if len(nearby) >= 5:
                break
    return nearby

def _population_row(payload: dict | str) -> dict:
    if isinstance(payload, str):
        if '<!DOCTYPE' in payload.upper() or '<!ENTITY' in payload.upper():
            raise SeoulDataError('지원하지 않는 XML 선언입니다.')
        try: root = ET.fromstring(payload)
        except ET.ParseError as exc: raise SeoulDataError('서울시 XML 응답을 해석할 수 없습니다.') from exc
        code = root.findtext('.//RESULT.CODE') or root.findtext('.//CODE')
        if code and code != 'INFO-000': raise SeoulDataError(f'서울시 API 오류: {code[:30]}')
        rows = [e for e in root.iter('LIVE_PPLTN_STTS') if e.find('AREA_CONGEST_LVL') is not None]
        if not rows: raise SeoulDataError('도시데이터 응답에 실시간 인구 항목이 없습니다.')
        return {e.tag: e.text for e in rows[0]}
    result = payload.get('RESULT', {})
    if result and (result.get('RESULT.CODE') or result.get('CODE')) != 'INFO-000':
        raise SeoulDataError('서울시 API 인증/요청 오류입니다. API 키와 서비스 승인을 확인하세요.')
    rows = payload.get('SeoulRtd.citydata_ppltn')
    if isinstance(rows, dict): rows = rows.get('row')
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise SeoulDataError('지원하지 않는 서울시 인구 응답 구조입니다.')
    return rows[0]

def adapt_seoul_response(payload: dict | str, name: str, geometry, expected_area_code: str | None = None) -> CongestionZone:
    row = _population_row(payload)
    if expected_area_code and row.get('AREA_CD') != expected_area_code:
        raise SeoulDataError('요청한 장소와 응답 장소 코드가 다릅니다. sample 키는 광화문·덕수궁만 지원합니다.')
    level = row.get('AREA_CONGEST_LVL')
    if level not in LEVELS:
        raise SeoulDataError('서울시 혼잡도 값이 없거나 알려지지 않은 값입니다.')
    def optional_int(value):
        try:
            return int(float(str(value).replace(',', '').strip())) if value not in (None, '') else None
        except (TypeError, ValueError):
            return None

    return CongestionZone(name, normalize_congestion(level), geometry, level,
        area_code=row.get('AREA_CD'), observed_at=row.get('PPLTN_TIME'),
        message=row.get('AREA_CONGEST_MSG'), replaced=row.get('REPLACE_YN') == 'Y',
        population_min=optional_int(row.get('AREA_PPLTN_MIN')),
        population_max=optional_int(row.get('AREA_PPLTN_MAX')))

def load_seoul_zones(config: Settings, bounds: tuple | None = None) -> list[CongestionZone]:
    if not config.seoul_api_key.strip(): raise SeoulDataError('SEOUL_API_KEY가 없습니다. 프로젝트 .env에 발급받은 키를 입력하고 서버를 재시작하세요.')
    features = get_boundaries(config, bounds)
    if config.seoul_api_key == 'sample' and any(f['area_code'] != 'POI009' for f in features):
        raise SeoulDataError('sample 키는 광화문·덕수궁(POI009)만 지원합니다. 여의도에는 발급받은 키가 필요합니다.')
    zones = []
    service = config.seoul_api_service
    fmt = 'json' if service == 'citydata_ppltn' else 'xml'
    with httpx.Client(timeout=config.api_timeout_seconds) as client:
        for feature in features:
            area = feature['area_code'] or feature['name']
            url = f'{config.seoul_api_base_url.rstrip("/")}/{quote(config.seoul_api_key, safe="")}/{fmt}/{service}/1/5/{quote(area, safe="")}'
            try:
                response = client.get(url)
                response.raise_for_status()
                # Some API errors arrive as XML even when JSON was requested.
                payload = response.text if response.text.lstrip().startswith('<') else response.json()
                zone = adapt_seoul_response(payload, feature['name'], feature['geometry'], feature['area_code'])
            except httpx.HTTPError as exc:
                raise SeoulDataError('서울시 서버 통신에 실패했습니다. 네트워크와 API 주소를 확인하세요.') from exc
            if not zone.observed_at: raise SeoulDataError('서울시 데이터의 관측 시각이 없습니다.')
            try:
                observed = datetime.strptime(zone.observed_at, '%Y-%m-%d %H:%M').replace(tzinfo=ZoneInfo('Asia/Seoul'))
            except ValueError as exc: raise SeoulDataError('서울시 관측 시각 형식이 올바르지 않습니다.') from exc
            age = (datetime.now(ZoneInfo('Asia/Seoul')) - observed).total_seconds() / 60
            if age > config.seoul_max_age_minutes or age < -5:
                raise SeoulDataError('서울시 관측 데이터가 오래되었거나 관측 시각이 올바르지 않습니다.')
            zones.append(zone)
    return zones
