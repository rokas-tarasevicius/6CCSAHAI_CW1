import { useEffect, useState } from 'react'
import { useRating } from '../contexts/RatingContext'
import { userProfileApi, type IncorrectConceptRef } from '../services/api'
import './ProfilePage.css'

export default function ProfilePage() {
  const { rating } = useRating()
  const [incorrectConcepts, setIncorrectConcepts] = useState<IncorrectConceptRef[]>([])

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const profile = await userProfileApi.getProfile()
        setIncorrectConcepts(profile.incorrect_concepts || [])
      } catch (err) {
        // ignore fetch errors, show empty list
      }
    }
    loadProfile()
  }, [])

  return (
    <div className="profile-page">
      <div className="profile-container">
        <h1 className="profile-title">Profile</h1>
        <div className="rating-section">
          <div className="rating-label">Rating</div>
          <div className="rating-value">{Math.round(rating)}</div>
        </div>
        <div className="incorrect-section">
          <h2>Recent incorrect concepts</h2>
          {incorrectConcepts.length === 0 ? (
            <p className="empty-state">No missed concepts recorded yet.</p>
          ) : (
            <ul className="incorrect-list">
              {incorrectConcepts.map((c) => (
                <li key={`${c.topic}-${c.subtopic}-${c.concept}`}>
                  <strong>{c.concept}</strong> — {c.topic} / {c.subtopic}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}

