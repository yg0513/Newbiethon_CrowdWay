import { useNavigate } from 'react-router-dom'

type BrandLogoProps = {
  compact?: boolean
}

export default function BrandLogo({ compact = false }: BrandLogoProps) {
  const navigate = useNavigate()

  return (
    <button type="button" className={`brand-logo brand-logo-button ${compact ? 'brand-logo--compact' : ''}`} aria-label="CrowdWay 홈으로 이동" onClick={() => navigate('/')}>
      <svg viewBox="0 0 72 72" role="img" aria-hidden="true">
        <path d="M13 51c10-21 17-29 27-29 7 0 11 4 18 14" className="logo-path logo-path--back" />
        <path d="M14 53c12-11 21-14 33-10 5 2 8 5 12 11" className="logo-path logo-path--front" />
        <circle cx="20" cy="47" r="4" className="logo-dot" />
        <circle cx="56" cy="54" r="4" className="logo-dot" />
      </svg>
      <div>
        <strong>CrowdWay</strong>
        {!compact && <span>혼잡을 피하는 도보 길찾기</span>}
      </div>
    </button>
  )
}
