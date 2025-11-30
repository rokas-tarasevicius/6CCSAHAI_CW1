import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { videosApi, courseApi } from '../services/api'
import type { VideoContent } from '../types'
import './VideoFeedPage.css'

export default function VideoFeedPage() {
  const [hasContent, setHasContent] = useState<boolean | null>(null)
  const [generatedVideos, setGeneratedVideos] = useState<Record<string, VideoContent>>({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    checkContent()
    loadCachedVideos()
  }, [])

  const loadCachedVideos = async () => {
    try {
      const cachedVideos = await videosApi.getCachedVideos()
      const videosMap: Record<string, VideoContent> = {}
      cachedVideos.forEach((video, index) => {
        // Use cache_key if available, otherwise use topic-subtopic-concept
        // For old cached videos without topic/subtopic/concept, use cache_key or index
        const key = (video as any).cache_key || 
                    (video.topic && video.subtopic && video.concept ? `${video.topic}-${video.subtopic}-${video.concept}` : null) ||
                    `cached-${index}-${(video as any).cache_key || Date.now()}`
        videosMap[key] = video
      })
      setGeneratedVideos(videosMap)
      console.log(`Loaded ${cachedVideos.length} cached videos`)
    } catch (error) {
      console.error('Failed to load cached videos:', error)
    }
  }

  const checkContent = async () => {
    try {
      const data = await courseApi.getCourse()
      const hasFiles = data.files && Object.keys(data.files).length > 0
      setHasContent(hasFiles)
    } catch (err) {
      setHasContent(false)
    }
  }

  const generateRandomVideo = async () => {
    if (loading) return

    setLoading(true)
    try {
      const content = await videosApi.generateRandomVideo()
      const key = `${content.topic}-${content.subtopic}-${content.concept}`
      // Add new video at the top of the feed
      setGeneratedVideos((prev) => {
        const { [key]: _, ...rest } = prev
        return { [key]: content, ...rest }
      })
    } catch (error) {
      console.error('Failed to generate random video:', error)
    } finally {
      setLoading(false)
    }
  }

  const generatedVideoKeys = Object.keys(generatedVideos)

  return (
    <div className="video-feed-page">
      {hasContent === false ? (
        <div className="empty-state">
          <h2>No Course Material Found</h2>
          <p>You need to upload course materials before we can generate videos.</p>
          <p>Please upload PDF files to get started with personalized video content.</p>
          <Link to="/courses" className="btn-primary">
            Upload Course Material
          </Link>
        </div>
      ) : (
        <div className="video-content">
          <div className="video-feed-header">
            <h2>Video Feed</h2>
            <button 
              className="btn-primary generate-btn"
              onClick={generateRandomVideo}
              disabled={loading}
            >
              {loading ? 'Generating...' : 'Generate Random Video'}
            </button>
          </div>
          
          {generatedVideoKeys.length === 0 && !loading && (
            <div className="empty-state">
              <p>No videos generated yet. Click the button above to generate a random video.</p>
            </div>
          )}
          
          {/* Show all generated videos */}
          {generatedVideoKeys.map((key) => {
            const video = generatedVideos[key]
            if (!video) return null

            return (
              <div key={key} className="video-card">
                <h3>{video.concept}</h3>
                <div className="video-content-display">
                  {video.video_path ? (
                    <div className="video-player-container">
                      <video
                        controls
                        className="video-player"
                        src={`/api/videos/file/${video.video_path.includes('/') ? video.video_path.split('/').pop() : video.video_path}`}
                        style={{ width: '100%', maxWidth: '800px', borderRadius: '8px' }}
                      >
                        Your browser does not support the video tag.
                      </video>
                    </div>
                  ) : null}
                </div>
              </div>
            )
          })}

          {loading && (
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
