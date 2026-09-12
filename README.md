> **지역 확장 업데이트**: 이제 `/search`에서 서울시 공식 지역 이름 검색과 지도 클릭으로 출발·도착지를 선택합니다. `GRAPHML_PATH`를 비워 서울 지역 그래프를 동적으로 가져옵니다. [검색 사용 안내](outputs/PLACE_SEARCH_GUIDE.md)를 참고하세요. 상세 상호·주소 검색은 선택적 카카오 Local 키로 활성화합니다. 최신 테스트는 57개 통과입니다.

> **서울시 실제 데이터 연결 업데이트**: 공식 121개 장소 경계를 동봉했고, 현재 작업환경 `.env`는 실제 모드입니다. 키 입력·재시작·검증 방법은 [실데이터 연결 안내](outputs/SEOUL_LIVE_SETUP.md)를 먼저 확인하세요. 아래의 40/42개 테스트와 mock 수치는 이전 구현 검증 기록이며 최신 테스트는 50개 통과입니다.

# CrowdWay 통합 웹사이트

제공된 CrowdWay React 프론트엔드와 Python 경로 엔진을 한 웹사이트로 통합했습니다. 원본 Downloads 폴더는 수정하지 않았으며 통합 UI는 `frontend/`에 있습니다. 별도의 Node API 서버는 사용하지 않습니다.

## 웹사이트 실행

현재 작업환경에서는 설치와 빌드가 완료되어 있습니다:

```bash
./run_web.sh
```

브라우저에서 **http://127.0.0.1:8000**을 열고 **시작하기 → 길찾기**를 누르세요. 이미 서버가 실행 중이면 그대로 접속하면 됩니다. 포트가 사용 중이면 `PORT=8001 ./run_web.sh`로 별도 실행할 수 있습니다.

새 환경에서는 Python 3.11+와 Node.js 22.12+ 또는 24+를 설치하고:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
./run_web.sh
```

`run_web.sh`는 `.env`와 shell 설정을 우선 사용합니다. `GRAPHML_PATH`가 아예 지정되지 않은 경우에만 동봉된 여의도 OSM 그래프를 기본으로 선택합니다. `.env`에서 `GRAPHML_PATH=`로 비워 두면 OSM을 다운로드합니다. 저장본을 쓰려면 `GRAPHML_PATH=data/yeouido_walk.graphml`로 지정하세요.

## 연결 구조와 사용법

- FastAPI가 `/`, `/search`, `/result`, `/assets/*` 화면과 `POST /route` API를 같은 주소에서 제공합니다. SPA의 결과 화면을 새로고침해도 열립니다.
- 화면의 선택 지점 또는 직접 입력한 위도·경도가 실제 경로 엔진으로 전달됩니다. 기본 선택 지점은 저장된 그래프 범위에 맞춘 여의도 예시입니다.
- 빠르게/균형 있게/쾌적하게는 fastest/balanced/comfortable에 대응합니다. 결과 화면에서 성향을 변경한 뒤 재계산할 수 있습니다.
- 최단/추천 경로 카드와 지도 선을 눌러 선택할 수 있습니다. 거리, 시간, 평균·최대 혼잡도, 혼잡 구간 거리, 지역 수와 추가 거리·노출 감소율은 백엔드 계산 결과입니다.
- `POST /route` 응답의 `congestion_zones`는 **그 경로 계산에 사용한 동일 snapshot의 GeoJSON Feature 목록**입니다. Polygon/MultiPolygon 및 내부 hole을 지도에 그대로 표시합니다.
- 지도 핀은 snap된 도보 노드 위치이며 연결 거리 제외 안내를 표시합니다.
- 프론트엔드의 고정 경로, 독립적인 감소율 계산, 가산지역 추정 혼잡 원형은 제거했습니다. 기존 프론트의 `VITE_USE_ROUTE_MOCK`/`VITE_USE_CONGESTION_MOCK` 변수와 Node 서버는 통합본에서 사용하지 않습니다.
- 혼잡도는 백엔드의 `USE_MOCK_CONGESTION`만 따릅니다. 기본은 **실제 OSM 경로 + 데모 혼잡도**이며 화면에 DEMO를 명시합니다. 서울시 실제 데이터 모드는 아래 기존 안내대로 key와 공식 경계를 설정하세요. 원본 프론트의 `.env`/비밀키는 복사하지 않았습니다.
- 서울시 조회 실패 시 FALLBACK과 경고를 표시하고 실제 데이터로 오인할 LIVE 문구를 표시하지 않습니다.
- 기본 지도 타일은 OpenStreetMap 인터넷 연결이 필요합니다. 저장 graph를 쓰면 경로 계산에는 네트워크가 필요 없지만 배경지도 타일은 별개입니다.

## 개발 중 수정

백엔드를 8000 포트에서 실행한 상태에서:

```bash
npm --prefix frontend run dev
```

http://127.0.0.1:5173 에서 Vite 개발 화면을 사용합니다. `/route` 요청은 8000으로 proxy됩니다. 배포 형태로 확인하려면 다시 `npm --prefix frontend run build` 후 8000 화면을 새로고침하세요. Python 변경은 서버 재시작이 필요합니다.

## 통합 검증

- TypeScript 검사 + Vite production build 성공.
- Python 테스트 **42개 통과**, 라이브러리 deprecation warning 2개.
- 브라우저에서 첫 화면 → 검색 → 실제 경로 결과 → 성향 재계산 확인.
- 390px 모바일 화면과 지원 범위 밖 좌표의 오류/검색 복귀 확인.
- 실측 예시: 1,153.5m → 1,437.4m(+24.6%), 가중 혼잡 노출 54.2% 감소. 혼잡도는 합성 데이터입니다.
- 로컬 통합 사이트이며 공개 도메인 배포는 하지 않았습니다.

---

# 실시간 혼잡도 기반 도보 경로 추천 MVP

FastAPI + OSMnx + NetworkX A*로 일반 최단 도보 경로와 혼잡 회피 경로를 비교합니다. 기본 모드는 **실제 OSM 도보 네트워크 + 여의도 합성 혼잡 Polygon**입니다. 서울시 API key 없이 동작하며, 최초 OSM 다운로드에는 인터넷이 필요합니다.

## 설치와 실행

Python 3.11 이상을 사용하세요. 프로젝트 루트에서:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

- API 문서: http://127.0.0.1:8000/docs
- 상태 확인: `curl http://127.0.0.1:8000/health`
- `.env`는 자동으로 읽으며 shell 환경변수가 우선합니다. 변경 후 서버를 재시작하세요.
- 설치 검증 환경은 Python 3.14입니다. `requirements.lock.txt`는 이 환경에서 실제 설치된 버전 기록이며 다른 Python 버전에서는 `requirements.txt` 사용을 권장합니다.

## API 예시

```bash
curl -sS -X POST http://127.0.0.1:8000/route \
  -H 'Content-Type: application/json' \
  -d '{"start":{"lat":37.521,"lon":126.924},"end":{"lat":37.528,"lon":126.932},"preference":"comfortable"}'
```

`preference`는 `fastest` / `balanced` / `comfortable`이며 생략하면 `comfortable`입니다. 좌표는 숫자이며 범위를 벗어나거나 정의하지 않은 필드를 보내면 422를 반환합니다.

응답은 `shortest`, `recommended`, `comparison`, `metadata`로 구성됩니다.

| 필드 | 의미 |
|---|---|
| distance_m | snap된 노드 사이의 OSM edge 길이 합(m) |
| estimated_time_min | 거리 / 기본 분속 75m |
| average_congestion | Σ(length × congestion) / 총 거리 |
| max_congestion | 경로 edge 혼잡도 중 최댓값 |
| congested_distance_m | edge 혼잡도 ≥ 0.7인 edge의 전체 길이 합 |
| high_congestion_zone_count | 양의 길이로 통과한 score ≥ 0.7 지역의 고유 이름 수 |
| congestion_exposure_m | Σ(length × congestion), 비교에 쓰는 가중 노출량 |
| geometry | 실제 edge 형상을 연결한 `[longitude, latitude]` 배열 |
| comparison.extra_distance_m / percent | 최단경로 대비 추가 거리 및 비율 |
| comparison.extra_time_min | 추가 도보 시간 |
| comparison.congestion_reduction_percent | 가중 노출량 감소율(%) |

프론트에서 `{ "type": "LineString", "coordinates": response.recommended.geometry }`로 바로 그릴 수 있습니다. 같은 노드로 snap되면 거리 0, 동일 좌표 2개를 반환합니다.

`metadata`에는 요청/적용 alpha, 우회 제한에 따른 alpha 감소 여부, 혼잡 데이터 출처와 조회 시각, 경고, snap 좌표 및 원래 좌표와의 거리가 포함됩니다. 원래 좌표에서 도보 노드까지의 연결 구간은 경로 거리/시간에 포함하지 않습니다. 수치는 비교 정확도를 위해 중간 반올림하지 않으므로 UI에서 표시 자릿수를 정하세요.

오류: 입력/지원 범위/snap 실패 422, 연결된 도보 경로 없음 404, OSM 다운로드/파일 오류 503, 기타 경로 계산 오류 500. 한 요청의 실패가 서버를 종료하지 않습니다. `/health`는 프로세스 생존 확인이며 외부 API 가용성을 보장하지 않습니다.

## 알고리즘

1. 두 좌표의 중간점을 0.01도 단위로 묶고, 양 끝점까지 거리 중 큰 값에 1km 여유를 더해 요청 반경을 계산합니다. 최소 1.5km이며 500m 단위로 올림합니다. 따라서 3km 이상 떨어진 두 지점도 동적으로 포함합니다. 반경 10km를 넘으면 422로 거절해 서울 전체 다운로드를 방지합니다.
2. `ox.graph_from_point(..., network_type="walk", retain_all=True)`로 도보 MultiDiGraph를 생성합니다. 떨어진 컴포넌트도 유지해 잘못된 인접 컴포넌트로 snap하지 않습니다.
3. 미터 단위 UTM에서 가장 가까운 노드를 STRtree로 찾습니다. 도보 노드까지 500m 이상이면 거절합니다.
4. edge 형상이 없으면 양 끝 노드로 LineString을 만듭니다. 모든 선/Polygon을 동일 UTM으로 투영하고 Polygon STRtree로 겹칠 후보만 찾습니다. 도 단위 길이를 미터로 오해하지 않습니다.
5. 지역별 영향은 `intersection_length / geometry_length × zone_score`이며, edge 혼잡도는 영향값의 **최댓값**입니다. 값은 0~1로 제한합니다. 복수 지역이 서로 다른 구간을 덮어도 합산하지 않으므로 노출을 과소평가할 수 있는 MVP 근사입니다.
6. A*로 alpha=0의 일반 최단경로와 요청 성향 경로를 각각 찾습니다. parallel edge는 해당 alpha의 최소 비용 edge key를 선택하고, 평가와 geometry에도 동일 key를 사용합니다.
7. 추천 거리가 최단거리 × 1.30을 초과하면 comfortable은 `3 → 2 → 1 → 0`, balanced는 `1 → 0` 순서로 재탐색합니다. 최초로 한도를 만족한 경로를 반환하고 마지막에는 최단경로를 반환합니다. fastest는 최단경로와 같습니다.

### 비용 함수

```python
cost = distance * (1 + alpha * congestion ** 2)
```

alpha 기본값은 fastest=0, balanced=1, comfortable=3입니다. 제곱 패널티는 낮은 혼잡에는 작게, 높은 혼잡에는 크게 작용합니다. 예를 들어 100m edge와 alpha=3에서 혼잡도 0 / 0.5 / 1의 비용은 100 / 175 / 400입니다.

A* heuristic은 목적지까지 great-circle 거리이며 혼잡 패널티는 넣지 않습니다. OSM 길이 반올림이나 테스트 그래프에서 직선거리보다 짧은 길이가 생겨도 admissible하도록 모든 edge의 `length / straight_distance` 최솟값(최대 1)으로 보정합니다.

평균 혼잡도는 거리 가중 평균입니다. `congested_distance_m`는 부분 교차 길이가 아니라 **최종 edge score가 임계값을 넘은 edge 길이**입니다. 지역 통과 수는 그 edge 임계값과 독립적으로 높은 혼잡 지역과 양의 길이로 겹쳤는지를 기준으로 셉니다. 접점만 닿는 경우 제외하며 같은 지역 재진입은 한 번으로 셉니다.

감소율은 `(shortest_exposure - recommended_exposure) / shortest_exposure × 100`입니다. 최단 노출량이 0이면 0을 반환합니다. 제곱 비용을 최적화하므로 선형 가중 노출량 감소가 항상 보장되는 것은 아니며, 음수 감소율도 사실대로 반환합니다. alpha 재탐색은 거리 제약 내 전역 최적 경로를 보장하는 알고리즘이 아닙니다.

## 환경변수

전체 예시는 `.env.example`에 있습니다.

| 변수 | 기본값 | 용도 |
|---|---|---|
| USE_MOCK_CONGESTION | true | 합성/실제 혼잡 데이터 선택 |
| SEOUL_API_KEY | 빈 값 | 서울시 API 인증키 |
| SEOUL_API_BASE_URL | http://openapi.seoul.go.kr:8088 | API 주소 |
| SEOUL_ZONES_FILE | data/seoul_zones.geojson | 공식 영역을 변환한 WGS84 GeoJSON |
| CONGESTION_FALLBACK | empty | 실제 API 실패 시 empty 또는 mock |
| CONGESTION_TTL_SECONDS | 60 | 혼잡 snapshot 캐시 초, 실패 결과에도 적용 |
| API_TIMEOUT_SECONDS | 10 | 서울시 HTTP 요청 timeout |
| MAX_DETOUR_RATIO | 1.30 | 최단경로 대비 최대 추천 거리 비율 |
| WALKING_SPEED_KMH | 4.5 | 도보 속도 |
| HIGH_CONGESTION_THRESHOLD | 0.7 | 높은 혼잡도 기준 |
| GRAPH_MIN_RADIUS_M | 1500 | 최소 OSM 반경 |
| GRAPH_BUFFER_M | 1000 | 양 끝점을 포함한 후 추가 여유 |
| GRAPH_MAX_RADIUS_M | 10000 | 그래프 반경 상한 |
| GRAPH_CACHE_SIZE | 4 | 메모리 LRU 그래프 수 |
| MAX_SNAP_DISTANCE_M | 500 | 입력 좌표에서 node까지 최대 거리 |
| OSM_TIMEOUT_SECONDS | 90 | OSMnx 요청 timeout |
| GRAPHML_PATH | 빈 값 | 저장된 OSMnx GraphML을 사용하면 다운로드 생략 |

OSMnx HTTP disk cache는 `cache/osmnx/`에 저장합니다. 메모리 LRU와 혼잡 TTL은 프로세스별이며 동시 최초 요청의 중복 작업은 lock으로 막습니다. 혼잡도는 그래프 복사본에만 부여하므로 요청끼리 공유 graph를 오염시키지 않습니다. 복잡한 Redis나 DB는 없습니다.

## Mock 테스트와 데모

```bash
python -m pytest -q
```

자동 테스트는 외부 네트워크 없이 합성 MultiDiGraph를 사용합니다. API 통합 테스트는 그래프 공급만 교체하고 실제 snap, mock provider, Polygon 계산, A*, 평가 및 JSON 응답을 거칩니다. 서울시 응답 adapter의 HTTP 연결은 MockTransport로 검증합니다.

실제 OSM + mock 혼잡도 통합 검증 및 그래프 저장:

```bash
USE_MOCK_CONGESTION=true python -m scripts.smoke_osm
```

성공하면 `outputs/osm_route_response.json`과 `data/yeouido_walk.graphml`을 생성합니다. 이후 같은 여의도 지역은 인터넷 없이 실행할 수 있습니다:

```bash
USE_MOCK_CONGESTION=true GRAPHML_PATH=data/yeouido_walk.graphml uvicorn app.main:app --reload
```

mock Polygon은 여의도 예시 좌표에만 존재하고 공식 경계가 아닙니다. 다른 지역은 score가 0이며, 두 경로가 같을 수 있습니다. 이미 저장한 그래프는 해당 영역에 한정됩니다. 그래프 다운로드 실패를 합성 도로로 자동 대체하지 않습니다.

## 실제 서울시 API 연결

[서울시 실시간 인구데이터 공식 안내](https://data.seoul.go.kr/dataList/OA-21778/A/1/datasetView.do)는 장소별 조회 API와 영역 파일을 별도로 제공합니다. 데이터 응답에 임의의 Polygon이 있다고 가정하지 않습니다.

1. 공식 사이트에서 인증키와 장소 영역/코드 목록을 받습니다.
2. 필요한 데모 지역만 골라 영역 파일을 WGS84(EPSG:4326) GeoJSON FeatureCollection으로 변환합니다. properties를 `name`(공식 장소명)과 선택적 `area_code`(공식 코드)로 맞춥니다. 원본 CRS를 정확히 지정한 후 `GeoDataFrame.to_crs(4326)`으로 변환하세요.
3. `data/seoul_zones.geojson`에 저장합니다. 각 feature의 geometry는 실제 Polygon 또는 MultiPolygon이어야 합니다. 빈 좌표/합성 경계를 실제 경계로 사용하지 마세요.
4. `.env`에 아래 값을 지정하고 재시작합니다.

```dotenv
USE_MOCK_CONGESTION=false
SEOUL_API_KEY=발급받은키
SEOUL_ZONES_FILE=data/seoul_zones.geojson
CONGESTION_FALLBACK=empty
```

`seoul_provider.py`는 `/KEY/json/citydata_ppltn/1/5/장소명또는코드`를 장소별로 조회합니다. `adapt_seoul_response()`만 외부 응답 구조를 알고, `SeoulRtd.citydata_ppltn` 목록(또는 그 아래 row)의 `AREA_CONGEST_LVL`을 내부 모델로 변환합니다. 실제 계약이 다르면 **이 adapter 함수만** 수정하고 `tests/test_provider.py`에 실제 응답에서 민감정보를 제거한 fixture를 추가하세요.

매핑: 여유=0, 보통=0.3, 약간 붐빔=0.7, 붐빔=1. 알 수 없는 값은 보통(0.3)을 사용합니다. 알 수 없는 응답 구조나 누락된 혼잡 필드는 실패로 취급합니다.

키/경계 누락, API 장애, 잘못된 응답이 발생하면 snapshot 전체를 설정된 fallback으로 대체합니다. 일부 지역 실패를 정상 실시간 데이터처럼 섞지 않습니다. `metadata.congestion_source`가 `seoul`인지 확인하세요. `fallback_empty`의 0은 실제로 한산하다는 뜻이 아니라 데이터 미확보입니다. `fallback_mock`은 데모값입니다. `congestion_fetched_at`은 우리 서버 조회 시각이며 원천 관측 시각이 아닙니다. 키가 포함된 URL이나 upstream 오류 전문을 응답/로그에 남기지 않습니다.

## 구조

```text
app/main.py                  API, 오류 처리
app/config.py                환경설정
app/models/                  요청/응답 Pydantic 모델
app/routing/graph.py          OSM 범위, 캐시, snap
app/routing/cost.py           비용 함수
app/routing/router.py         A*, parallel edge, 우회 제한
app/routing/evaluator.py      지표, 좌표, 비교
app/congestion/provider.py   정규화, 지역 모델, TTL, fallback
app/congestion/mock_provider.py
app/congestion/seoul_provider.py
app/congestion/mapper.py     UTM 교차 길이와 STRtree
app/utils/geo.py             구면거리, geometry 보완
scripts/smoke_osm.py         실제 OSM 통합 검증
tests/                     비용/혼잡/경로/provider/API 테스트
```

## 현재 한계

- MVP 지원 영역은 위도 37.35~37.75 / 경도 126.70~127.25입니다. OSM에 없는 도보 연결, 실시간 공사/통제, 계단/경사, 접근성은 별도로 다루지 않습니다.
- 공식 혼잡도는 지역 단위입니다. 개별 보도 관측값이 아니며 미관측 구간은 계산상 0입니다. 운영 서비스에서는 데이터 커버리지/원천 시각을 추가해야 합니다.
- 서울시 key와 공식 경계를 제공하지 않은 상태에서는 live 서울시 성공 응답 검증을 할 수 없습니다. adapter는 모의 응답으로 검증됩니다.
- 초기 OSM 다운로드는 수십 초 이상 걸릴 수 있습니다. OSMnx는 429/504를 자체 재시도하므로 `OSM_TIMEOUT_SECONDS`는 전체 API 요청의 엄격한 deadline이 아닙니다. 해커톤 시연 전 GraphML을 저장하세요.
- 요청마다 UTM 투영/edge 매핑을 수행합니다. STRtree로 모든 edge×Polygon 비교는 피하지만 대규모 동시 트래픽용으로 최적화한 구조는 아닙니다. 서울시 조회는 경계 파일에 있는 지역을 순차 조회하므로 MVP 데모 지역만 넣으세요.
- OSM graph 영역 밖의 더 좋은 경로는 찾지 못할 수 있습니다. 반환 우회 한도는 확보된 그래프의 최단경로 기준입니다.

OSM 데이터 출처: © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright). 그래프는 [OSMnx 공식 도보 그래프 API](https://osmnx.readthedocs.io/en/stable/user-reference.html)를 사용합니다. 지도 UI에도 데이터 출처를 표시하세요.

## 실제 검증 결과

2026-09-12, Python 3.14 환경에서:

- `python -m pytest -q`: **40 passed**, 라이브러리 deprecation warning 2개.
- 실제 OSM 다운로드: 여의도 도보 graph **3,633 nodes / 10,128 edges**. 저장본은 `data/yeouido_walk.graphml`.
- Uvicorn `/health` 및 `/route`의 fastest/balanced/comfortable 모두 실제 HTTP **200**.
- 예시 comfortable: **최단 1,153.52m → 추천 1,437.40m(+24.61%)**, 추가 **3.79분**, 가중 혼잡 노출 감소 **54.19%**. 이는 실제 OSM 도로 위 **합성 혼잡도** 결과입니다.
- fastest/balanced는 예시에서 최단경로와 동일했습니다.
- 응답 전문: `outputs/osm_route_response.json`; HTTP 검증 요약: `outputs/http_verification.json`; 테스트 로그: `outputs/test_results.txt`.
- 실제 서울시 인증키를 이용한 live 응답은 미검증입니다.
