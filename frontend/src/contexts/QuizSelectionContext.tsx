import React, { createContext, useContext, useState, useCallback } from 'react'

export interface SelectedQuizFile {
  filePath: string
  fileName: string
  questionCount: number
}

interface QuizSelectionContextType {
  selectedQuizFiles: SelectedQuizFile[]
  totalQuestions: number
  addQuizFile: (filePath: string, fileName: string, questionCount: number) => void
  removeQuizFile: (filePath: string) => void
  clearQuizSelection: () => void
  selectAllQuizFiles: (files: Array<{ filePath: string; fileName: string; questionCount: number }>) => void
  deselectAllQuizFiles: () => void
  isQuizSelected: (filePath: string) => boolean
  getSelectedFilePaths: () => string[]
}

const QuizSelectionContext = createContext<QuizSelectionContextType | null>(null)

export const QuizSelectionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedQuizFiles, setSelectedQuizFiles] = useState<SelectedQuizFile[]>([])

  const addQuizFile = useCallback((filePath: string, fileName: string, questionCount: number) => {
    setSelectedQuizFiles(prev => {
      // Check if already selected
      if (prev.some(file => file.filePath === filePath)) {
        return prev
      }
      return [...prev, { filePath, fileName, questionCount }]
    })
  }, [])

  const removeQuizFile = useCallback((filePath: string) => {
    setSelectedQuizFiles(prev => prev.filter(file => file.filePath !== filePath))
  }, [])

  const clearQuizSelection = useCallback(() => {
    setSelectedQuizFiles([])
  }, [])

  const selectAllQuizFiles = useCallback((files: Array<{ filePath: string; fileName: string; questionCount: number }>) => {
    setSelectedQuizFiles(files)
  }, [])

  const deselectAllQuizFiles = useCallback(() => {
    setSelectedQuizFiles([])
  }, [])

  const isQuizSelected = useCallback((filePath: string) => {
    return selectedQuizFiles.some(file => file.filePath === filePath)
  }, [selectedQuizFiles])

  const getSelectedFilePaths = useCallback(() => {
    return selectedQuizFiles.map(file => file.filePath)
  }, [selectedQuizFiles])

  const totalQuestions = selectedQuizFiles.reduce((sum, file) => sum + file.questionCount, 0)

  const value = {
    selectedQuizFiles,
    totalQuestions,
    addQuizFile,
    removeQuizFile,
    clearQuizSelection,
    selectAllQuizFiles,
    deselectAllQuizFiles,
    isQuizSelected,
    getSelectedFilePaths
  }

  return (
    <QuizSelectionContext.Provider value={value}>
      {children}
    </QuizSelectionContext.Provider>
  )
}

export const useQuizSelection = () => {
  const context = useContext(QuizSelectionContext)
  if (!context) {
    throw new Error('useQuizSelection must be used within a QuizSelectionProvider')
  }
  return context
}
