import { useUpload } from '../contexts/UploadContext'
import './UploadIndicator.css'

export default function UploadIndicator() {
  const { uploads, removeUpload } = useUpload()

  // Only show if there are active uploads
  if (uploads.length === 0) return null

  return (
    <div className="upload-indicator">
      <div className="upload-indicator-header">
        <span className="upload-indicator-title">
          {uploads.some(u => u.status === 'uploading' || u.status === 'processing') ? 'Processing...' : 'Uploads'}
        </span>
        {uploads.length === 1 && uploads[0].status === 'success' && (
          <button 
            className="close-indicator" 
            onClick={() => removeUpload(uploads[0].id)}
          >
            ✕
          </button>
        )}
      </div>
      <div className="upload-list">
        {uploads.map(upload => (
          <div key={upload.id} className={`upload-item ${upload.status}`}>
            <div className="upload-item-content">
              <div className="upload-file-info">
                <span className="upload-file-name">{upload.fileName}</span>
                <span className="upload-status-text">
                  {upload.status === 'uploading' && 'Uploading...'}
                  {upload.status === 'processing' && 'Processing...'}
                  {upload.status === 'success' && '✓ Complete'}
                  {upload.status === 'error' && '✗ Failed'}
                </span>
              </div>
              
              {(upload.status === 'uploading' || upload.status === 'processing') && (
                <div className="upload-progress">
                  <div className="upload-progress-bar">
                    <div className="upload-progress-fill"></div>
                  </div>
                </div>
              )}
              
              {upload.status === 'error' && upload.error && (
                <div className="upload-error">
                  <span className="error-text">{upload.error}</span>
                  <button 
                    className="remove-error" 
                    onClick={() => removeUpload(upload.id)}
                  >
                    Dismiss
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}