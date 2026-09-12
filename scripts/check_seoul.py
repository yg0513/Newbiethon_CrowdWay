"""Check real API wiring without printing keys. python -m scripts.check_seoul --sample"""
import argparse
import json
from app.config import Settings
from app.congestion.provider import CongestionProvider

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', action='store_true', help='Official sample key: POI009 only')
    parser.add_argument('--service', choices=['citydata_ppltn', 'citydata'])
    args = parser.parse_args()
    config = Settings.from_env().model_copy(update={'use_mock_congestion': False, 'congestion_fallback': 'empty'})
    if args.sample: config = config.model_copy(update={'seoul_api_key': 'sample', 'seoul_area_codes': 'POI009'})
    if args.service: config = config.model_copy(update={'seoul_api_service': args.service})
    # Bound the default verification to Yeouido; sample uses its single official area.
    bounds = None if args.sample else (126.90, 37.51, 126.95, 37.54)
    snapshot = CongestionProvider(config).get_snapshot(bounds)
    print(json.dumps({'source': snapshot.source, 'warnings': snapshot.warnings,
        'zones': [{'name': z.name, 'code': z.area_code, 'score': z.score, 'observed_at': z.observed_at, 'replaced': z.replaced} for z in snapshot.zones]},ensure_ascii=False,indent=2))
    return 0 if snapshot.source == 'seoul' and snapshot.zones else 1

if __name__ == '__main__': raise SystemExit(main())
