import { Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { usePerformanceStore } from '../store/usePerformanceStore'
import { courseApi } from '../services/api'
import ScorePanel from '../components/ScorePanel'
import './HomePage.css'

export default function HomePage() {
  const { performance } = usePerformanceStore()
  const [hasContent, setHasContent] = useState<boolean>(false)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    checkForContent()
  }, [])

  const checkForContent = async () => {
    try {
      setLoading(true)
      const data = await courseApi.getCourse()
      const hasFiles = data.files && Object.keys(data.files).length > 0
      setHasContent(hasFiles)
    } catch (err: any) {
      setHasContent(false)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="home-page">
        <div className="welcome-section">
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="home-page">
      {!hasContent ? (
        <div className="welcome-section">
          <h2>Welcome to the Adaptive Learning Platform</h2>
          <p>To get started, please upload your course materials first.</p>
          <p>Upload PDF files to create personalized quizzes and video content.</p>
          <Link to="/courses" className="btn-primary">
            Upload Course Material
          </Link>
        </div>
      ) : performance.total_questions_answered === 0 ? (
        <div className="welcome-section">
          <h2>Welcome to the Adaptive Learning Platform</h2>
          <p>Your course materials are ready! Start your personalized quiz now.</p>
          <div className="action-buttons">
            <Link to="/quiz" className="btn-primary">
              Start Quiz
            </Link>
            <Link to="/courses" className="btn-secondary">
              Manage Courses
            </Link>
          </div>
        </div>
      ) : (
        <div className="dashboard-content">
          <ScorePanel performance={performance} />
        </div>
      )}
    </div>
  )
}
