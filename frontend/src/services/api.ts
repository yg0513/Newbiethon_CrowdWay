import type { CongestionArea, LatLng, RoutePath, RouteResult } from '../types'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export function preferenceFor(value: number): 'fastest' | 'balanced' | 'comfortable' {
  return value < 0.34 ? 'fastest' : value < 0.67 ? 'balanced' : 'comfortable'
}

type BackendSegment = {
  congestion: number
  geometry: [number, number][]
}

type BackendRoute = {
  distance_m: number
  estimated_time_min: number
  average_congestion: number
  max_congestion: number
  congested_distance_m: number
  high_congestion_zone_count: number
  congestion_exposure_m: number
  geometry: [number, number][]
  segments?: BackendSegment[]
}

function adaptRoute(route: BackendRoute, id: RoutePath['id']): RoutePath {
  return {
    id,
    title: id === 'fastest' ? '빠른 길' : '추천 길',
    distance: route.distance_m,
    time: route.estimated_time_min * 60,
    congestionExposure: route.average_congestion,
    congestedZones: route.high_congestion_zone_count,
    maxCongestion: route.max_congestion,
    congestedDistance: route.congested_distance_m,
    exposureMeters: route.congestion_exposure_m,
    geometry: route.geometry.map(([lng, lat]) => ({ lat, lng })),
    segments: (route.segments ?? []).map((segment) => ({
      congestion: segment.congestion,
      geometry: segment.geometry.map(([lng, lat]) => ({ lat, lng })),
    })),
  }
}

export async function getRoutes(start: LatLng, end: LatLng, avoidCrowd: number, signal?: AbortSignal): Promise<RouteResult> {
  const response = await fetch(`${API_BASE_URL}/route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    signal,
    body: JSON.stringify({
      start: { lat: start.lat, lon: start.lng },
      end: { lat: end.lat, lon: end.lng },
      preference: preferenceFor(avoidCrowd),
    }),
  })

  const data = await response.json().catch(() => null)
  if (!response.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : '입력 좌표와 서버 상태를 확인해주세요.')
  if (!data?.shortest || !data?.recommended) throw new Error('경로 응답 형식이 올바르지 않습니다.')

  const zones: CongestionArea[] = (data.congestion_zones ?? []).map((feature: {
    properties: {
      name: string
      score: number
      level: CongestionArea['level']
      observed_at?: string
      message?: string
      replaced?: boolean
      population_min?: number
      population_max?: number
    }
    geometry: CongestionArea['geometry']
  }, i: number) => ({
    id: `${i}-${feature.properties.name}`,
    place: feature.properties.name,
    score: feature.properties.score,
    level: feature.properties.level,
    observedAt: feature.properties.observed_at,
    message: feature.properties.message,
    replaced: feature.properties.replaced,
    populationMin: feature.properties.population_min,
    populationMax: feature.properties.population_max,
    geometry: feature.geometry,
  }))

  return {
    fastest: adaptRoute(data.shortest, 'fastest'),
    comfortable: adaptRoute(data.recommended, 'comfortable'),
    comparison: data.comparison,
    metadata: data.metadata,
    congestion: zones,
  }
}
