import type { RoutePath } from '../types'

function formatMinutes(seconds: number) {
  return (seconds / 60).toFixed(1)
}

function formatDistance(meters: number) {
  return meters >= 1000 ? `${(meters / 1000).toFixed(2)}km` : `${Math.round(meters)}m`
}

type RouteCardProps = {
  crowdingAvailable?: boolean
  route: RoutePath
  selected: boolean
  onSelect: () => void
  differenceMinutes?: number
  exposureReduction?: number
}

export default function RouteCard({
  route,
  crowdingAvailable = true,
  selected,
  onSelect,
  differenceMinutes,
  exposureReduction,
}: RouteCardProps) {
  return (
    <button className={`route-card ${selected ? 'route-card--selected' : ''}`} onClick={onSelect}>
      <div className="route-card__top">
        <div>
          <span className="route-card__icon">{route.id === 'comfortable' ? '🌿' : '🚶'}</span>
          <strong>{route.title}</strong>
        </div>
        {selected && <span className="selected-pill">선택됨</span>}
      </div>

      <div className="route-card__numbers">
        <strong>{formatMinutes(route.time)}분</strong>
        <span>{formatDistance(route.distance)}</span>
      </div>

      <div className="exposure-row">
        <span>거리 가중 평균 혼잡도</span>
        <strong>{crowdingAvailable ? `${Math.round(route.congestionExposure * 100)}%` : '데이터 없음'}</strong>
      </div>
      {crowdingAvailable && <div className="exposure-bar" aria-hidden="true">
        <span style={{ width: `${crowdingAvailable ? `${Math.round(route.congestionExposure * 100)}%` : '데이터 없음'}` }} />
      </div>}

      {crowdingAvailable && <div className="route-card__meta"><span>혼잡 구간 {Math.round(route.congestedDistance)}m</span><span>최고 혼잡도 {Math.round(route.maxCongestion * 100)}%</span></div>}
      <div className="route-card__meta">
        <span>{crowdingAvailable ? `혼잡지역 ${route.congestedZones}곳` : '혼잡도 미확보 · 거리 기준 경로'}</span>
        {route.id === 'comfortable' && differenceMinutes !== undefined && exposureReduction !== undefined && (
          <span className="route-card__gain">+{differenceMinutes}분 · 노출 감소 {exposureReduction}%</span>
        )}
      </div>
    </button>
  )
}
