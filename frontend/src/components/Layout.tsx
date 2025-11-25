import { Link, useLocation } from 'react-router-dom'
import './Layout.css'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

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
          </div>
        </div>
      </nav>
      <main className="main-content">{children}</main>
    </div>
  )
}
