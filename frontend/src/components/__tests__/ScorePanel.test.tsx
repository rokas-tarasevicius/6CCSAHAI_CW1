import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ScorePanel from '../ScorePanel'
import type { Performance } from '../../types'

describe('ScorePanel', () => {
  const mockPerformance: Performance = {
    total_questions_answered: 10,
    total_correct: 7,
    total_incorrect: 3,
    trophy_score: 55,
    overall_accuracy: 70,
    topic_scores: {},
  }

  it('should display the trophy score', () => {
    render(<ScorePanel performance={mockPerformance} />)
    expect(screen.getByText('55')).toBeInTheDocument()
  })

  it('should calculate and display the correct level', () => {
    render(<ScorePanel performance={mockPerformance} />)
    expect(screen.getByText('1')).toBeInTheDocument() // 55 / 100 = level 1
  })

  it('should not show score change indicator when scoreChange is undefined', () => {
    render(<ScorePanel performance={mockPerformance} />)
    const changeIndicator = screen.queryByText(/↑|↓/)
    expect(changeIndicator).not.toBeInTheDocument()
  })

  it('should not show score change indicator when scoreChange is 0', () => {
    render(<ScorePanel performance={mockPerformance} scoreChange={0} />)
    const changeIndicator = screen.queryByText(/↑|↓/)
    expect(changeIndicator).not.toBeInTheDocument()
  })

  it('should show positive score change with up arrow', () => {
    render(<ScorePanel performance={mockPerformance} scoreChange={10} />)
    expect(screen.getByText('↑')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('should show negative score change with down arrow', () => {
    render(<ScorePanel performance={mockPerformance} scoreChange={-5} />)
    expect(screen.getByText('↓')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('should apply positive class for positive score change', () => {
    const { container } = render(<ScorePanel performance={mockPerformance} scoreChange={10} />)
    const changeElement = container.querySelector('.score-change.positive')
    expect(changeElement).toBeInTheDocument()
  })

  it('should apply negative class for negative score change', () => {
    const { container } = render(<ScorePanel performance={mockPerformance} scoreChange={-5} />)
    const changeElement = container.querySelector('.score-change.negative')
    expect(changeElement).toBeInTheDocument()
  })

  it('should display correct remaining points until next level', () => {
    render(<ScorePanel performance={mockPerformance} />)
    // Score is 55, next level is 100, so remaining is 45
    expect(screen.getByText(/45 until/)).toBeInTheDocument()
  })

  it('should handle score changes correctly when score updates', () => {
    const { rerender } = render(<ScorePanel performance={mockPerformance} />)
    
    // Initially no change indicator
    expect(screen.queryByText(/↑|↓/)).not.toBeInTheDocument()
    
    // After score change
    const updatedPerformance = { ...mockPerformance, trophy_score: 65 }
    rerender(<ScorePanel performance={updatedPerformance} scoreChange={10} />)
    
    expect(screen.getByText('↑')).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('65')).toBeInTheDocument()
  })

  it('should show absolute value of negative score change', () => {
    render(<ScorePanel performance={mockPerformance} scoreChange={-5} />)
    // Should show 5, not -5
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.queryByText('-5')).not.toBeInTheDocument()
  })
})

