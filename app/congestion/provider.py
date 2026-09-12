"""Small shared model and thread-safe TTL cache for congestion snapshots."""
from dataclasses import dataclass
from collections import OrderedDict
from datetime import datetime, timezone
from threading import Lock
from time import monotonic
from math import isfinite
from shapely.geometry import Polygon, MultiPolygon
from app.config import Settings

LEVELS = {'여유': 0.0, '보통': 0.3, '약간 붐빔': 0.7, '붐빔': 1.0}

def normalize_congestion(level: str) -> float:
    """Unknown values use moderate congestion rather than assuming empty streets."""
    return LEVELS.get(level.strip(), 0.3) if isinstance(level, str) else 0.3

@dataclass(frozen=True)
class CongestionZone:
    name: str
    score: float
    geometry: Polygon | MultiPolygon
    level: str = ''
    area_code: str | None = None
    observed_at: str | None = None
    message: str | None = None
    replaced: bool = False
    population_min: int | None = None
    population_max: int | None = None

    def __post_init__(self) -> None:
        if not isfinite(self.score) or not 0 <= self.score <= 1:
            raise ValueError('지역 혼잡도는 0~1의 유한한 값이어야 합니다.')
        if not isinstance(self.geometry, (Polygon, MultiPolygon)) or self.geometry.is_empty or not self.geometry.is_valid:
            raise ValueError('유효한 Polygon/MultiPolygon이 필요합니다.')

@dataclass(frozen=True)
class CongestionSnapshot:
    zones: tuple[CongestionZone, ...]
    source: str
    fetched_at: str
    warnings: tuple[str, ...] = ()

class CongestionProvider:
    def __init__(self, config: Settings):
        self.config = config
        self._lock = Lock()
        self._expires = 0.0
        self._cache = OrderedDict()
        self._snapshot: CongestionSnapshot | None = None

    def get_snapshot(self, bounds: tuple | None = None) -> CongestionSnapshot:
        from app.congestion.mock_provider import get_mock_zones
        from app.congestion.seoul_provider import load_seoul_zones, SeoulDataError
        with self._lock:
            key = None if self.config.use_mock_congestion else bounds
            if key in self._cache:
                expires, snapshot = self._cache[key]
                if monotonic() < min(expires, self._expires):
                    self._cache.move_to_end(key)
                    return snapshot
            warnings: tuple[str, ...] = ()
            if self.config.use_mock_congestion:
                zones, source = get_mock_zones(), 'mock'
            else:
                try:
                    zones, source = load_seoul_zones(self.config, bounds), 'seoul'
                    if not zones: warnings = ('요청 범위에 조회 가능한 서울시 혼잡 관측 지역이 없습니다. 미관측 구간의 0은 한산함을 뜻하지 않습니다.',)
                    if any(z.replaced for z in zones): warnings += ('일부 지역은 서울시가 대체한 인구 데이터입니다.',)
                except Exception as exc:
                    # Do not expose exception URLs: Seoul's API key is in the path.
                    source = f'fallback_{self.config.congestion_fallback}'
                    zones = get_mock_zones() if self.config.congestion_fallback == 'mock' else []
                    warnings = ((str(exc) if isinstance(exc, SeoulDataError) else '서울시 응답 또는 경계 파일 처리 오류입니다.'), '대체 데이터를 사용했습니다. 미관측 구간의 0은 실제 한산함을 뜻하지 않습니다.')
            self._snapshot = CongestionSnapshot(tuple(zones), source, datetime.now(timezone.utc).isoformat(), warnings)
            self._expires = monotonic() + self.config.congestion_ttl_seconds
            self._cache[key] = (self._expires, self._snapshot)
            while len(self._cache) > 8: self._cache.popitem(last=False)
            return self._snapshot
