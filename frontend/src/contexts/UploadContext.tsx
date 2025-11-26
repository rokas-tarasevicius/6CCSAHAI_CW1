import React, { createContext, useContext, useState, useCallback } from 'react'

export interface UploadProgress {
  id: string
  fileName: string
  status: 'uploading' | 'processing' | 'success' | 'error'
  progress?: number
  error?: string
  startTime: number
}

export interface SuccessMessage {
  id: string
  message: string
  timestamp: number
  type: 'individual' | 'batch'
}

interface UploadContextType {
  uploads: UploadProgress[]
  successMessages: SuccessMessage[]
  startUpload: (id: string, fileName: string) => void
  updateUpload: (id: string, updates: Partial<UploadProgress>) => void
  finishUpload: (id: string, success: boolean, error?: string) => void
  removeUpload: (id: string) => void
  hasActiveUploads: () => boolean
  addSuccessMessage: (message: string, type: 'individual' | 'batch') => void
  clearSuccessMessages: () => void
  removeSuccessMessage: (id: string) => void
}

const UploadContext = createContext<UploadContextType | null>(null)

export const UploadProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [uploads, setUploads] = useState<UploadProgress[]>([])
  const [successMessages, setSuccessMessages] = useState<SuccessMessage[]>([])

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

  const addSuccessMessage = useCallback((message: string, type: 'individual' | 'batch') => {
    const id = `success-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const newMessage: SuccessMessage = {
      id,
      message,
      timestamp: Date.now(),
      type
    }
    
    setSuccessMessages(prev => [...prev, newMessage])
    
    // Auto-remove success messages after 10 seconds (longer than uploads for better UX)
    setTimeout(() => {
      setSuccessMessages(prev => prev.filter(m => m.id !== id))
    }, 10000)
  }, [])

  const clearSuccessMessages = useCallback(() => {
    setSuccessMessages([])
  }, [])

  const removeSuccessMessage = useCallback((id: string) => {
    setSuccessMessages(prev => prev.filter(m => m.id !== id))
  }, [])

  const value = {
    uploads,
    successMessages,
    startUpload,
    updateUpload,
    finishUpload,
    removeUpload,
    hasActiveUploads,
    addSuccessMessage,
    clearSuccessMessages,
    removeSuccessMessage
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
