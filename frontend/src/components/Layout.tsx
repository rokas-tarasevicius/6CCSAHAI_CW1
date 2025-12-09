import { Link, useLocation } from 'react-router-dom'
import { useRating } from '../contexts/RatingContext'
import './Layout.css'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const { rating } = useRating()

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="navbar-container">
          <Link to="/" className="navbar-brand">
            Platform
          </Link>
          <div className="navbar-links">
            <Link
              to="/courses"
              className={location.pathname === '/courses' ? 'active' : ''}
            >
              Upload
            </Link>
            <Link
              to="/"
              className={location.pathname === '/' ? 'active' : ''}
            >
              Quiz
            </Link>
            <Link
              to="/videos"
              className={location.pathname === '/videos' ? 'active' : ''}
            >
              AI slop
            </Link>
            <Link
              to="/profile"
              className={location.pathname === '/profile' ? 'active' : ''}
            >
              Profile
              <span className="navbar-rating">{Math.round(rating)}</span>
            </Link>
          </div>
        </div>
      </nav>
      <main className="main-content">{children}</main>
    </div>
  )
}
