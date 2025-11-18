import axios from 'axios'
import type { Question, Performance, VideoRecommendation, VideoContent, Course, ParsedDataResponse } from '../types'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const courseApi = {
  getCourse: async (): Promise<ParsedDataResponse> => {
    const response = await api.get<ParsedDataResponse>('/course/')
    return response.data
  },
}

export const questionsApi = {
  generateQuestion: async (performanceData?: Partial<Performance>): Promise<Question> => {
    const response = await api.post<Question>('/questions/generate', {
      performance_data: performanceData || null
    })
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

export const performanceApi = {
  recordAnswer: async (
    performanceData: Partial<Performance>,
    topic: string,
    subtopic: string,
    concept: string,
    isCorrect: boolean
  ): Promise<Performance> => {
    const response = await api.post<Performance>('/performance/record-answer', {
      performance_data: performanceData,
      topic,
      subtopic,
      concept,
      is_correct: isCorrect,
    })
    return response.data
  },
  
  getWeakAreas: async (
    performanceData: Partial<Performance>,
    minAttempts: number = 2
  ) => {
    const response = await api.post('/performance/weak-areas', {
      performance_data: performanceData,
      min_attempts: minAttempts,
    })
    return response.data
  },
  
  getSummary: async (performanceData: Partial<Performance>) => {
    const response = await api.post('/performance/summary', {
      performance_data: performanceData,
    })
    return response.data
  },
}

export const videosApi = {
  getRecommendations: async (
    performanceData: Partial<Performance>,
    maxVideos: number = 5
  ): Promise<VideoRecommendation[]> => {
    const response = await api.post<{ recommendations: VideoRecommendation[] }>(
      '/videos/recommendations',
      {
        performance_data: performanceData,
        max_videos: maxVideos,
      }
    )
    return response.data.recommendations
  },
  
  generateContent: async (
    topic: string,
    subtopic: string,
    concept: string,
    relevanceScore: number = 1.0
  ): Promise<VideoContent> => {
    const response = await api.post<VideoContent>('/videos/generate', {
      topic,
      subtopic,
      concept,
      relevance_score: relevanceScore,
    })
    return response.data
  },
}


