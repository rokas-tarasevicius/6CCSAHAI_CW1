import { useState, useEffect } from 'react'
import './CoursesPage.css'
import { courseApi } from '../services/api'
import type { ParsedDataResponse } from '../types'

export default function CoursesPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [parsedData, setParsedData] = useState<ParsedDataResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    loadCourse()
  }, [])

  const loadCourse = async () => {
    try {
      setLoading(true)
      setLoadError(null)
      const data = await courseApi.getCourse()
      setParsedData(data)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load parsed data'
      setLoadError(errorMessage)
      console.error('Error loading course data:', errorMessage)
    } finally {
      setLoading(false)
    }
  }

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
    setUploadError(null)
    setSuccess(null)
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploading(true)
    setUploadError(null)
    setSuccess(null)

    try {
      const result = await courseApi.uploadPdf(selectedFile)
      if (result.success) {
        setSuccess(result.message)
        setSelectedFile(null)
        // Reload the course data after successful upload
        await loadCourse()
      } else {
        setUploadError(result.message || 'Upload failed')
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to upload PDF'
      setUploadError(errorMessage)
      console.error('Error uploading PDF:', errorMessage)
    } finally {
      setUploading(false)
    }
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
              <button 
                className="btn-primary" 
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : 'Upload Course'}
              </button>
              <button 
                className="btn-secondary" 
                onClick={handleRemove}
                disabled={uploading}
              >
                Cancel
              </button>
            </div>
          )}

          {uploadError && (
            <div className="upload-message error">
              {uploadError}
            </div>
          )}

          {success && (
            <div className="upload-message success">
              {success}
            </div>
          )}
        </div>

        <div className="courses-list">
          <h2 className="section-title">Your Courses</h2>
          {loading ? (
            <div className="empty-state">
              <p>Loading parsed files...</p>
            </div>
          ) : loadError ? (
            <div className="empty-state">
              <p className="error-text">Error: {loadError}</p>
            </div>
          ) : parsedData && Object.keys(parsedData.files).length > 0 ? (
            <div className="parsed-files-list">
              {Object.entries(parsedData.files).map(([filePath, fileData]) => (
                <div key={filePath} className="parsed-file-card">
                  <div className="parsed-file-header">
                    <h3 className="parsed-file-title">{fileData.metadata.file_name}</h3>
                    <div className="parsed-file-meta">
                      <span className="meta-item">Type: {fileData.metadata.file_type.toUpperCase()}</span>
                      <span className="meta-item">Size: {(fileData.metadata.content_length / 1024).toFixed(2)} KB</span>
                      <span className="meta-item">Content Length: {fileData.metadata.content_length.toLocaleString()} chars</span>
                      <span className="meta-item">Language: {fileData.metadata.language}</span>
                      <span className="meta-item">Extracted: {new Date(fileData.metadata.extraction_timestamp).toLocaleString()} {fileData.metadata.timezone.toUpperCase()}</span>
                    </div>
                  </div>
                  <div className="parsed-file-content">
                    <p className="content-preview">
                      {fileData.content.substring(0, 500)}
                      {fileData.content.length > 500 ? '...' : ''}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
          <div className="empty-state">
              <p>No parsed files yet. Upload a PDF to get started.</p>
          </div>
          )}
        </div>
      </div>
    </div>
  )
}

