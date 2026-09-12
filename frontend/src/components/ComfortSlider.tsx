import { preferenceFor } from '../services/api'
type Props = { value: number; onChange: (value: number) => void; compact?: boolean }
export default function ComfortSlider({ value, onChange, compact = false }: Props) {
  const options = [{value: 0, label: '빠르게', key: 'fastest'}, {value: 0.5, label: '균형 있게', key: 'balanced'}, {value: 1, label: '쾌적하게', key: 'comfortable'}]
  return <div className={`comfort-control ${compact ? 'comfort-control--compact' : ''}`}>
    <div className="comfort-control__heading"><span className="eyebrow">경로 우선순위</span></div>
    <div className="preference-options" role="group" aria-label="경로 성향">
      {options.map(option => <button key={option.key} type="button" aria-pressed={preferenceFor(value) === option.key}
        className={preferenceFor(value) === option.key ? 'active' : ''} onClick={() => onChange(option.value)}>{option.label}</button>)}
    </div>
    {!compact && <p className="comfort-copy">시간과 혼잡도 사이에서 원하는 이동 방식을 선택하세요.</p>}
  </div>
}
