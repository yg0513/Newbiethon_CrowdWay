import { useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import BrandLogo from '../components/BrandLogo'
import ComfortSlider from '../components/ComfortSlider'
import MapView from '../components/MapView'
import RouteCard from '../components/RouteCard'
import { placeOptions } from '../data/places'
import { getRoutes, preferenceFor } from '../services/api'
import type { CongestionArea, LatLng, RouteResult, SearchState } from '../types'

type GpsStatus = 'idle' | 'locating' | 'active' | 'denied' | 'error'

function collectCoordinates(value: unknown, output: LatLng[]) {
  if (!Array.isArray(value)) return
  if (value.length >= 2 && typeof value[0] === 'number' && typeof value[1] === 'number') {
    output.push({ lng: value[0], lat: value[1] })
    return
  }
  value.forEach((child) => collectCoordinates(child, output))
}

function zoneCenter(zone: CongestionArea): LatLng | null {
  const points: LatLng[] = []
  collectCoordinates(zone.geometry.coordinates, points)
  if (!points.length) return null
  const lat = points.reduce((sum, point) => sum + point.lat, 0) / points.length
  const lng = points.reduce((sum, point) => sum + point.lng, 0) / points.length
  return { lat, lng }
}

function distanceToRoute(zone: CongestionArea, route: LatLng[]) {
  const center = zoneCenter(zone)
  if (!center || !route.length) return Number.POSITIVE_INFINITY
  return Math.min(...route.map((point) => {
    const latScale = Math.cos((center.lat * Math.PI) / 180)
    const dx = (point.lng - center.lng) * latScale
    const dy = point.lat - center.lat
    return dx * dx + dy * dy
  }))
}

function formatPopulation(zone: CongestionArea) {
  if (zone.populationMin == null || zone.populationMax == null) return '예상 인구 정보 없음'
  return `${zone.populationMin.toLocaleString('ko-KR')}~${zone.populationMax.toLocaleString('ko-KR')}명`
}

export default function ResultPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const initial = useRef((location.state as SearchState | null) ?? { start: placeOptions[0], end: placeOptions[1], avoidCrowd: 1 }).current
  const [avoidCrowd, setAvoidCrowd] = useState(initial.avoidCrowd)
  const [applied, setApplied] = useState(initial.avoidCrowd)
  const [routes, setRoutes] = useState<RouteResult | null>(null)
  const [selectedRoute, setSelectedRoute] = useState<'fastest' | 'comfortable'>('comfortable')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [gpsPosition, setGpsPosition] = useState<LatLng | null>(initial.start.id === 'gps-current' ? initial.start.position : null)
  const [gpsAccuracy, setGpsAccuracy] = useState<number | null>(null)
  const [gpsStatus, setGpsStatus] = useState<GpsStatus>('idle')
  const active = useRef<AbortController | null>(null)
  const gpsWatchId = useRef<number | null>(null)

  async function load(value: number) {
    active.current?.abort()
    const controller = new AbortController()
    active.current = controller
    setLoading(true)
    setError('')
    setRoutes(null)
    try {
      const result = await getRoutes(initial.start.position, initial.end.position, value, controller.signal)
      if (!controller.signal.aborted) {
        setRoutes(result)
        setApplied(value)
      }
    } catch (err) {
      if (!controller.signal.aborted) setError(err instanceof Error ? err.message : '경로 요청에 실패했습니다.')
    } finally {
      if (!controller.signal.aborted) setLoading(false)
    }
  }

  const startGpsWatch = () => {
    if (!navigator.geolocation) {
      setGpsStatus('error')
      return
    }
    if (gpsWatchId.current !== null) return

    setGpsStatus('locating')
    gpsWatchId.current = navigator.geolocation.watchPosition(
      (position) => {
        setGpsPosition({ lat: position.coords.latitude, lng: position.coords.longitude })
        setGpsAccuracy(position.coords.accuracy)
        setGpsStatus('active')
      },
      (geoError) => {
        setGpsStatus(geoError.code === geoError.PERMISSION_DENIED ? 'denied' : 'error')
        if (gpsWatchId.current !== null) {
          navigator.geolocation.clearWatch(gpsWatchId.current)
          gpsWatchId.current = null
        }
      },
      { enableHighAccuracy: true, maximumAge: 2000, timeout: 15000 },
    )
  }

  useEffect(() => {
    void load(initial.avoidCrowd)
    if (initial.start.id === 'gps-current') startGpsWatch()
    return () => {
      active.current?.abort()
      if (gpsWatchId.current !== null) navigator.geolocation.clearWatch(gpsWatchId.current)
    }
  }, [])

  const extra = routes ? Number(routes.comparison.extra_time_min.toFixed(1)) : 0
  const reduction = routes ? Number(routes.comparison.congestion_reduction_percent.toFixed(1)) : 0
  const source = routes?.metadata.congestion_source
  const hasCrowding = source === 'mock' || source === 'fallback_mock' || (source === 'seoul' && !!routes?.congestion.length)
  const snappedStart = routes ? { lng: routes.metadata.snapped_start[0], lat: routes.metadata.snapped_start[1] } : initial.start.position
  const snappedEnd = routes ? { lng: routes.metadata.snapped_end[0], lat: routes.metadata.snapped_end[1] } : initial.end.position

  const nearbyCongestion = useMemo(() => {
    if (!routes) return []
    const route = selectedRoute === 'fastest' ? routes.fastest.geometry : routes.comfortable.geometry
    return [...routes.congestion]
      .sort((a, b) => distanceToRoute(a, route) - distanceToRoute(b, route))
      .slice(0, 5)
  }, [routes, selectedRoute])

  return (
    <main className="result-page">
      <header className="result-header">
        <div className="result-header__inner">
          <button className="icon-button" onClick={() => navigate('/search')} aria-label="검색 화면으로 돌아가기">←</button>
          <BrandLogo compact />
          <div className="route-title"><span>{initial.start.name}</span><b>→</b><span>{initial.end.name}</span></div>
          <button className="ghost-button" onClick={() => navigate('/search')}>경로 변경</button>
        </div>
      </header>

      <div className="result-layout">
        <aside className="result-sidebar">
          <div className="result-sidebar__intro">
            <span className="eyebrow">추천 결과</span>
            <h1>조금 돌아가도,<br />덜 붐비게.</h1>
            {routes && hasCrowding && <p>추가 <strong>{extra}분</strong> · 혼잡 노출 {reduction >= 0 ? '감소' : '증가'} <strong>{Math.abs(reduction)}%</strong></p>}
            {routes && !hasCrowding && <p>혼잡 데이터를 확보하면 회피 경로를 비교할 수 있어요.</p>}
          </div>

          <ComfortSlider value={avoidCrowd} onChange={setAvoidCrowd} compact />
          <button className="secondary-button" disabled={loading || (!error && preferenceFor(avoidCrowd) === preferenceFor(applied))} onClick={() => void load(avoidCrowd)}>이 기준으로 다시 계산</button>

          {loading && <div className="loading-card" role="status"><span className="loading-spinner" /><div><strong>도보 경로를 계산하고 있어요</strong><p>최초 지도 다운로드는 시간이 걸릴 수 있어요.</p></div></div>}
          {error && <div className="error-card" role="alert"><strong>경로를 불러오지 못했어요.</strong><p>{error}</p><button onClick={() => void load(avoidCrowd)}>다시 시도</button></div>}

          {routes && <section className="result-section result-section--routes">
            <div className="result-section__heading">
              <div><span className="eyebrow">경로 정보</span><h2>어떤 길로 갈까요?</h2></div>
            </div>

            <div className="route-card-list route-card-list--top">
              <RouteCard crowdingAvailable={hasCrowding} route={routes.fastest} selected={selectedRoute === 'fastest'} onSelect={() => setSelectedRoute('fastest')} />
              <RouteCard crowdingAvailable={hasCrowding} route={routes.comfortable} selected={selectedRoute === 'comfortable'} onSelect={() => setSelectedRoute('comfortable')} differenceMinutes={hasCrowding ? extra : undefined} exposureReduction={hasCrowding ? reduction : undefined} />
            </div>

            <div className="why-card">
              <span className="eyebrow">경로 비교</span>
              <ul>
                <li>최단경로 대비 {routes.comparison.extra_distance_m.toFixed(0)}m 추가 ({routes.comparison.extra_distance_percent.toFixed(1)}%).</li>
                <li>지도에서 청록색 실선은 선택한 경로, 회색 점선은 비교 경로입니다.</li>
                {routes.metadata.detour_limited && <li>우회 한도를 지키기 위해 혼잡 회피 강도를 낮췄어요.</li>}
                {routes.comparison.extra_distance_m === 0 && reduction === 0 && <li>현재 기준에서는 최단경로와 추천경로가 같아요.</li>}
              </ul>
            </div>
          </section>}

          {routes && <section className="result-section result-section--crowding">
            <div className="result-section__heading">
              <div><span className="eyebrow">서울시 실시간 혼잡 데이터</span><h2>경로 주변 혼잡 현황</h2></div>
              <span className="nearby-count">가까운 5곳</span>
            </div>

            {source === 'seoul' && nearbyCongestion.length > 0 ? (
              <div className="crowding-spot-list">
                {nearbyCongestion.map((zone) => (
                  <article className="crowding-spot-card" key={zone.id}>
                    <div className="crowding-spot-card__top">
                      <strong>{zone.place}</strong>
                      <span className={`crowding-level crowding-level--${zone.level.replace(' ', '-')}`}>{zone.level}</span>
                    </div>
                    <div className="crowding-spot-card__population">{formatPopulation(zone)}</div>
                    <div className="crowding-spot-card__meta">
                      <span>{zone.observedAt ? `관측 ${zone.observedAt}` : '관측 시각 없음'}</span>
                      {zone.replaced && <span>대체 데이터</span>}
                    </div>
                    {zone.message && <p>{zone.message}</p>}
                  </article>
                ))}
              </div>
            ) : (
              <div className="live-crowding-card live-crowding-card--warning">
                <strong>{source === 'seoul' ? '경로 주변에 표시할 서울시 관측 장소가 없어요.' : '현재 서울시 실시간 혼잡 데이터를 불러오지 못했어요.'}</strong>
                {routes.metadata.warnings.map((warning) => <p className="live-error-copy" key={warning}>{warning}</p>)}
              </div>
            )}
          </section>}
        </aside>

        <section className="result-map-area">
          {routes ? (
            <MapView
              start={snappedStart}
              end={snappedEnd}
              startName={initial.start.name}
              endName={initial.end.name}
              routes={routes}
              congestion={routes.congestion}
              selectedRoute={selectedRoute}
              onSelectRoute={setSelectedRoute}
              currentPosition={gpsPosition}
              currentAccuracy={gpsAccuracy}
              gpsStatus={gpsStatus}
              onEnableGps={startGpsWatch}
            />
          ) : (
            <div className="map-placeholder">
              {loading && <span className="loading-spinner" />}
              <p>{error ? '검색 조건을 확인한 뒤 다시 시도해주세요.' : '지도를 준비하고 있어요.'}</p>
            </div>
          )}

          {routes && hasCrowding && <div className="map-summary-card"><span className="map-summary-card__icon">🌿</span><div><small>추천 경로 비교</small><strong>+{extra}분 · 혼잡 노출 {Math.abs(reduction)}% {reduction >= 0 ? '감소' : '증가'}</strong></div></div>}
        </section>
      </div>
    </main>
  )
}
