import { Link } from 'react-router-dom'
import { usePerformanceStore } from '../store/usePerformanceStore'
import './HomePage.css'

export default function HomePage() {
  const { performance, resetPerformance } = usePerformanceStore()

  return (
    <div className="home-page">
      <div className="subject-header">
        <h1 className="subject-title">HUMAN AI INTERACTION / PROTOTYPING</h1>
      </div>

      {performance.total_questions_answered === 0 ? (
        <div className="welcome-section">
          <p>Welcome to the Adaptive Learning Platform</p>
          <Link to="/quiz" className="btn-primary">
            Start Quiz
          </Link>
        </div>
      ) : (
        <div className="dashboard-content">
          <ScorePanel performance={performance} />
        </div>
      )}
    </div>
  )
}
