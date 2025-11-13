import { describe, it, expect } from 'vitest'
import {
  calculateScoreChange,
  shouldShowScoreChange,
  isPositiveChange,
} from '../scoreChange'

describe('Score Change Utilities', () => {
  describe('calculateScoreChange', () => {
    it('should calculate positive change correctly', () => {
      expect(calculateScoreChange(0, 10)).toBe(10)
      expect(calculateScoreChange(50, 60)).toBe(10)
    })

    it('should calculate negative change correctly', () => {
      expect(calculateScoreChange(10, 5)).toBe(-5)
      expect(calculateScoreChange(50, 45)).toBe(-5)
    })

    it('should return 0 when scores are equal', () => {
      expect(calculateScoreChange(10, 10)).toBe(0)
      expect(calculateScoreChange(0, 0)).toBe(0)
    })

    it('should handle edge cases', () => {
      expect(calculateScoreChange(0, 0)).toBe(0)
      expect(calculateScoreChange(100, 100)).toBe(0)
    })
  })

  describe('shouldShowScoreChange', () => {
    it('should return true for positive changes', () => {
      expect(shouldShowScoreChange(10)).toBe(true)
      expect(shouldShowScoreChange(5)).toBe(true)
    })

    it('should return true for negative changes', () => {
      expect(shouldShowScoreChange(-5)).toBe(true)
      expect(shouldShowScoreChange(-10)).toBe(true)
    })

    it('should return false for zero change', () => {
      expect(shouldShowScoreChange(0)).toBe(false)
    })

    it('should return false for undefined', () => {
      expect(shouldShowScoreChange(undefined)).toBe(false)
    })
  })

  describe('isPositiveChange', () => {
    it('should return true for positive changes', () => {
      expect(isPositiveChange(10)).toBe(true)
      expect(isPositiveChange(5)).toBe(true)
      expect(isPositiveChange(1)).toBe(true)
    })

    it('should return false for negative changes', () => {
      expect(isPositiveChange(-5)).toBe(false)
      expect(isPositiveChange(-10)).toBe(false)
    })

    it('should return false for zero change', () => {
      expect(isPositiveChange(0)).toBe(false)
    })

    it('should return false for undefined', () => {
      expect(isPositiveChange(undefined)).toBe(false)
    })
  })
})

