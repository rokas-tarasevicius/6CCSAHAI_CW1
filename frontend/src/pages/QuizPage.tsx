import { useState, useEffect } from 'react'
import { usePerformanceStore } from '../store/usePerformanceStore'
import { questionsApi, performanceApi } from '../services/api'
import { calculateScoreChange } from '../utils/scoreChange'
import type { Question } from '../types'
import QuestionCard from '../components/QuestionCard'
import ScorePanel from '../components/ScorePanel'
import './QuizPage.css'

export default function QuizPage() {
  const { performance, setPerformance } = usePerformanceStore()
  const [question, setQuestion] = useState<Question | null>(null)
  const [cachedQuestion, setCachedQuestion] = useState<Question | null>(null)
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
  const [isAnswered, setIsAnswered] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [scoreChange, setScoreChange] = useState<number | undefined>(undefined)

  useEffect(() => {
    loadQuestion()
  }, [])

  // Pre-generate next question in the background (async, non-blocking)
  const preloadNextQuestion = async (performanceData?: typeof performance) => {
    try {
      const perfData = performanceData || performance
      const nextQuestion = await questionsApi.generateQuestion(perfData)
      setCachedQuestion(nextQuestion)
    } catch (err) {
      // Silently fail - we'll generate on demand if preload fails
      console.error('Failed to preload next question:', err)
    }
  }

  // Start pre-generating next question when a question is displayed
  useEffect(() => {
    if (question) {
      // Start pre-generating the next question asynchronously (only if not already cached)
      // This runs whenever a new question is displayed, using current performance data
      if (!cachedQuestion) {
        // Use current performance from store (will be updated after submit)
        preloadNextQuestion(performance)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question])

  const loadQuestion = async () => {
    setLoading(true)
    setError(null)
    setScoreChange(undefined) // Reset score change when loading new question
    
    try {
      // Use cached question if available, otherwise generate new one
      let newQuestion: Question | null = null
      
      if (cachedQuestion) {
        // Use cached question immediately
        newQuestion = cachedQuestion
        setCachedQuestion(null) // Clear cache
      } else {
        // Generate new question
        console.log('Generating new question...')
        newQuestion = await questionsApi.generateQuestion(performance)
        console.log('Question generated:', newQuestion)
      }
      
      if (newQuestion) {
        setQuestion(newQuestion)
        setSelectedAnswer(null)
        setIsAnswered(false)
        setLoading(false)
        // Pre-generation will be triggered by useEffect when question is set
      } else {
        throw new Error('Failed to get question')
      }
    } catch (err: any) {
      console.error('Error loading question:', err)
      setError(err?.response?.data?.detail || err?.message || 'Failed to load question')
      setLoading(false)
    }
  }

  const handleAnswerSelect = (index: number) => {
    if (!isAnswered) {
      setSelectedAnswer(index)
    }
  }

  const handleSubmit = async () => {
    if (selectedAnswer === null || !question) return

    const isCorrect = question.answers[selectedAnswer]?.is_correct || false
    const previousScore = performance.trophy_score || 0
    
    // Update performance
    try {
      const updatedPerformance = await performanceApi.recordAnswer(
        performance,
        question.topic,
        question.subtopic,
        question.concepts[0] || '',
        isCorrect
      )
      
      // Calculate score change using utility function
      const newScore = updatedPerformance.trophy_score || 0
      const change = calculateScoreChange(previousScore, newScore)
      
      // Update performance state first
      setPerformance(updatedPerformance)
      
      // Then set score change (this will trigger re-render with new score)
      setScoreChange(change)
    } catch (err) {
      console.error('Failed to record answer:', err)
    }

    setIsAnswered(true)
    // Pre-generation happens automatically via useEffect when question is displayed
  }

  const handleNext = async () => {
    // If we have a cached question, use it immediately (no loading)
    if (cachedQuestion) {
      setQuestion(cachedQuestion)
      setCachedQuestion(null) // Clear cache
      setSelectedAnswer(null)
      setIsAnswered(false)
      setScoreChange(undefined)
      // Pre-generation will be triggered by useEffect when question is set
    } else {
      // No cached question, show loading and generate on demand
      loadQuestion()
    }
  }

  if (loading) {
    return (
      <div className="quiz-page">
        <div className="loading">Generating your question...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="quiz-page">
        <div className="error">{error}</div>
        <button onClick={loadQuestion} className="btn-primary">
          Retry
        </button>
      </div>
    )
  }

  if (!question) {
    return null
  }

  return (
    <div className="quiz-page">
      <div className="quiz-content">
        <div className="quiz-left-pane">
          <div className="question-section">
            <QuestionCard
              question={question}
              selectedAnswer={selectedAnswer}
              isAnswered={isAnswered}
              onAnswerSelect={handleAnswerSelect}
              onSubmit={handleSubmit}
              onNext={handleNext}
            />
          </div>
        </div>
        
        <div className="rating-pane">
          <ScorePanel performance={performance} scoreChange={scoreChange} />
        </div>
      </div>
    </div>
  )
}
