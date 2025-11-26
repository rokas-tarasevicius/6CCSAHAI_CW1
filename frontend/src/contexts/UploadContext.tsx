import React, { createContext, useContext, useState, useCallback } from 'react'

export interface UploadProgress {
  id: string
  fileName: string
  status: 'uploading' | 'processing' | 'success' | 'error'
  progress?: number
  error?: string
  startTime: number
}

interface UploadContextType {
  uploads: UploadProgress[]
  startUpload: (id: string, fileName: string) => void
  updateUpload: (id: string, updates: Partial<UploadProgress>) => void
  finishUpload: (id: string, success: boolean, error?: string) => void
  removeUpload: (id: string) => void
  hasActiveUploads: () => boolean
}

const UploadContext = createContext<UploadContextType | null>(null)

export const UploadProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [uploads, setUploads] = useState<UploadProgress[]>([])

  const startUpload = useCallback((id: string, fileName: string) => {
    setUploads(prev => [
      ...prev.filter(u => u.id !== id), // Remove existing upload with same ID
      {
        id,
        fileName,
        status: 'uploading' as const,
        startTime: Date.now()
      }
    ])
  }, [])

  const updateUpload = useCallback((id: string, updates: Partial<UploadProgress>) => {
    setUploads(prev => 
      prev.map(upload => 
        upload.id === id ? { ...upload, ...updates } : upload
      )
    )
  }, [])

  const finishUpload = useCallback((id: string, success: boolean, error?: string) => {
    setUploads(prev => 
      prev.map(upload => 
        upload.id === id 
          ? { 
              ...upload, 
              status: success ? 'success' as const : 'error' as const,
              error: error || undefined
            }
          : upload
      )
    )

    // Auto-remove successful uploads after 3 seconds
    if (success) {
      setTimeout(() => {
        setUploads(prev => prev.filter(u => u.id !== id))
      }, 3000)
    }
  }, [])

  const removeUpload = useCallback((id: string) => {
    setUploads(prev => prev.filter(u => u.id !== id))
  }, [])

  const hasActiveUploads = useCallback(() => {
    return uploads.some(u => u.status === 'uploading' || u.status === 'processing')
  }, [uploads])

  const value = {
    uploads,
    startUpload,
    updateUpload,
    finishUpload,
    removeUpload,
    hasActiveUploads
  }

  return (
    <UploadContext.Provider value={value}>
      {children}
    </UploadContext.Provider>
  )
}

export const useUpload = () => {
  const context = useContext(UploadContext)
  if (!context) {
    throw new Error('useUpload must be used within an UploadProvider')
  }
  return context
}
