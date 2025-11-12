import type { Question } from '../types'
import './QuestionCard.css'

interface QuestionCardProps {
  question: Question
  selectedAnswer: number | null
  isAnswered: boolean
  onAnswerSelect: (index: number) => void
  onSubmit: () => void
}

export default function QuestionCard({
  question,
  selectedAnswer,
  isAnswered,
  onAnswerSelect,
  onSubmit,
}: QuestionCardProps) {
  const correctAnswerIndex = question.answers.findIndex((ans) => ans.is_correct)

  return (
    <div className="question-card">
      <h2 className="question-text">{question.question_text}</h2>

      <div className="mcq-choices">
        {question.answers.map((answer, index) => {
          const isSelected = selectedAnswer === index
          const isCorrect = answer.is_correct
          const showResult = isAnswered

          let className = 'mcq-choice'
          if (showResult) {
            if (isCorrect) {
              className += ' mcq-correct'
            } else if (isSelected && !isCorrect) {
              className += ' mcq-incorrect'
            } else {
              className += ' mcq-default'
            }
          } else if (isSelected) {
            className += ' mcq-selected'
          } else {
            className += ' mcq-default'
          }

          return (
            <button
              key={index}
              className={className}
              onClick={() => onAnswerSelect(index)}
              disabled={isAnswered}
            >
              <span className="mcq-text">{answer.text}</span>
            </button>
          )
        })}
      </div>

      {!isAnswered && selectedAnswer !== null && (
        <button onClick={onSubmit} className="btn-submit">
          Submit Answer
        </button>
      )}
    </div>
  )
}
