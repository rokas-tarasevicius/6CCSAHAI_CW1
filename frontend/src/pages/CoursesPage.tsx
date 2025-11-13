import { useState } from 'react'
import './CoursesPage.css'

export default function CoursesPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (file.type === 'application/pdf') {
        setSelectedFile(file)
      }
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      if (file.type === 'application/pdf') {
        setSelectedFile(file)
      }
    }
  }

  const handleRemove = () => {
    setSelectedFile(null)
  }

  return (
    <div className="courses-page">
      <div className="subject-header">
        <h1 className="subject-title">COURSES</h1>
      </div>

      <div className="courses-content">
        <div className="upload-section">
          <h2 className="section-title">Upload Course Material</h2>
          <p className="section-description">
            Upload a PDF file to create a new course. The system will extract content and generate questions automatically.
          </p>

          <div
            className={`upload-area ${dragActive ? 'drag-active' : ''} ${selectedFile ? 'has-file' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {selectedFile ? (
              <div className="file-preview">
                <div className="file-icon">📄</div>
                <div className="file-info">
                  <div className="file-name">{selectedFile.name}</div>
                  <div className="file-size">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                </div>
                <button className="remove-button" onClick={handleRemove}>
                  ✕
                </button>
              </div>
            ) : (
              <>
                <div className="upload-icon">📤</div>
                <div className="upload-text">
                  <p className="upload-title">Drag and drop your PDF here</p>
                  <p className="upload-subtitle">or</p>
                  <label htmlFor="file-upload" className="upload-button">
                    Browse Files
                  </label>
                  <input
                    id="file-upload"
                    type="file"
                    accept=".pdf"
                    onChange={handleChange}
                    className="file-input"
                  />
                </div>
                <p className="upload-hint">Supported format: PDF (max 10MB)</p>
              </>
            )}
          </div>

          {selectedFile && (
            <div className="upload-actions">
              <button className="btn-primary">
                Upload Course
              </button>
              <button className="btn-secondary" onClick={handleRemove}>
                Cancel
              </button>
            </div>
          )}
        </div>

        <div className="courses-list">
          <h2 className="section-title">Your Courses</h2>
          <div className="empty-state">
            <p>No courses yet. Upload a PDF to get started.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

