import type { PlaceOption } from '../types'
// Coordinates for the bundled OSM walking network; no generated routes here.
export const placeOptions: PlaceOption[] = [
  { id: 'yeouido-start', name: '여의도 출발 지점', position: { lat: 37.521, lng: 126.924 } },
  { id: 'yeouido-end', name: '여의도 도착 지점', position: { lat: 37.528, lng: 126.932 } },
  { id: 'yeouido-station', name: '여의도역 인근', position: { lat: 37.5219, lng: 126.9245 } },
  { id: 'yeouinaru', name: '여의나루역 인근', position: { lat: 37.527, lng: 126.9328 } },
]
