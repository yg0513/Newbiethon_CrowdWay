import type { Polygon, MultiPolygon } from 'geojson'

export type LatLng = { lat: number; lng: number }
export type PlaceOption = { id: string; name: string; position: LatLng }
export type CongestionLevel = '여유' | '보통' | '약간 붐빔' | '붐빔'

export type CongestionArea = {
  id: string
  place: string
  level: CongestionLevel
  score: number
  observedAt?: string
  message?: string
  replaced?: boolean
  populationMin?: number
  populationMax?: number
  geometry: Polygon | MultiPolygon
}

export type RouteSegment = {
  congestion: number
  geometry: LatLng[]
}

export type RoutePath = {
  id: 'fastest' | 'comfortable'
  title: string
  distance: number
  time: number
  congestionExposure: number
  congestedZones: number
  geometry: LatLng[]
  segments: RouteSegment[]
  maxCongestion: number
  congestedDistance: number
  exposureMeters: number
}

export type RouteResult = {
  fastest: RoutePath
  comfortable: RoutePath
  congestion: CongestionArea[]
  comparison: {
    extra_distance_m: number
    extra_distance_percent: number
    extra_time_min: number
    congestion_reduction_percent: number
  }
  metadata: {
    preference: string
    requested_alpha: number
    applied_alpha: number
    detour_limited: boolean
    congestion_source: string
    congestion_fetched_at: string
    warnings: string[]
    snapped_start: [number, number]
    snapped_end: [number, number]
    start_snap_distance_m: number
    end_snap_distance_m: number
  }
}

export type SearchState = { start: PlaceOption; end: PlaceOption; avoidCrowd: number }
