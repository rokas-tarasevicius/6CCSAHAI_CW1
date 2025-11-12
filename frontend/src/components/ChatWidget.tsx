import { useState } from 'react'
import { questionsApi } from '../services/api'
import type { Question } from '../types'
import './ChatWidget.css'

const imgSearch = "http://localhost:3845/assets/9176bc6fe6ea4f6fa95d47d65fecd816aa9c5d86.svg"

interface ChatWidgetProps {
  question: Question
  selectedAnswer: number
  isCorrect: boolean
}

export default function ChatWidget({
  question,
  selectedAnswer,
  isCorrect,
}: ChatWidgetProps) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userQuestion = input.trim()
    setInput('')
    setLoading(true)

    try {
      const response = await questionsApi.getExplanation(
        question.question_text,
        question.answers.find((a) => a.is_correct)?.text || '',
        question.answers[selectedAnswer]?.text || '',
        isCorrect,
        question.topic,
        question.subtopic,
        question.concepts,
        question.explanation,
        userQuestion
      )
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: userQuestion },
        { role: 'assistant', content: response },
      ])
    } catch (error) {
      console.error('Failed to get explanation:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="ai-input-container">
      <div className="ai-input">
        <div className="search-icon">
          <img src={imgSearch} alt="Search" />
        </div>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask AI..."
          disabled={loading}
          className="ai-input-field"
        />
      </div>
      {messages.length > 0 && (
        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.role}`}>
              <p>{msg.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
