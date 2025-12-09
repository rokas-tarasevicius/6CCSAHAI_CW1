import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { userProfileApi } from '../services/api'

interface RatingContextType {
  rating: number
  updateRating: (delta: number) => Promise<void>
  refreshRating: () => Promise<void>
}

const RatingContext = createContext<RatingContextType | undefined>(undefined)

export function RatingProvider({ children }: { children: ReactNode }) {
  const [rating, setRating] = useState<number>(1000)

  const loadRating = async () => {
    try {
      const profile = await userProfileApi.getProfile()
      setRating(profile.rating)
    } catch (err) {
      // Silently fail - use default rating
    }
  }

  useEffect(() => {
    loadRating()
  }, [])

  const updateRating = async (delta: number) => {
    try {
      const currentRating = rating
      const newRating = Math.max(0, currentRating + delta)
      await userProfileApi.updateRating(newRating)
      setRating(newRating)
    } catch (err) {
      console.error('Failed to update rating:', err)
    }
  }

  const refreshRating = async () => {
    await loadRating()
  }

  return (
    <RatingContext.Provider value={{ rating, updateRating, refreshRating }}>
      {children}
    </RatingContext.Provider>
  )
}

export function useRating() {
  const context = useContext(RatingContext)
  if (context === undefined) {
    throw new Error('useRating must be used within a RatingProvider')
  }
  return context
}



