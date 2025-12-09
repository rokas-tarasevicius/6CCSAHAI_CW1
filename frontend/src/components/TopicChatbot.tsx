import { useState, useRef, useEffect } from 'react'
import { chatbotApi } from '../services/api'
import type { Question } from '../types'
import './TopicChatbot.css'

interface TopicChatbotProps {
  question: Question | null
}

export default function TopicChatbot({ question }: TopicChatbotProps) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([])
  const responseRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (responseRef.current) {
      responseRef.current.scrollTop = responseRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading || !question) return

    const userQuestion = input.trim()
    const correctAnswer = question.answers.find((a) => a.is_correct)?.text || ''
    setInput('')
    setLoading(true)

    try {
      setMessages((prev) => [...prev, { role: 'user', content: userQuestion }])
      const result = await chatbotApi.ask({
        question: userQuestion,
        quiz_question: question.question_text,
        correct_answer: correctAnswer,
        topic: question.topic,
        subtopic: question.subtopic,
        concepts: question.concepts,
      })
      setMessages((prev) => [...prev, { role: 'assistant', content: result.answer }])
    } catch (error: any) {
      console.error('Failed to get chatbot response:', error)
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (!question) {
    return (
      <div className="topic-chatbot">
        <div className="chatbot-placeholder">
          <p>Start a quiz to ask questions about the topic</p>
        </div>
      </div>
    )
  }

  return (
    <div className="topic-chatbot">
      <div className="chatbot-response-area" ref={responseRef}>
        {messages.length === 0 && (
          <div className="chatbot-welcome">
            <p>Ask me anything about <strong>{question.topic}</strong>!</p>
            {question.concepts && question.concepts.length > 0 && (
              <p className="chatbot-concepts">
                Related concepts: {question.concepts.join(', ')}
              </p>
            )}
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.role}`}>
            <p className="chatbot-response-text">{msg.content}</p>
          </div>
        ))}
        {loading && (
          <div className="chatbot-loading">
            <p>Thinking...</p>
          </div>
        )}
      </div>
      
      <div className="chatbot-input-container">
        <div className="ai-input">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask AI..."
            disabled={loading}
            className="ai-input-field"
          />
        </div>
      </div>
    </div>
  )
}
