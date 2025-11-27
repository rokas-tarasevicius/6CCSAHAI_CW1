import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { questionsApi } from '../services/api'
import type { Question } from '../types'
import QuestionCard from '../components/QuestionCard'
import './QuizPage.css'

export default function QuizPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const [hasContent, setHasContent] = useState<boolean | null>(null)
  const [question, setQuestion] = useState<Question | null>(null)
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
  const [isAnswered, setIsAnswered] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // File-based quiz state
  const [allQuestions, setAllQuestions] = useState<Question[]>([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)

  useEffect(() => {
    // Check if this is a file-based quiz from navigation state
    const state = location.state as any
    if (state?.fileBasedQuiz && state?.selectedFilePaths) {
      loadFileBasedQuiz(state.selectedFilePaths, state.maxQuestions)
    } else {
      // No adaptive mode - redirect to courses if no files selected
      setError('Please select quiz files from the courses page')
      setHasContent(false)
    }
  }, [location.state])

  const loadFileBasedQuiz = async (selectedFilePaths: string[], maxQuestions?: number) => {
    try {
      setLoading(true)
      setError(null)
      
      // Call the API endpoint to get combined quiz questions
      const questions = await questionsApi.startFileBasedQuiz(selectedFilePaths, maxQuestions)
      setAllQuestions(questions)
      setCurrentQuestionIndex(0)
      
      // Set the first question
      if (questions.length > 0) {
        setQuestion(questions[0])
        setHasContent(true)
      } else {
        setError('No questions found in selected files')
        setHasContent(false)
      }
    } catch (err: any) {
      console.error('Failed to load file-based quiz:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to load quiz')
      setHasContent(false)
    } finally {
      setLoading(false)
    }
  }

  const loadNextFileBasedQuestion = () => {
    const nextIndex = currentQuestionIndex + 1
    if (nextIndex < allQuestions.length) {
      setCurrentQuestionIndex(nextIndex)
      setQuestion(allQuestions[nextIndex])
      setSelectedAnswer(null)
      setIsAnswered(false)
    } else {
      // Quiz completed - show completion screen
      setQuestion(null)
      setHasContent(null) // This will trigger a completion screen
    }
  }

  const handleAnswerSelect = (index: number) => {
    if (!isAnswered) {
      setSelectedAnswer(index)
    }
  }

  const handleSubmit = async () => {
    if (selectedAnswer === null || !question) return
    setIsAnswered(true)
  }

  const handleNext = async () => {
    // Check if this is the last question
    const isLastQuestion = currentQuestionIndex >= allQuestions.length - 1
    
    if (isLastQuestion) {
      // Navigate directly to dashboard on quiz completion
      navigate('/')
    } else {
      // Load next question
      loadNextFileBasedQuestion()
    }
  }

  // Check if content exists first
  if (hasContent === false) {
    return (
      <div className="quiz-page">
        <div className="no-content">
          <h2>No Quiz Selected</h2>
          <p>You need to select quiz files before you can take a quiz.</p>
          <p>Please select files from the courses page to get started.</p>
          <Link to="/courses" className="btn-primary">
            Select Quiz Files
          </Link>
        </div>
      </div>
    )
  }

  if (loading || hasContent === null) {
    return (
      <div className="quiz-page">
        <div className="loading">Loading your quiz...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="quiz-page">
        <div className="error">{error}</div>
        <Link to="/courses" className="btn-primary">
          Back to Courses
        </Link>
      </div>
    )
  }

  if (!question) {
    if (allQuestions.length > 0) {
      // Show completion screen for file-based quiz
      return (
        <div className="quiz-page">
          <div className="quiz-completed">
            <h2>Quiz Completed! 🎉</h2>
            <p>You've successfully completed the quiz with {allQuestions.length} questions.</p>
            <div className="completion-actions">
              <Link to="/courses" className="btn-primary">
                Back to Courses
              </Link>
              <Link to="/" className="btn-secondary">
                Go to Dashboard
              </Link>
            </div>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="quiz-page">
      <div className="quiz-content">
        <div className="quiz-left-pane">
          <div className="quiz-progress">
            <h3>Quiz Progress</h3>
            <div className="progress-info">
              Question {currentQuestionIndex + 1} of {allQuestions.length}{" "}
              <span className="progress-percentage">
                ({Math.round((currentQuestionIndex / allQuestions.length) * 100)}%)
              </span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ 
                  width: `${Math.round((currentQuestionIndex / allQuestions.length) * 100)}%` 
                }}
              ></div>
            </div>
          </div>
          
          <div className="question-section">
            <QuestionCard
              question={question}
              selectedAnswer={selectedAnswer}
              isAnswered={isAnswered}
              onAnswerSelect={handleAnswerSelect}
              onSubmit={handleSubmit}
              onNext={handleNext}
              isLastQuestion={currentQuestionIndex >= allQuestions.length - 1}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
