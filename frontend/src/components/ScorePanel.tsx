import type { Performance } from '../types'
import { shouldShowScoreChange, isPositiveChange } from '../utils/scoreChange'
import './ScorePanel.css'

interface ScorePanelProps {
  performance: Performance
  scoreChange?: number
}

export default function ScorePanel({ performance, scoreChange }: ScorePanelProps) {
  const score = performance.trophy_score || 0
  const level = Math.max(1, Math.floor(score / 100))
  const nextLevel = (level + 1) * 100
  const remaining = Math.max(0, nextLevel - score)
  
  const showChange = shouldShowScoreChange(scoreChange)
  const isPositive = isPositiveChange(scoreChange)

  return (
    <div className="score-panel">
      <div className="score-group">
        <div className="score-value-container">
          <div className="score-value">{score}</div>
          {showChange && (
            <div className={`score-change ${isPositive ? 'positive' : 'negative'}`}>
              <span className="change-arrow">{isPositive ? '↑' : '↓'}</span>
              <span className="change-value">{Math.abs(scoreChange)}</span>
            </div>
          )}
        </div>
        <div className="progress-text">
          <span>{remaining} until </span>
          <span className="bold">Grand Master</span>
        </div>
      </div>
    </div>
  )
}
