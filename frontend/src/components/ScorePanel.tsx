import type { Performance } from '../types'
import './ScorePanel.css'

const imgVector = "http://localhost:3845/assets/b086553be9d7f7cefeee97b195317b51e7ec2626.svg"

interface ScorePanelProps {
  performance: Performance
}

export default function ScorePanel({ performance }: ScorePanelProps) {
  const score = performance.trophy_score || 0
  const level = Math.max(1, Math.floor(score / 100))
  const nextLevel = (level + 1) * 100
  const remaining = Math.max(0, nextLevel - score)

  return (
    <div className="score-panel">
      <div className="score-group">
        <div className="score-value">{score}</div>
        <div className="level-value">{level}</div>
        <img src={imgVector} alt="Trophy" className="trophy-icon" />
        <div className="progress-text">
          <span>{remaining} until </span>
          <span className="bold">Grand Master</span>
        </div>
      </div>
    </div>
  )
}
