import { useState, useEffect, useRef } from 'react'
import { videosApi } from '../services/api'
import type { VideoRecommendation, VideoContent } from '../types'
import './VideoFeedPage.css'

export default function VideoFeedPage() {
  const [recommendations, setRecommendations] = useState<VideoRecommendation[]>([])
  const [generatedVideos, setGeneratedVideos] = useState<Record<string, VideoContent>>({})
  const [loading, setLoading] = useState(false)
  const [generatingVideos, setGeneratingVideos] = useState<Set<string>>(new Set())
  const processedRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    loadRecommendations()
  }, [])

  useEffect(() => {
    // Automatically generate videos for all recommendations when they're loaded
    if (recommendations.length > 0) {
      recommendations.forEach((rec) => {
        const key = `${rec.topic}-${rec.subtopic}-${rec.concept}`
        if (!processedRef.current.has(key)) {
          processedRef.current.add(key)
          generateVideo(rec)
        }
      })
    }
  }, [recommendations])

  const loadRecommendations = async () => {
    setLoading(true)
    try {
      const recs = await videosApi.getRecommendations(5)
      setRecommendations(recs)
    } catch (error) {
      console.error('Failed to load recommendations:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateVideo = async (rec: VideoRecommendation) => {
    const key = `${rec.topic}-${rec.subtopic}-${rec.concept}`
    if (generatedVideos[key] || generatingVideos.has(key)) return

    setGeneratingVideos((prev) => new Set(prev).add(key))
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
      setGeneratingVideos((prev) => {
        const next = new Set(prev)
        next.delete(key)
        return next
      })
    }
  }

  const hasGeneratingVideos = generatingVideos.size > 0
  const generatedVideoKeys = Object.keys(generatedVideos)

  return (
    <div className="video-feed-page">
      {loading ? (
        <div className="empty-state">
          <p>Loading video recommendations...</p>
        </div>
      ) : recommendations.length === 0 ? (
        <div className="empty-state">
          <p>No course material available. Please upload PDF files first.</p>
        </div>
      ) : (
        <div className="video-content">
          {/* Show all generated videos */}
          {generatedVideoKeys.map((key) => {
            const video = generatedVideos[key]
            if (!video) return null

            return (
              <div key={key} className="video-card">
                <h3>{video.concept}</h3>
                <p className="video-meta">{video.topic} → {video.subtopic}</p>
                <div className="video-content-display">
                  {video.video_url ? (
                    <div className="video-player-container">
                      <video
                        controls
                        className="video-player"
                        src={video.video_url}
                        style={{ width: '100%', maxWidth: '800px', borderRadius: '8px' }}
                      >
                        Your browser does not support the video tag.
                      </video>
                    </div>
                  ) : null}
                  <div className="video-script">
                    <h4>Script:</h4>
                    <p>{video.script}</p>
                    {video.duration_seconds && (
                      <p className="video-duration">
                        Duration: {Math.round(video.duration_seconds)}s
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )
          })}

          {/* Show single in-progress card if any videos are still generating */}
          {hasGeneratingVideos && (
            <div className="video-card">
              <div className="video-generating">
                Generating video content...
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
