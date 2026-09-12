import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import BrandLogo from '../components/BrandLogo'
import ComfortSlider from '../components/ComfortSlider'
import PlacePickerMap from '../components/PlacePickerMap'
import type { PlaceOption, LatLng } from '../types'

type SearchPlace = PlaceOption & { address?: string }

export default function SearchPage() {
  const navigate = useNavigate()
  const [start, setStart] = useState<SearchPlace | null>(null)
  const [end, setEnd] = useState<SearchPlace | null>(null)
  const [target, setTarget] = useState<'start' | 'end'>('start')
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchPlace[]>([])
  const [searched, setSearched] = useState(false)
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState('장소 이름을 검색해 출발지와 도착지를 선택하세요.')
  const [error, setError] = useState('')
  const [focus, setFocus] = useState<LatLng | null>(null)
  const [avoidCrowd, setAvoidCrowd] = useState(1)
  const [locating, setLocating] = useState(false)
  const controller = useRef<AbortController | null>(null)

  useEffect(() => () => controller.current?.abort(), [])

  const invalid = !start || !end || (start.position.lat === end.position.lat && start.position.lng === end.position.lng)

  const pick = (place: SearchPlace) => {
    if (target === 'start') setStart(place)
    else setEnd(place)
    setFocus(place.position)
    setError('')
  }

  const pickPoint = (point: LatLng) => {
    if (!(point.lat >= 37.35 && point.lat <= 37.75 && point.lng >= 126.70 && point.lng <= 127.25)) {
      setError('서울 및 인접 지역 안에서 위치를 선택해주세요.')
      return
    }
    pick({
      id: `map-${point.lat}-${point.lng}`,
      name: `지도 선택 위치`,
      position: point,
    })
  }


  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      setError('이 브라우저에서는 GPS 위치 기능을 사용할 수 없어요.')
      return
    }

    setLocating(true)
    setError('')
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const point = { lat: position.coords.latitude, lng: position.coords.longitude }
        if (!(point.lat >= 37.35 && point.lat <= 37.75 && point.lng >= 126.70 && point.lng <= 127.25)) {
          setError('현재 위치가 서울 및 인접 지역 밖으로 확인됐어요.')
          setLocating(false)
          return
        }
        const place: SearchPlace = { id: 'gps-current', name: '내 현재 위치', position: point }
        setStart(place)
        setTarget('end')
        setFocus(point)
        setNotice('현재 위치를 출발지로 설정했어요. 결과 화면에서는 GPS 위치가 실시간으로 갱신됩니다.')
        setLocating(false)
      },
      (geoError) => {
        const message = geoError.code === geoError.PERMISSION_DENIED
          ? '현재 위치를 사용하려면 브라우저의 위치 권한을 허용해주세요.'
          : '현재 위치를 확인하지 못했어요. 잠시 후 다시 시도해주세요.'
        setError(message)
        setLocating(false)
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 3000 },
    )
  }

  async function search(event: React.FormEvent) {
    event.preventDefault()
    if (query.trim().length < 2) {
      setError('두 글자 이상 입력해주세요.')
      return
    }

    controller.current?.abort()
    const request = new AbortController()
    controller.current = request
    setLoading(true)
    setError('')
    setResults([])
    setSearched(false)

    try {
      const response = await fetch(
        `${(import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')}/places/search?q=${encodeURIComponent(query.trim())}`,
        { signal: request.signal },
      )
      const data = await response.json()
      if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : '검색에 실패했습니다.')

      if (!request.signal.aborted) {
        setResults(data.results)
        setNotice(data.warning || '검색 결과에서 장소를 선택하세요.')
        setSearched(true)
        if (data.results[0]) setFocus(data.results[0].position)
      }
    } catch (err) {
      if (!request.signal.aborted) setError(err instanceof Error ? err.message : '검색에 실패했습니다.')
    } finally {
      if (!request.signal.aborted) setLoading(false)
    }
  }

  return (
    <main className="page-shell search-page">
      <header className="app-header">
        <button className="icon-button" onClick={() => navigate('/')} aria-label="이전 화면">←</button>
        <BrandLogo compact />
        <div className="header-spacer" />
      </header>

      <section className="search-content search-content--wide">
        <div className="search-intro">
          <span className="eyebrow">서울 도보 길찾기</span>
          <h1>어디로 갈까요?</h1>
          <p>장소 이름을 검색하거나 현재 위치를 출발지로 사용하세요.</p>
        </div>

        <div className="place-search-layout">
          <div className="search-panel">
            <div className="chosen-places">
              <button className={target === 'start' ? 'chosen-place active' : 'chosen-place'} aria-pressed={target === 'start'} onClick={() => setTarget('start')}>
                <small>출발지 선택</small>
                <strong>{start?.name ?? '출발지를 선택하세요'}</strong>
              </button>
              <button className="ghost-button" onClick={() => { setStart(end); setEnd(start) }} aria-label="출발지와 도착지 바꾸기">⇅ 바꾸기</button>
              <button className={target === 'end' ? 'chosen-place active' : 'chosen-place'} aria-pressed={target === 'end'} onClick={() => setTarget('end')}>
                <small>도착지 선택</small>
                <strong>{end?.name ?? '도착지를 선택하세요'}</strong>
              </button>
            </div>

            <button type="button" className="gps-start-button" onClick={useCurrentLocation} disabled={locating}>
              <span className="gps-start-button__icon" aria-hidden="true">◎</span>
              <span><strong>{locating ? '현재 위치 확인 중…' : '내 현재 위치를 출발지로'}</strong><small>GPS를 사용해 현재 위치를 바로 설정합니다.</small></span>
            </button>

            <form className="place-search-form" onSubmit={search}>
              <label htmlFor="place-query">장소·지역 검색</label>
              <div>
                <input
                  id="place-query"
                  value={query}
                  maxLength={100}
                  placeholder="예: 강남역, 서울숲, 경복궁"
                  onChange={(e) => {
                    controller.current?.abort()
                    setLoading(false)
                    setQuery(e.target.value)
                    setResults([])
                    setSearched(false)
                  }}
                />
                <button className="secondary-button" disabled={loading || query.trim().length < 2}>{loading ? '검색 중…' : '검색'}</button>
              </div>
            </form>

            <p className="data-source-note">{notice}</p>
            {error && <p className="inline-error" role="alert">{error}</p>}
            {searched && results.length === 0 && <p role="status">검색 결과가 없습니다. 다른 이름으로 검색하거나 지도에서 선택하세요.</p>}

            <ul className="place-results">
              {results.map((place) => (
                <li key={place.id}>
                  <button onClick={() => pick(place)}>
                    <strong>{place.name}</strong>
                    <small>{place.address || '검색된 장소'}</small>
                    <span>{target === 'start' ? '출발지' : '도착지'}로 선택</span>
                  </button>
                </li>
              ))}
            </ul>

            <ComfortSlider value={avoidCrowd} onChange={setAvoidCrowd} />
            <button className="primary-button primary-button--large" disabled={invalid} onClick={() => navigate('/result', { state: { start, end, avoidCrowd } })}>길찾기 →</button>
            <p className="data-source-note">새 지역은 도보 지도를 처음 준비하는 데 시간이 걸릴 수 있어요. 혼잡도는 서울시가 관측하는 지역에 한해 반영됩니다.</p>
          </div>

          <section className="picker-panel" aria-label="출발지와 도착지를 선택하는 지도">
            <div className="picker-hint">지도에서 클릭하면 <strong>{target === 'start' ? '출발지' : '도착지'}</strong>로 지정됩니다.</div>
            <PlacePickerMap start={start} end={end} focus={focus} onPick={pickPoint} />
          </section>
        </div>
      </section>
    </main>
  )
}
