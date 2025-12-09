import { useState, useEffect, useCallback } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { questionsApi, quizProgressApi, type IncorrectConceptRef } from '../services/api'
import type { Question } from '../types'
import QuestionCard from '../components/QuestionCard'
import TopicChatbot from '../components/TopicChatbot'
import { useRating } from '../contexts/RatingContext'
import './QuizPage.css'

export default function QuizPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { updateRating } = useRating()
  const [hasContent, setHasContent] = useState<boolean | null>(null)
  const [question, setQuestion] = useState<Question | null>(null)
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
  const [isAnswered, setIsAnswered] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [incorrectConcepts, setIncorrectConcepts] = useState<IncorrectConceptRef[]>([])
  const [isCompleted, setIsCompleted] = useState(false)
  
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

  const loadNextFileBasedQuestion = useCallback(() => {
    const nextIndex = currentQuestionIndex + 1
    if (nextIndex < allQuestions.length) {
      setCurrentQuestionIndex(nextIndex)
      setQuestion(allQuestions[nextIndex])
      setSelectedAnswer(null)
      setIsAnswered(false)
    } else {
      // Quiz completed - show completion screen
      setQuestion(null)
      setIsCompleted(true)
    }
  }, [currentQuestionIndex, allQuestions])

  const handleAnswerSelect = (index: number) => {
    if (!isAnswered) {
      setSelectedAnswer(index)
    }
  }

  const handleSubmit = async () => {
    if (selectedAnswer === null || !question) return
    
    // Check if answer is correct
    const selectedAnswerObj = question.answers[selectedAnswer]
    const isCorrect = selectedAnswerObj?.is_correct || false
    const concept = question.concepts?.[0]
    
    // Update rating based on correctness
    if (isCorrect) {
      await updateRating(10) // +10 for correct answer
    } else {
      await updateRating(-5) // -5 for incorrect answer
      if (concept) {
        setIncorrectConcepts((prev) => {
          const exists = prev.some(
            (c) => c.topic === question.topic && c.subtopic === question.subtopic && c.concept === concept
          )
          if (exists) return prev
          return [...prev, { topic: question.topic, subtopic: question.subtopic, concept }]
        })
      }
    }
    
    setIsAnswered(true)
  }

  const handleNext = useCallback(async () => {
    // Check if this is the last question
    const isLastQuestion = currentQuestionIndex >= allQuestions.length - 1
    
    if (isLastQuestion) {
      try {
        await quizProgressApi.completeQuiz(incorrectConcepts)
      } catch (err) {
        console.error('Failed to store incorrect concepts', err)
      }
      // Show completion screen instead of redirecting immediately
      setQuestion(null)
      setIsCompleted(true)
    } else {
      // Load next question
      loadNextFileBasedQuestion()
    }
  }, [currentQuestionIndex, allQuestions.length, loadNextFileBasedQuestion, incorrectConcepts])

  // Auto-advance to next question after 3 seconds when answered
  useEffect(() => {
    if (isAnswered && question) {
      const timer = setTimeout(() => {
        handleNext()
      }, 3000) // 3 seconds

      return () => {
        clearTimeout(timer)
      }
    }
  }, [isAnswered, question, handleNext])

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

  if (isCompleted) {
    return (
      <div className="quiz-page">
        <div className="quiz-completed">
          <h2>Quiz Completed! 🎉</h2>
          <p>You've successfully completed the quiz with {allQuestions.length} questions.</p>
          <div className="incorrect-concepts">
            <h3>Concepts to review</h3>
            {incorrectConcepts.length === 0 ? (
              <p>Great job! No incorrect concepts this time.</p>
            ) : (
              <ul>
                {incorrectConcepts.map((c) => (
                  <li key={`${c.topic}-${c.subtopic}-${c.concept}`}>
                    <strong>{c.concept}</strong> — {c.topic} / {c.subtopic}
                  </li>
                ))}
              </ul>
            )}
          </div>
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

  if (!question) return null

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
        
        <div className="quiz-right-pane">
          <TopicChatbot question={question} />
        </div>
      </div>
    </div>
  )
}
