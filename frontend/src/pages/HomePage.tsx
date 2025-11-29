import { Link, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { useQuizSelection } from '../contexts/QuizSelectionContext'
import { courseApi } from '../services/api'
import type { ParsedDataResponse } from '../types'
import './HomePage.css'

export default function HomePage() {
  const navigate = useNavigate()
  const { selectedQuizFiles, totalQuestions, getSelectedFilePaths, addQuizFile, removeQuizFile, isQuizSelected, selectAllQuizFiles, deselectAllQuizFiles } = useQuizSelection()
  const [hasContent, setHasContent] = useState<boolean>(false)
  const [loading, setLoading] = useState<boolean>(true)
  const [maxQuestions, setMaxQuestions] = useState<number | ''>('')
  const [parsedData, setParsedData] = useState<ParsedDataResponse | null>(null)

  useEffect(() => {
    checkForContent()
  }, [])

  const checkForContent = async () => {
    try {
      setLoading(true)
      const data = await courseApi.getCourse()
      const hasFiles = data.files && Object.keys(data.files).length > 0
      setHasContent(hasFiles)
      setParsedData(data)
    } catch (err: any) {
      setHasContent(false)
    } finally {
      setLoading(false)
    }
  }

  const handleFileToggle = (filePath: string, fileName: string, questionCount: number) => {
    if (isQuizSelected(filePath)) {
      removeQuizFile(filePath)
    } else {
      addQuizFile(filePath, fileName, questionCount)
    }
  }

  const handleSelectAll = () => {
    if (!parsedData) return
    const filesWithQuiz = Object.entries(parsedData.files)
      .filter(([_, fileData]) => fileData.quiz && fileData.quiz.length > 0)
      .map(([filePath, fileData]) => ({
        filePath,
        fileName: fileData.metadata.file_name,
        questionCount: fileData.quiz?.length || 0
      }))
    selectAllQuizFiles(filesWithQuiz)
  }

  const handleDeselectAll = () => {
    deselectAllQuizFiles()
  }

  const handleStartQuiz = () => {
    if (selectedQuizFiles.length === 0) {
      // No files selected - redirect to courses page
      navigate('/courses')
    } else {
      // Use file-based quiz with selected files
      const selectedFilePaths = getSelectedFilePaths()
      const questionLimit = typeof maxQuestions === 'number' && maxQuestions > 0 ? maxQuestions : undefined
      
      navigate('/quiz', { 
        state: { 
          fileBasedQuiz: true,
          selectedFilePaths: selectedFilePaths,
          totalQuestions: totalQuestions,
          maxQuestions: questionLimit
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
      ) : (
        <div className="welcome-section">
          <h2>Welcome to the File-Based Quiz Platform</h2>
          <p>Your course materials are ready! Start your quiz now.</p>
          
          {parsedData && Object.keys(parsedData.files).length > 0 && (
            <div className="selected-quiz-info">
              <h3>Selected Quiz Files</h3>
              <p>{`${selectedQuizFiles.length} file${selectedQuizFiles.length > 1 ? 's' : ''} selected with ${totalQuestions} question${totalQuestions > 1 ? 's' : ''}`}</p>
              
              <div className="selected-files-actions">
                <button 
                  className="btn-select-all-small"
                  onClick={handleSelectAll}
                >
                  Select All
                </button>
                <button 
                  className="btn-deselect-all-small"
                  onClick={handleDeselectAll}
                >
                  Deselect All
                </button>
              </div>

              <ul className="selected-files-list">
                {Object.entries(parsedData.files)
                  .filter(([_, fileData]) => fileData.quiz && fileData.quiz.length > 0)
                  .map(([filePath, fileData]) => {
                    const isSelected = isQuizSelected(filePath)
                    return (
                      <li key={filePath} className={isSelected ? 'selected' : ''}>
                        <span className="file-name-text">
                          {fileData.metadata.file_name} ({fileData.quiz?.length || 0} questions)
                        </span>
                        <button
                          className="btn-file-toggle"
                          onClick={() => handleFileToggle(filePath, fileData.metadata.file_name, fileData.quiz?.length || 0)}
                          title={isSelected ? 'Deselect' : 'Select'}
                        >
                          {isSelected ? '✓' : '☐'}
                        </button>
                      </li>
                    )
                  })}
              </ul>
              
              <div className="quiz-options">
                <label htmlFor="max-questions">
                  Limit questions to:
                </label>
                <input
                  id="max-questions"
                  type="number"
                  min="1"
                  max={totalQuestions}
                  value={maxQuestions}
                  onChange={(e) => setMaxQuestions(e.target.value === '' ? '' : parseInt(e.target.value))}
                  placeholder={`All ${totalQuestions} questions`}
                  className="question-limit-input"
                />
                <span className="input-hint">Leave empty to use all questions</span>
              </div>
            </div>
          )}
          
          <div className="action-buttons">
            <button onClick={handleStartQuiz} className="btn-primary">
              {selectedQuizFiles.length > 0 ? 'Start Selected Quiz' : 'Select Quiz Files First'}
            </button>
            <Link to="/courses" className="btn-secondary">
              Manage Courses
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
