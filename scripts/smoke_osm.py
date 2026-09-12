"""Real OSM + mock congestion integration check. Run: python -m scripts.smoke_osm."""
import json
from pathlib import Path
import osmnx as ox
from fastapi.testclient import TestClient
from app.main import app, graph_service
from app.models.request import RouteRequest

payload = {'start': {'lat': 37.521, 'lon': 126.924}, 'end': {'lat': 37.528, 'lon': 126.932}, 'preference': 'comfortable'}
if __name__ == '__main__':
    with TestClient(app) as client:
        response = client.post('/route', json=payload)
        response.raise_for_status()
        body = response.json()
    assert body['recommended']['distance_m'] <= body['shortest']['distance_m'] * 1.30 + 1e-8
    assert body['metadata']['congestion_source'] == 'mock'
    directory = Path('outputs')
    directory.mkdir(exist_ok=True)
    (directory / 'osm_route_response.json').write_text(json.dumps(body, ensure_ascii=False, indent=2))
    request = RouteRequest(**payload)
    graph = graph_service.get_graph(request.start, request.end)
    Path('data').mkdir(exist_ok=True)
    ox.save_graphml(graph, 'data/yeouido_walk.graphml')
    print(json.dumps({'nodes': len(graph), 'edges': graph.number_of_edges(), 'shortest_m': body['shortest']['distance_m'], 'recommended_m': body['recommended']['distance_m'], 'comparison': body['comparison']}, ensure_ascii=False))
