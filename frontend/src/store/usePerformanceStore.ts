import { create } from 'zustand'
import type { Performance } from '../types'

interface PerformanceState {
  performance: Performance
  setPerformance: (performance: Performance) => void
  updatePerformance: (updates: Partial<Performance>) => void
  resetPerformance: () => void
}

const initialPerformance: Performance = {
  total_questions_answered: 0,
  total_correct: 0,
  total_incorrect: 0,
  trophy_score: 0,
  overall_accuracy: 0,
  topic_scores: {},
}

export const usePerformanceStore = create<PerformanceState>((set) => ({
  performance: initialPerformance,
  setPerformance: (performance) => set({ performance }),
  updatePerformance: (updates) =>
    set((state) => ({
      performance: { ...state.performance, ...updates },
    })),
  resetPerformance: () => set({ performance: initialPerformance }),
}))


