"""Synthetic Yeouido polygons; these are not official boundaries or live values."""
from shapely.geometry import box
from app.congestion.provider import CongestionZone

def get_mock_zones() -> list[CongestionZone]:
    return [
        CongestionZone('여의도 데모 혼잡구역 A', 1.0, box(126.9255, 37.5220, 126.9280, 37.5240), '붐빔'),
        CongestionZone('여의도 데모 혼잡구역 B', 0.7, box(126.9305, 37.5260, 126.9330, 37.5290), '약간 붐빔'),
    ]
