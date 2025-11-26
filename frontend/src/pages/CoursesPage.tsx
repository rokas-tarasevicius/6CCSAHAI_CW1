import { useState, useEffect } from 'react'
import './CoursesPage.css'
import { courseApi } from '../services/api'
import { useUpload } from '../contexts/UploadContext'
import type { ParsedDataResponse } from '../types'

export default function CoursesPage() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [dragActive, setDragActive] = useState(false)
  const [parsedData, setParsedData] = useState<ParsedDataResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [_, setRefreshing] = useState(false)
  const [refreshTimeout, setRefreshTimeout] = useState<number | null>(null)
  
  // Use global upload context for persistent upload tracking and success messages
  const { uploads, successMessages, startUpload, updateUpload, finishUpload, addSuccessMessage, clearSuccessMessages } = useUpload()

  useEffect(() => {
    loadCourse()
  }, [])

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (refreshTimeout) {
        clearTimeout(refreshTimeout)
      }
    }
  }, [refreshTimeout])

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

  // Refresh course data without showing loading spinner (preserves UI state)
  const refreshCourse = async (retryCount = 0, maxRetries = 3): Promise<boolean> => {
    try {
      setRefreshing(true)
      setLoadError(null)
      
      // Add a small delay before first attempt to ensure backend has processed the upload
      if (retryCount === 0) {
        await new Promise(resolve => setTimeout(resolve, 500))
      }
      
      const data = await courseApi.getCourse()
      
      // Check if we actually got new data (more files than before)
      const currentFileCount = parsedData ? Object.keys(parsedData.files).length : 0
      const newFileCount = Object.keys(data.files).length
      
      setParsedData(data)
      
      // If we didn't get new data and we haven't exhausted retries, try again
      if (newFileCount <= currentFileCount && retryCount < maxRetries) {
        console.log(`Refresh attempt ${retryCount + 1}: No new data found, retrying...`)
        await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1))) // Exponential backoff
        return await refreshCourse(retryCount + 1, maxRetries)
      }
      
      return true
    } catch (err: any) {
      console.error('Error refreshing course data:', err)
      
      // If we haven't exhausted retries, try again
      if (retryCount < maxRetries) {
        console.log(`Refresh attempt ${retryCount + 1} failed, retrying...`)
        await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)))
        return await refreshCourse(retryCount + 1, maxRetries)
      }
      
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to refresh course data'
      setLoadError(errorMessage)
      return false
    } finally {
      setRefreshing(false)
    }
  }

  // Debounced refresh function to prevent multiple simultaneous calls
  const debouncedRefreshCourse = (fileName: string) => {
    // Clear existing timeout
    if (refreshTimeout) {
      clearTimeout(refreshTimeout)
    }
    
    // Set new timeout
    const timeout = setTimeout(() => {
      console.log(`Debounced refresh triggered for ${fileName}`)
      refreshCourse().then(refreshSuccess => {
        if (refreshSuccess) {
          console.log(`Course data refreshed successfully for ${fileName}`)
        } else {
          console.warn(`Course data refresh failed for ${fileName}`)
        }
      }).catch(err => {
        console.error(`Error refreshing course data for ${fileName}:`, err)
      })
    }, 1000) // Wait 1 second before refreshing
    
    setRefreshTimeout(timeout)
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

    if (e.dataTransfer.files) {
      const files = Array.from(e.dataTransfer.files).filter(file => file.type === 'application/pdf')
      if (files.length > 0) {
        console.log(`Adding ${files.length} files via drag & drop:`, files.map(f => f.name))
        setSelectedFiles(prevFiles => [...prevFiles, ...files])
        // Clear messages when new files are added
        setUploadError(null)
        setSuccess(null)
        clearSuccessMessages()
      }
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files) {
      const files = Array.from(e.target.files).filter(file => file.type === 'application/pdf')
      if (files.length > 0) {
        console.log(`Adding ${files.length} files via file input:`, files.map(f => f.name))
        setSelectedFiles(prevFiles => [...prevFiles, ...files])
        // Clear messages when new files are added
        setUploadError(null)
        setSuccess(null)
        clearSuccessMessages()
      }
    }
    // Reset the input value so the same files can be selected again
    e.target.value = ''
  }

  const handleRemove = (fileToRemove?: File) => {
    if (fileToRemove) {
      setSelectedFiles(prevFiles => prevFiles.filter(file => file !== fileToRemove))
    } else {
      setSelectedFiles([])
    }
    setUploadError(null)
    setSuccess(null)
    clearSuccessMessages()
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return

    console.log(`Starting upload of ${selectedFiles.length} files:`, selectedFiles.map(f => f.name))

    // Clear the UI state immediately - files and messages, but NOT uploading state
    const filesToUpload = [...selectedFiles] // Copy the files before clearing
    setSelectedFiles([])
    setUploadError(null)
    setSuccess(null)
    clearSuccessMessages()
    // Remove setUploading(true) to allow consecutive uploads
    
    // Process files individually so we can refresh after each successful upload
    const uploadPromises = filesToUpload.map(async (file) => {
      const uploadId = `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      
      // Start global upload tracking
      startUpload(uploadId, file.name)

      try {
        // Update status to processing
        updateUpload(uploadId, { status: 'processing' })
        
        const result = await courseApi.uploadPdf(file)
        
        if (result.success) {
          // Mark upload as successful
          finishUpload(uploadId, true)
          
          // Add to persistent success messages immediately
          addSuccessMessage(`✓ ${file.name} uploaded successfully`, 'individual')
          
          // Immediately refresh course data for this successful upload
          console.log(`File ${file.name} uploaded successfully, triggering refresh...`)
          debouncedRefreshCourse(file.name)
          
          return { success: true, fileName: file.name, message: result.message }
        } else {
          finishUpload(uploadId, false, result.message || 'Upload failed')
          return { success: false, fileName: file.name, message: result.message || 'Upload failed' }
        }
      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || err.message || 'Failed to upload PDF'
        finishUpload(uploadId, false, errorMessage)
        return { success: false, fileName: file.name, message: errorMessage }
      }
    })

    try {
      const results = await Promise.all(uploadPromises)
      
      // Check results for final summary
      const successfulUploads = results.filter(r => r.success)
      const failedUploads = results.filter(r => !r.success)
      
      // Set batch completion message if multiple files were uploaded
      if (filesToUpload.length > 1) {
        if (successfulUploads.length > 0 && failedUploads.length === 0) {
          addSuccessMessage(`✓ All ${successfulUploads.length} files uploaded successfully!`, 'batch')
        } else if (successfulUploads.length > 0 && failedUploads.length > 0) {
          addSuccessMessage(`✓ ${successfulUploads.length} of ${filesToUpload.length} files uploaded successfully`, 'batch')
        }
      } else if (successfulUploads.length === 1) {
        // For single file, the individual success message is already added above
        // No need to add anything extra
      }
      
      if (failedUploads.length > 0) {
        const errorMessages = failedUploads.map(r => `• ${r.fileName}: ${r.message}`).join('\n')
        setUploadError(`Failed uploads:\n${errorMessages}`)
      }
    } catch (err: any) {
      console.error('Error during bulk upload:', err)
      setUploadError('An unexpected error occurred during upload')
    }
    // Remove finally block that sets uploading to false
    // This allows consecutive uploads without waiting for the previous batch to complete
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
            Upload one or more PDF files to create courses. The system will extract content and generate questions automatically.
          </p>

          <div
            className={`upload-area ${dragActive ? 'drag-active' : ''} ${selectedFiles.length > 0 ? 'has-file' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {selectedFiles.length > 0 ? (
              <div className="files-preview">
                <h3 className="files-title">Selected Files ({selectedFiles.length})</h3>
                <div className="files-list">
                  {selectedFiles.map((file, index) => (
                    <div key={index} className="file-preview">
                      <div className="file-icon">📄</div>
                      <div className="file-info">
                        <div className="file-name">{file.name}</div>
                        <div className="file-size">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </div>
                      </div>
                      <button 
                        className="remove-button" 
                        onClick={(e) => {
                          e.preventDefault()
                          handleRemove(file)
                        }}
                        title={`Remove ${file.name}`}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
                <div className="upload-actions-inline">
                  <label htmlFor="file-upload" className="upload-button">
                    Add More Files
                  </label>
                  <button 
                    className="btn-secondary" 
                    onClick={(e) => {
                      e.preventDefault()
                      handleRemove()
                    }}
                  >
                    Clear All
                  </button>
                </div>
                <input
                  id="file-upload"
                  type="file"
                  accept=".pdf"
                  multiple
                  onChange={handleChange}
                  className="file-input"
                />
              </div>
            ) : (
              <>
                <div className="upload-icon">📤</div>
                <div className="upload-text">
                  <p className="upload-title">Drag and drop your PDFs here</p>
                  <p className="upload-subtitle">or</p>
                  <label htmlFor="file-upload" className="upload-button">
                    Browse Files
                  </label>
                  <input
                    id="file-upload"
                    type="file"
                    accept=".pdf"
                    multiple
                    onChange={handleChange}
                    className="file-input"
                  />
                </div>
                <p className="upload-hint">Supported format: PDF (max 10MB each) • Select multiple files</p>
              </>
            )}
          </div>

          {selectedFiles.length > 0 && (
            <div className="upload-actions">
              <button 
                className="btn-primary" 
                onClick={handleUpload}
                disabled={selectedFiles.length === 0}
              >
                {`Upload ${selectedFiles.length} Course${selectedFiles.length === 1 ? '' : 's'}`}
              </button>
              <button 
                className="btn-secondary" 
                onClick={(e) => {
                  e.preventDefault()
                  handleRemove()
                }}
              >
                Cancel
              </button>
            </div>
          )}

          {uploadError && (
            <div className="upload-message error">
              {uploadError.split('\n').map((line, index) => (
                <div key={index}>{line}</div>
              ))}
            </div>
          )}

          {/* Success messages from context - persistent across page navigation */}
          {successMessages.length > 0 && (
            <div className="upload-message success">
              {successMessages.map((messageObj) => (
                <div 
                  key={messageObj.id} 
                  className={`success-message-item ${messageObj.type}`}
                >
                  {messageObj.message}
                </div>
              ))}
            </div>
          )}

          {/* Single file success message (local state, for immediate feedback) */}
          {success && (
            <div className="upload-message success">
              {success}
            </div>
          )}
        </div>

        <div className="courses-list">
          <div className="courses-header">
            <h2 className="section-title">Your Courses</h2>
          </div>
          
          {/* Active Upload Progress - show at top of courses list */}
          {uploads.filter(u => u.status === 'uploading' || u.status === 'processing').map(upload => (
            <div key={upload.id} className="upload-progress-card">
              <div className="upload-progress-header">
                <div className="upload-file-info">
                  <span className="upload-file-name">{upload.fileName}</span>
                  <span className={`upload-status ${upload.status}`}>
                    {upload.status === 'uploading' && '📤 Uploading...'}
                    {upload.status === 'processing' && '⚡ Processing...'}
                  </span>
                </div>
              </div>
              
              <div className="upload-progress-bar">
                <div className="upload-progress-fill"></div>
              </div>
            </div>
          ))}
          
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
                      <span className="meta-item">Language: {fileData.metadata.language.toUpperCase()}</span>
                      <span className="meta-item">Content Length: {fileData.metadata.content_length.toLocaleString()} chars</span>
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

