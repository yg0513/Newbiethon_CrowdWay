"""Environment settings; .env is loaded without overriding shell variables."""
import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')

class Settings(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    use_mock_congestion: bool = True
    seoul_api_key: str = Field(default='', repr=False)
    seoul_api_service: Literal['citydata_ppltn', 'citydata'] = 'citydata_ppltn'
    seoul_area_codes: str = ''
    seoul_max_age_minutes: float = Field(default=60, gt=0)
    seoul_api_base_url: str = 'http://openapi.seoul.go.kr:8088'
    seoul_zones_file: str = 'data/seoul_zones.geojson'
    congestion_fallback: Literal['mock', 'empty'] = 'empty'
    congestion_ttl_seconds: float = Field(default=60, gt=0)
    api_timeout_seconds: float = Field(default=10, gt=0)
    max_detour_ratio: float = Field(default=1.30, ge=1)
    walking_speed_kmh: float = Field(default=4.5, gt=0)
    high_congestion_threshold: float = Field(default=0.7, gt=0, le=1)
    graph_min_radius_m: float = Field(default=1500, gt=0)
    graph_buffer_m: float = Field(default=1000, gt=0)
    graph_max_radius_m: float = Field(default=10000, gt=0)
    graph_cache_size: int = Field(default=4, ge=1)
    max_snap_distance_m: float = Field(default=500, gt=0)
    osm_timeout_seconds: int = Field(default=90, gt=0)
    graphml_path: str = ''
    kakao_rest_api_key: str = Field(default='', repr=False)

    @classmethod
    def from_env(cls) -> 'Settings':
        return cls(**{name: os.environ[name.upper()] for name in cls.model_fields if name.upper() in os.environ})

settings = Settings.from_env()
ALPHAS = {'fastest': 0.0, 'balanced': 1.0, 'comfortable': 3.0}
MAX_DETOUR_RATIO = settings.max_detour_ratio
WALKING_SPEED_KMH = settings.walking_speed_kmh
HIGH_CONGESTION_THRESHOLD = settings.high_congestion_threshold
