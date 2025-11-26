import { Link, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { usePerformanceStore } from '../store/usePerformanceStore'
import { useQuizSelection } from '../contexts/QuizSelectionContext'
import { courseApi } from '../services/api'
import ScorePanel from '../components/ScorePanel'
import './HomePage.css'

export default function HomePage() {
  const navigate = useNavigate()
  const { performance } = usePerformanceStore()
  const { selectedQuizFiles, totalQuestions, getSelectedFilePaths } = useQuizSelection()
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

  const handleStartQuiz = () => {
    if (selectedQuizFiles.length === 0) {
      // If no files selected, use adaptive quiz mode (existing behavior)
      navigate('/quiz')
    } else {
      // Use file-based quiz with selected files
      const selectedFilePaths = getSelectedFilePaths()
      navigate('/quiz', { 
        state: { 
          fileBasedQuiz: true,
          selectedFilePaths: selectedFilePaths,
          totalQuestions: totalQuestions
        }
      })
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
          
          {selectedQuizFiles.length > 0 && (
            <div className="selected-quiz-info">
              <h3>Selected Quiz Files</h3>
              <p>{`${selectedQuizFiles.length} file${selectedQuizFiles.length > 1 ? 's' : ''} selected with ${totalQuestions} question${totalQuestions > 1 ? 's' : ''}`}</p>
              <ul className="selected-files-list">
                {selectedQuizFiles.map((file) => (
                  <li key={file.filePath}>
                    {file.fileName} ({file.questionCount} questions)
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="action-buttons">
            <button onClick={handleStartQuiz} className="btn-primary">
              {selectedQuizFiles.length > 0 ? 'Start Selected Quiz' : 'Start Adaptive Quiz'}
            </button>
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
