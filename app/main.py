"""Run with uvicorn app.main:app --reload; interactive docs at /docs."""
import logging
import networkx as nx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from shapely.geometry import mapping
from app.config import ROOT
from app.config import ALPHAS, settings
from app.models.request import RouteRequest
from app.models.response import RouteResponse, RouteMetadata
from app.congestion.provider import CongestionProvider
from app.congestion.mapper import map_congestion
from app.routing.graph import GraphService, GraphUnavailable
from app.routing.router import calculate_routes
from app.routing.evaluator import evaluate_route, compare_routes

app = FastAPI(title='혼잡 회피 도보 경로 API', version='0.1.0')
graph_service = GraphService(settings)
congestion_provider = CongestionProvider(settings)
logger = logging.getLogger(__name__)

@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}

@app.post('/route', response_model=RouteResponse)
def route(request: RouteRequest) -> RouteResponse:
    # Sync endpoint runs in FastAPI's worker threadpool, keeping event loop free.
    try:
        raw = graph_service.get_graph(request.start, request.end)
        start, start_distance = graph_service.snap(raw, request.start)
        end, end_distance = graph_service.snap(raw, request.end)
        xs = [d['x'] for _, d in raw.nodes(data=True)]
        ys = [d['y'] for _, d in raw.nodes(data=True)]
        snapshot = congestion_provider.get_snapshot((min(xs), min(ys), max(xs), max(ys)))
        graph = map_congestion(raw, snapshot.zones, settings.high_congestion_threshold)
        shortest_route, recommended_route = calculate_routes(graph, start, end, request.preference, settings.max_detour_ratio)
        shortest = evaluate_route(graph, shortest_route, settings.walking_speed_kmh, settings.high_congestion_threshold)
        recommended = evaluate_route(graph, recommended_route, settings.walking_speed_kmh, settings.high_congestion_threshold)
        warnings = list(snapshot.warnings)
        if snapshot.source == 'mock':
            warnings.append('데모용 합성 혼잡도이며 실제 현장 혼잡도가 아닙니다.')
        return RouteResponse(shortest=shortest, recommended=recommended, comparison=compare_routes(shortest, recommended),
            congestion_zones=[{'type': 'Feature', 'properties': {'name': z.name, 'score': z.score,
                'area_code': z.area_code, 'observed_at': z.observed_at, 'message': z.message, 'replaced': z.replaced,
                'population_min': z.population_min, 'population_max': z.population_max,
                'level': z.level or ('붐빔' if z.score >= 1 else '약간 붐빔' if z.score >= 0.7 else '보통' if z.score > 0 else '여유')},
                'geometry': mapping(z.geometry)} for z in snapshot.zones],
            metadata=RouteMetadata(preference=request.preference, requested_alpha=ALPHAS[request.preference],
                applied_alpha=recommended_route.alpha, detour_limited=recommended_route.alpha < ALPHAS[request.preference],
                congestion_source=snapshot.source, congestion_fetched_at=snapshot.fetched_at, warnings=warnings,
                snapped_start=(raw.nodes[start]['x'], raw.nodes[start]['y']),
                snapped_end=(raw.nodes[end]['x'], raw.nodes[end]['y']),
                start_snap_distance_m=start_distance, end_snap_distance_m=end_distance))
    except GraphUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc
    except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
        raise HTTPException(404, '두 지점 사이에 연결된 도보 경로가 없습니다.') from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        logger.error('Route calculation failed: %s', type(exc).__name__)
        raise HTTPException(500, '경로 계산 중 오류가 발생했습니다. 잠시 후 다시 시도하세요.') from exc


# Build the supplied React app once, then serve UI + API on one origin.
FRONTEND_DIST = ROOT / 'frontend' / 'dist'
if (FRONTEND_DIST / 'assets').is_dir():
    app.mount('/assets', StaticFiles(directory=FRONTEND_DIST / 'assets'), name='assets')

@app.get('/', include_in_schema=False)
@app.get('/search', include_in_schema=False)
@app.get('/result', include_in_schema=False)
def website() -> FileResponse:
    index = FRONTEND_DIST / 'index.html'
    if not index.is_file():
        raise HTTPException(503, '웹 화면을 먼저 빌드하세요: npm --prefix frontend install && npm --prefix frontend run build')
    return FileResponse(index, headers={'Cache-Control': 'no-cache'})

@app.get('/data-status')
def data_status() -> dict:
    """Read-only setup diagnostics; never expose credentials or make API requests."""
    from app.congestion.seoul_provider import get_boundaries
    try:
        boundaries = get_boundaries(settings)
        count, boundary_error = len(boundaries), None
    except Exception:
        count, boundary_error = 0, '공식 경계 파일을 확인하세요.'
    return {'mode': 'mock' if settings.use_mock_congestion else 'seoul',
            'api_key_configured': bool(settings.seoul_api_key.strip()),
            'service': settings.seoul_api_service, 'boundary_count': count,
            'boundary_error': boundary_error, 'max_data_age_minutes': settings.seoul_max_age_minutes}


from app.places.search import PlaceSearch, PlaceSearchError
place_search = PlaceSearch(settings)

@app.get('/places/search')
def search_places(q: str = Query(min_length=2, max_length=100)) -> dict:
    try:
        return place_search.search(q)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except PlaceSearchError as exc:
        raise HTTPException(503, str(exc)) from exc
