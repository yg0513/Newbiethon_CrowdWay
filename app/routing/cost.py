from math import isfinite

def calculate_edge_cost(distance: float, congestion: float, alpha: float) -> float:
    """Quadratic penalty emphasizes highly congested edges."""
    if not all(isfinite(v) for v in (distance, congestion, alpha)):
        raise ValueError('비용 입력은 유한한 수여야 합니다.')
    if distance < 0 or alpha < 0 or not 0 <= congestion <= 1:
        raise ValueError('거리/alpha는 음수가 아니고 혼잡도는 0~1이어야 합니다.')
    return distance * (1 + alpha * congestion ** 2)
