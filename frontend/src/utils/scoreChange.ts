/**
 * Utility functions for score change calculations
 */

export function calculateScoreChange(
  previousScore: number,
  newScore: number
): number {
  return newScore - previousScore
}

export function shouldShowScoreChange(scoreChange: number | undefined): boolean {
  return scoreChange !== undefined && scoreChange !== 0
}

export function isPositiveChange(scoreChange: number | undefined): boolean {
  return scoreChange !== undefined && scoreChange > 0
}

