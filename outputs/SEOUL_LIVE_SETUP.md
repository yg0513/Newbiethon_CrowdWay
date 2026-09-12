# 서울시 실제 데이터 연결

새로 압축을 푼 환경에서는 먼저 `cp .env.example .env`를 실행하세요.

공식 영역은 이미 `data/seoul_zones.geojson`에 포함되어 있습니다. 실제 운영 키만 프로젝트 루트 `.env`에 입력하면 됩니다. 키를 채팅이나 프론트엔드 코드에 넣지 마세요.

```dotenv
USE_MOCK_CONGESTION=false
SEOUL_API_KEY=여기에_발급받은_키
SEOUL_API_SERVICE=citydata_ppltn
SEOUL_ZONES_FILE=data/seoul_zones.geojson
CONGESTION_FALLBACK=empty
GRAPHML_PATH=data/yeouido_walk.graphml
```

기존 서버를 실행한 터미널에서 Ctrl+C로 종료한 후 `./run_web.sh`로 재시작합니다. 서버가 8000에서 실행 중이라 종료하기 어렵다면 `PORT=8001 ./run_web.sh` 후 http://127.0.0.1:8001 로 접속할 수 있습니다. shell에 `USE_MOCK_CONGESTION=true`가 별도로 설정되어 있으면 해제하세요. shell 환경변수가 .env보다 우선합니다.

## 확인 명령

```bash
# 키 없이 공식 샘플의 광화문·덕수궁 실데이터 연결 검사
.venv/bin/python -m scripts.check_seoul --sample
.venv/bin/python -m scripts.check_seoul --sample --service citydata

# 내 키로 여의도 주변 실제 데이터 검사
.venv/bin/python -m scripts.check_seoul

# 설정 확인: 키 원문은 반환하지 않습니다
curl http://127.0.0.1:8000/data-status

# 자동 테스트
.venv/bin/python -m pytest -q
```

정상 실제 조회에서는 `source: seoul`, 장소별 관측 시각과 점수가 출력됩니다. `sample`은 POI009(광화문·덕수궁)만 지원하며 여의도 실데이터로 대신 사용할 수 없습니다.

## 공식 문서 적용

1. [OA-21778 실시간 인구데이터](https://data.seoul.go.kr/dataList/OA-21778/A/1/datasetView.do): 기본 API. `/KEY/json/citydata_ppltn/1/5/장소코드`를 호출합니다. `SeoulRtd.citydata_ppltn`, `RESULT.CODE`, `AREA_CD`, `AREA_CONGEST_LVL`, `PPLTN_TIME`, `REPLACE_YN`을 실제 샘플로 확인했습니다.
2. [OA-21285 실시간 도시데이터](https://data.seoul.go.kr/dataList/OA-21285/A/1/datasetView.do): `SEOUL_API_SERVICE=citydata`로 선택합니다. `/KEY/xml/citydata/1/5/장소코드`의 `CITYDATA/LIVE_PPLTN_STTS/LIVE_PPLTN_STTS`를 읽습니다. 데이터셋 페이지는 확인 당시 서비스 지연 메시지를 반환했으나, 공식 인구데이터 페이지 첨부 매뉴얼과 실제 XML 샘플 호출로 구조를 검증했습니다.
3. [OA-22385 상권현황데이터](https://data.seoul.go.kr/dataList/OA-22385/F/1/datasetView.do): 카드 소비 중심의 상권현황 데이터입니다. 보행 인구 혼잡도로 대체하지 않으며 현재 비용 함수에는 넣지 않습니다.
4. [여의도한강공원 공식 지도](https://data.seoul.go.kr/SeoulRtd/map?hotspotNm=여의도한강공원): 사용자 확인용 지도입니다. 내부 웹 API를 긁어오는 방식으로 서버에 결합하지 않았습니다.

## 경계와 장소 코드

서울시 공식 `서울시 주요 121장소 영역.zip`을 내려받아 원본 WGS84 좌표계를 유지하고 속성만 name/area_code/category로 통일했습니다. 공식 원본 중 쌍문역(POI070)의 유효하지 않은 geometry는 make_valid로 보정했습니다. 다운로드 출처, 원본 SHA256 및 보정 내용은 `data/seoul_zones.source.json`에 있습니다. 출처: 서울특별시, 공공누리 제1유형.

여의도 관련 장소: POI072 여의도, POI105 여의도한강공원, POI126 여의서로. 서울시 응답의 AREA_CD와 공식 경계를 일치시켜 사용합니다. 요청 그래프의 영역과 겹치는 장소만 조회해 매 요청마다 121개를 모두 호출하지 않습니다. `SEOUL_AREA_CODES=POI072,POI105,POI126`으로 조회 장소를 추가 제한할 수도 있습니다. 비워 두면 공간 범위로만 제한합니다.

## 시간·장애 처리

- TTL 60초, 요청 영역별 캐시 최대 8개.
- `PPLTN_TIME`을 한국 시간으로 파싱합니다. 기본 60분보다 오래되거나 미래 5분 이상인 데이터는 실패로 처리합니다. `SEOUL_MAX_AGE_MINUTES`로 변경 가능합니다.
- 화면과 각 Polygon tooltip에 원천 관측 시각을 표시합니다. 서버 조회 시각과 원천 관측 시각은 다릅니다.
- 키 누락, sample 장소 불일치, 응답 코드/필드 오류, 오래된 데이터는 구체적 경고로 표시합니다. API 키/URL은 오류 응답에 넣지 않습니다.
- 지역 하나라도 실패하면 해당 snapshot 전체를 fallback으로 처리하는 MVP 정책입니다. 지역별 부분 성공이나 과거 데이터 유지 정책은 구현하지 않았습니다.
- 데이터 미확보 시 UI는 혼잡도를 '데이터 없음'으로 표시합니다. API의 계산용 0은 한산하다는 관측이 아닙니다.
- 공식 경계 밖 도로에는 관측값이 없습니다. 관측지역 내부의 점수도 개별 보도의 실측 인원 수가 아닌 지역 단위 지표입니다.
- 서울시 실제 경계는 넓으므로 두 경로가 모두 같은 혼잡지역 안에 있으면 회피 효과가 없을 수 있습니다. 이전 합성 데이터의 54.2% 감소를 실데이터에서 보장하지 않습니다.

## 이번 실행 검증

2026-09-12: 공식 샘플키로 JSON 인구데이터와 XML 도시데이터 모두 실제 호출 성공. 두 응답은 광화문·덕수궁, 보통(0.3), 관측 15:50으로 확인됐습니다. 결과는 `seoul_population_check.json`, `seoul_city_check.json`에 기록했습니다. 이는 당시 관측값이며 현재 혼잡도를 의미하지 않습니다.

Python 50개 테스트 통과, 프론트 production build 성공. 발급받은 여의도용 API 키는 아직 입력되지 않아 사용자 키로 여의도 성공 응답은 미검증입니다. 현재 .env는 실제 데이터 모드이며 키 입력 전에는 fallback_empty와 안내가 표시됩니다.
