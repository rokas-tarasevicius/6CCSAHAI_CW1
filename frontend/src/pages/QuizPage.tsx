import { useState, useEffect } from 'react'
import { usePerformanceStore } from '../store/usePerformanceStore'
import { questionsApi, performanceApi } from '../services/api'
import { calculateScoreChange } from '../utils/scoreChange'
import type { Question } from '../types'
import QuestionCard from '../components/QuestionCard'
import ScorePanel from '../components/ScorePanel'
import ChatWidget from '../components/ChatWidget'
import './QuizPage.css'

const imgVector = "http://localhost:3845/assets/b086553be9d7f7cefeee97b195317b51e7ec2626.svg"

export default function QuizPage() {
  const { performance, setPerformance } = usePerformanceStore()
  const [question, setQuestion] = useState<Question | null>(null)
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null)
  const [isAnswered, setIsAnswered] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showExplanation, setShowExplanation] = useState(false)
  const [scoreChange, setScoreChange] = useState<number | undefined>(undefined)

  useEffect(() => {
    loadQuestion()
  }, [])

  const loadQuestion = async () => {
    setLoading(true)
    setError(null)
    setShowExplanation(false)
    setScoreChange(undefined) // Reset score change when loading new question
    try {
      const newQuestion = await questionsApi.generateQuestion(performance)
      setQuestion(newQuestion)
      setSelectedAnswer(null)
      setIsAnswered(false)
    } catch (err: any) {
      setError(err.message || 'Failed to load question')
    } finally {
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
    setShowExplanation(true)
  }

  const handleNext = () => {
    loadQuestion()
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
      <div className="subject-header">
        <h1 className="subject-title">HUMAN AI INTERACTION / PROTOTYPING</h1>
        {!showExplanation && (
          <button className="btn-ai-slop">
            AI Slop
          </button>
        )}
        {showExplanation && (
          <button onClick={handleNext} className="btn-next">
            Next Question
          </button>
        )}
      </div>

      <div className="quiz-content">
        <div className="quiz-left-pane">
          <div className="question-section">
            <QuestionCard
              question={question}
              selectedAnswer={selectedAnswer}
              isAnswered={isAnswered}
              onAnswerSelect={handleAnswerSelect}
              onSubmit={handleSubmit}
            />
          </div>

          {showExplanation && (
            <div className="explanation-section">
              <div className="explanation-text">
                {question.explanation}
              </div>
              <ChatWidget
                question={question}
                selectedAnswer={selectedAnswer!}
                isCorrect={question.answers[selectedAnswer!]?.is_correct || false}
              />
            </div>
          )}
        </div>
        
        <div className="rating-pane">
          <ScorePanel performance={performance} scoreChange={scoreChange} />
        </div>
      </div>
    </div>
  )
}
