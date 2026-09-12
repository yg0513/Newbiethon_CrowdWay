import { useNavigate } from 'react-router-dom'
import BrandLogo from '../components/BrandLogo'

export default function SplashPage() {
  const navigate = useNavigate()

  return (
    <main className="splash-page page-shell">
      <div className="splash-orb splash-orb--one" />
      <div className="splash-orb splash-orb--two" />

      <section className="splash-card">
        <BrandLogo />
        <div className="splash-copy">
          <span className="eyebrow">실시간 혼잡 회피 도보 길찾기</span>
          <h1>사람 많은 길 대신,<br />조금 더 여유로운 길로.</h1>
          <p>도로의 혼잡도를 비교해 나에게 맞는 도보 경로를 찾아드려요.</p>
        </div>

        <button className="primary-button primary-button--large" onClick={() => navigate('/search')}>
          시작하기
          <span aria-hidden="true">→</span>
        </button>
      </section>
    </main>
  )
}
