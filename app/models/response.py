from pydantic import BaseModel, Field

class RouteSegment(BaseModel):
    congestion: float
    geometry: list[tuple[float, float]]

class RouteMetrics(BaseModel):
    distance_m: float
    estimated_time_min: float
    average_congestion: float
    max_congestion: float
    congested_distance_m: float
    high_congestion_zone_count: int
    congestion_exposure_m: float
    geometry: list[tuple[float, float]]
    segments: list[RouteSegment] = Field(default_factory=list)

class Comparison(BaseModel):
    extra_distance_m: float
    extra_distance_percent: float
    extra_time_min: float
    congestion_reduction_percent: float

class RouteMetadata(BaseModel):
    preference: str
    requested_alpha: float
    applied_alpha: float
    detour_limited: bool
    congestion_source: str
    congestion_fetched_at: str
    warnings: list[str]
    snapped_start: tuple[float, float]
    snapped_end: tuple[float, float]
    start_snap_distance_m: float
    end_snap_distance_m: float

class RouteResponse(BaseModel):
    shortest: RouteMetrics
    recommended: RouteMetrics
    comparison: Comparison
    metadata: RouteMetadata
    congestion_zones: list[dict] = Field(default_factory=list, description="GeoJSON Features from the exact congestion snapshot used by this route")
