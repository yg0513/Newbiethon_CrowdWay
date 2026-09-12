import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import ResultPage from './pages/ResultPage'
import SearchPage from './pages/SearchPage'
import SplashPage from './pages/SplashPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SplashPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/result" element={<ResultPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
