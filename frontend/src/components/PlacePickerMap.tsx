import { useEffect } from 'react'
import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap, useMapEvents } from 'react-leaflet'
import type { PlaceOption, LatLng } from '../types'
type Props = { start: PlaceOption | null; end: PlaceOption | null; focus: LatLng | null; onPick: (point: LatLng) => void }
function Controls({focus, onPick}: Pick<Props,'focus'|'onPick'>) {
  const map = useMap()
  useMapEvents({click: e => onPick({lat: e.latlng.lat, lng: e.latlng.lng})})
  useEffect(() => { if (focus) map.setView([focus.lat,focus.lng],16) }, [map,focus])
  useEffect(() => { const observer = new ResizeObserver(() => map.invalidateSize()); observer.observe(map.getContainer()); return () => observer.disconnect() }, [map])
  return null
}
export default function PlacePickerMap({start,end,focus,onPick}: Props) {
  return <MapContainer className="place-picker-map" center={[37.5665,126.978]} zoom={12} scrollWheelZoom={false}>
    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>' />
    <Controls focus={focus} onPick={onPick} />
    {start && <CircleMarker center={[start.position.lat,start.position.lng]} radius={9} pathOptions={{color:'#334155',fillOpacity:1}}><Tooltip permanent direction="top">출발 · {start.name}</Tooltip></CircleMarker>}
    {end && <CircleMarker center={[end.position.lat,end.position.lng]} radius={9} pathOptions={{color:'#0f766e',fillOpacity:1}}><Tooltip permanent direction="bottom">도착 · {end.name}</Tooltip></CircleMarker>}
  </MapContainer>
}
