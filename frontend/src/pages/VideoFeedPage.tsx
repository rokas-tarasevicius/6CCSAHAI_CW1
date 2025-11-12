import { useState, useEffect } from 'react'
import { usePerformanceStore } from '../store/usePerformanceStore'
import { videosApi } from '../services/api'
import type { VideoRecommendation, VideoContent } from '../types'
import './VideoFeedPage.css'

export default function VideoFeedPage() {
  const { performance } = usePerformanceStore()
  const [recommendations, setRecommendations] = useState<VideoRecommendation[]>([])
  const [generatedVideos, setGeneratedVideos] = useState<Record<string, VideoContent>>({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (performance.total_questions_answered > 0) {
      loadRecommendations()
    }
  }, [performance])

  const loadRecommendations = async () => {
    setLoading(true)
    try {
      const recs = await videosApi.getRecommendations(performance, 5)
      setRecommendations(recs)
    } catch (error) {
      console.error('Failed to load recommendations:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateVideo = async (rec: VideoRecommendation) => {
    const key = `${rec.topic}-${rec.subtopic}-${rec.concept}`
    if (generatedVideos[key]) return

    setLoading(true)
    try {
      const content = await videosApi.generateContent(
        rec.topic,
        rec.subtopic,
        rec.concept,
        rec.relevance_score
      )
      setGeneratedVideos((prev) => ({ ...prev, [key]: content }))
    } catch (error) {
      console.error('Failed to generate video:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="video-feed-page">
      <div className="subject-header">
        <h1 className="subject-title">HUMAN AI INTERACTION / PROTOTYPING</h1>
      </div>

      {performance.total_questions_answered === 0 ? (
        <div className="empty-state">
          <p>Start answering questions to get personalized video recommendations!</p>
        </div>
      ) : (
        <div className="video-content">
          {recommendations.map((rec, idx) => {
            const key = `${rec.topic}-${rec.subtopic}-${rec.concept}`
            const video = generatedVideos[key]

            return (
              <div key={idx} className="video-card">
                <h3>{rec.concept}</h3>
                <p className="video-meta">{rec.topic} → {rec.subtopic}</p>
                {video ? (
                  <div className="video-script">
                    <p>{video.script}</p>
                  </div>
                ) : (
                  <button
                    onClick={() => generateVideo(rec)}
                    className="btn-primary"
                    disabled={loading}
                  >
                    Generate Video Content
                  </button>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
