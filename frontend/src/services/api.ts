import axios from 'axios'
import type { Question, VideoContent, ParsedDataResponse } from '../types'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes timeout for file uploads
})

export const courseApi = {
  getCourse: async (): Promise<ParsedDataResponse> => {
    const response = await api.get<ParsedDataResponse>('/course/')
    return response.data
  },
  
  uploadPdf: async (file: File): Promise<{ success: boolean; message: string; data?: any }> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/course/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000, // 5 minutes for large file uploads
    })
    return response.data
  },
  
  generateQuiz: async (fileKey: string, numQuestions: number = 5): Promise<{ success: boolean; message: string; data?: any }> => {
    const response = await api.post(`/course/generate-quiz/${encodeURIComponent(fileKey)}?num_questions=${numQuestions}`)
    return response.data
  },
  
  deleteCourse: async (fileKey: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete(`/course/${encodeURIComponent(fileKey)}`)
    return response.data
  },
}

export const questionsApi = {
  startFileBasedQuiz: async (selectedFilePaths: string[], maxQuestions?: number): Promise<Question[]> => {
    const requestBody: any = {
      file_paths: selectedFilePaths
    }
    
    // Include max_questions only if specified
    if (maxQuestions && maxQuestions > 0) {
      requestBody.max_questions = maxQuestions
    }
    
    const response = await api.post<Question[]>('/questions/start-file-quiz', requestBody)
    return response.data
  },
  
  submitAnswer: async (
    selectedIndex: number,
    topic: string,
    subtopic: string,
    concept: string
  ) => {
    const response = await api.post('/questions/submit-answer', {
      selected_answer_index: selectedIndex,
      topic,
      subtopic,
      concept,
    })
    return response.data
  },
  
  getExplanation: async (
    questionText: string,
    correctAnswer: string,
    studentAnswer: string,
    wasCorrect: boolean,
    topic: string,
    subtopic: string,
    concepts: string[],
    explanation: string,
    studentQuestion: string
  ): Promise<string> => {
    const response = await api.post<{ response: string }>('/questions/explain', {
      question_text: questionText,
      correct_answer: correctAnswer,
      student_answer: studentAnswer,
      was_correct: wasCorrect,
      topic,
      subtopic,
      concepts,
      explanation,
      student_question: studentQuestion,
    })
    return response.data.response
  },
}

export const videosApi = {
  generateVideo: async (
    topic: string,
    subtopic: string,
    concept: {
      name: string
      description: string
      keywords: string[]
    }
  ): Promise<VideoContent> => {
    const response = await api.post<VideoContent>('/videos/generate', {
      topic,
      subtopic,
      concept,
    })
    return response.data
  },
  
  generateRandomVideo: async (): Promise<VideoContent> => {
    const response = await api.post<VideoContent>('/videos/generate-random')
    return response.data
  },
  
  getCachedVideos: async (): Promise<VideoContent[]> => {
    const response = await api.get<VideoContent[]>('/videos/cached')
    return response.data
  },
}

export interface IncorrectConceptRef {
  topic: string
  subtopic: string
  concept: string
}

export interface UserProfile {
  rating: number
  incorrect_concepts: IncorrectConceptRef[]
}

export const userProfileApi = {
  getProfile: async (): Promise<UserProfile> => {
    const response = await api.get<UserProfile>('/user/profile')
    return response.data
  },
  
  updateRating: async (rating: number): Promise<UserProfile> => {
    const response = await api.patch<UserProfile>('/user/profile/rating', { rating })
    return response.data
  },
}

export const quizProgressApi = {
  completeQuiz: async (incorrectConcepts: IncorrectConceptRef[]): Promise<UserProfile> => {
    const response = await api.post<UserProfile>('/questions/complete', {
      incorrect_concepts: incorrectConcepts,
    })
    return response.data
  },
}

export interface ChatbotRequest {
  question: string
  quiz_question?: string
  correct_answer?: string
  topic: string
  subtopic?: string
  concepts?: string[]
}

export interface ChatbotResponse {
  answer: string
}

export const chatbotApi = {
  ask: async (request: ChatbotRequest): Promise<ChatbotResponse> => {
    const response = await api.post<ChatbotResponse>('/chatbot/ask', request)
    return response.data
  },
}


