import { useEffect, useMemo } from 'react'
import {
  ZoomControl,
  Circle,
  CircleMarker,
  MapContainer,
  Polyline,
  TileLayer,
  Tooltip,
  useMap,
} from 'react-leaflet'
import L from 'leaflet'
import type { CongestionArea, LatLng, RouteResult } from '../types'

type GpsStatus = 'idle' | 'locating' | 'active' | 'denied' | 'error'

type MapViewProps = {
  start: LatLng
  end: LatLng
  startName: string
  endName: string
  routes: RouteResult
  congestion: CongestionArea[]
  selectedRoute: 'fastest' | 'comfortable'
  onSelectRoute: (route: 'fastest' | 'comfortable') => void
  currentPosition?: LatLng | null
  currentAccuracy?: number | null
  gpsStatus?: GpsStatus
  onEnableGps?: () => void
}

const spotColor: Record<CongestionArea['level'], string> = {
  여유: '#16a34a',
  보통: '#ca8a04',
  '약간 붐빔': '#ea580c',
  붐빔: '#dc2626',
}

function FitBounds({ points }: { points: LatLng[] }) {
  const map = useMap()

  useEffect(() => {
    if (!points.length) return
    const bounds = L.latLngBounds(points.map((point) => [point.lat, point.lng] as [number, number]))
    map.fitBounds(bounds, { padding: [34, 34] })
  }, [map, points])

  return null
}

function toTuple(points: LatLng[]): [number, number][] {
  return points.map((point) => [point.lat, point.lng])
}

function collectCoordinates(value: unknown, output: LatLng[]) {
  if (!Array.isArray(value)) return
  if (value.length >= 2 && typeof value[0] === 'number' && typeof value[1] === 'number') {
    output.push({ lng: value[0], lat: value[1] })
    return
  }
  value.forEach((child) => collectCoordinates(child, output))
}

function centerOfArea(area: CongestionArea): LatLng | null {
  const points: LatLng[] = []
  collectCoordinates(area.geometry.coordinates, points)
  if (!points.length) return null
  return {
    lat: points.reduce((sum, point) => sum + point.lat, 0) / points.length,
    lng: points.reduce((sum, point) => sum + point.lng, 0) / points.length,
  }
}

function formatPopulation(area: CongestionArea) {
  if (area.populationMin == null || area.populationMax == null) return null
  return `${area.populationMin.toLocaleString('ko-KR')}~${area.populationMax.toLocaleString('ko-KR')}명`
}

function SpotTooltip({ area }: { area: CongestionArea }) {
  const population = formatPopulation(area)
  return (
    <Tooltip sticky>
      <strong>{area.place}</strong>
      <br />혼잡도 {area.level}
      {population && <><br />예상 인구 {population}</>}
      {area.observedAt && <><br />관측 {area.observedAt}</>}
    </Tooltip>
  )
}

export default function MapView({
  start,
  end,
  startName,
  endName,
  routes,
  congestion,
  selectedRoute,
  onSelectRoute,
  currentPosition = null,
  currentAccuracy = null,
  gpsStatus = 'idle',
  onEnableGps,
}: MapViewProps) {
  const allPoints = useMemo(() => [...routes.fastest.geometry, ...routes.comfortable.geometry], [routes])
  const activeRoute = selectedRoute === 'fastest' ? routes.fastest : routes.comfortable
  const inactiveRoute = selectedRoute === 'fastest' ? routes.comfortable : routes.fastest

  const gpsText = gpsStatus === 'active'
    ? `실시간 GPS${currentAccuracy ? ` · ±${Math.round(currentAccuracy)}m` : ''}`
    : gpsStatus === 'locating'
      ? '현재 위치 확인 중…'
      : gpsStatus === 'denied'
        ? '위치 권한 필요'
        : gpsStatus === 'error'
          ? 'GPS 연결 실패'
          : '내 위치 표시'

  return (
    <div className="map-shell">
      <MapContainer
        center={[start.lat, start.lng]}
        zoom={16}
        scrollWheelZoom
        touchZoom
        doubleClickZoom
        zoomControl={false}
        className="map-container"
      >
        <ZoomControl position="topright" />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <FitBounds points={allPoints} />

        {congestion.map((area) => {
          const center = centerOfArea(area)
          if (!center) return null
          return (
            <CircleMarker
              key={`${area.id}-${area.score}`}
              center={[center.lat, center.lng]}
              radius={12}
              pathOptions={{
                color: spotColor[area.level],
                fillColor: '#ffffff',
                fillOpacity: 0.92,
                opacity: 0.95,
                weight: 4,
                dashArray: '2 5',
              }}
            >
              <SpotTooltip area={area} />
            </CircleMarker>
          )
        })}

        <Polyline
          positions={toTuple(inactiveRoute.geometry)}
          pathOptions={{ color: '#64748b', weight: 4, opacity: 0.48, dashArray: '8 10' }}
          eventHandlers={{ click: () => onSelectRoute(inactiveRoute.id) }}
        />

        <Polyline
          positions={toTuple(activeRoute.geometry)}
          pathOptions={{ color: '#ffffff', weight: 11, opacity: 0.92, lineCap: 'round', lineJoin: 'round' }}
          eventHandlers={{ click: () => onSelectRoute(activeRoute.id) }}
        />
        <Polyline
          positions={toTuple(activeRoute.geometry)}
          pathOptions={{ color: '#0f766e', weight: 7, opacity: 0.98, lineCap: 'round', lineJoin: 'round' }}
          eventHandlers={{ click: () => onSelectRoute(activeRoute.id) }}
        />

        <CircleMarker center={[start.lat, start.lng]} radius={8} pathOptions={{ color: '#0f172a', fillColor: '#ffffff', fillOpacity: 1, weight: 4 }}>
          <Tooltip permanent direction="top" offset={[0, -8]}>{startName}</Tooltip>
        </CircleMarker>
        <CircleMarker center={[end.lat, end.lng]} radius={8} pathOptions={{ color: '#0f766e', fillColor: '#ffffff', fillOpacity: 1, weight: 4 }}>
          <Tooltip permanent direction="bottom" offset={[0, 8]}>{endName}</Tooltip>
        </CircleMarker>

        {currentPosition && <>
          {currentAccuracy && currentAccuracy > 0 && (
            <Circle
              center={[currentPosition.lat, currentPosition.lng]}
              radius={Math.min(currentAccuracy, 150)}
              pathOptions={{ color: '#2563eb', fillColor: '#60a5fa', fillOpacity: 0.10, opacity: 0.35, weight: 1 }}
            />
          )}
          <CircleMarker
            center={[currentPosition.lat, currentPosition.lng]}
            radius={8}
            pathOptions={{ color: '#ffffff', fillColor: '#2563eb', fillOpacity: 1, weight: 4 }}
          >
            <Tooltip direction="top" offset={[0, -7]}>내 현재 위치 · 실시간 GPS</Tooltip>
          </CircleMarker>
        </>}
      </MapContainer>

      <div className="map-legend">
        <strong>서울시 혼잡 스팟</strong>
        <div><i className="legend-dot legend-dot--green" />여유</div>
        <div><i className="legend-dot legend-dot--yellow" />보통</div>
        <div><i className="legend-dot legend-dot--orange" />약간 붐빔</div>
        <div><i className="legend-dot legend-dot--red" />붐빔</div>
      </div>

      <div className="route-legend">
        <strong>{selectedRoute === 'fastest' ? '빠른 길' : '추천 길'} 표시 중</strong>
        <div><i className="route-line route-line--comfort" />청록색 실선은 선택 경로</div>
        <div><i className="route-line route-line--inactive" />회색 점선은 비교 경로</div>
      </div>

      <div className={`gps-map-card gps-map-card--${gpsStatus}`}>
        <span className="gps-live-dot" aria-hidden="true" />
        <strong>{gpsText}</strong>
        {gpsStatus !== 'active' && onEnableGps && (
          <button type="button" onClick={onEnableGps} disabled={gpsStatus === 'locating'}>
            {gpsStatus === 'locating' ? '확인 중' : 'GPS 켜기'}
          </button>
        )}
      </div>
    </div>
  )
}
