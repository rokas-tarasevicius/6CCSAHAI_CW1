export interface AnswerOption {
  text: string
  is_correct: boolean
  explanation?: string
}

export interface Question {
  question_text: string
  answers: AnswerOption[]
  topic: string
  subtopic: string
  concepts: string[]
  difficulty: string
  explanation: string
}

export interface QuizQuestion {
  id: string
  question_text: string
  answers: AnswerOption[]
  topic: string
  subtopic: string
  concepts: string[]
  difficulty: string
  explanation: string
  created_at?: string
}



export interface VideoRecommendation {
  topic: string
  subtopic: string
  concept: string
  relevance_score: number
}

export interface VideoContent {
  topic: string
  subtopic: string
  concept: string
  script: string
  duration_seconds: number
  audio_path: string
  video_path: string
}

export interface Course {
  title: string
  description: string
  topics: Topic[]
}

export interface Topic {
  name: string
  description: string
  subtopics: Subtopic[]
}

export interface Subtopic {
  name: string
  description: string
  concepts: Concept[]
  content?: string
}

export interface Concept {
  name: string
  description: string
  keywords: string[]
}

export interface ParsedFileMetadata {
  file_name: string
  file_type: string
  content_length: number
  language: string
  extraction_timestamp: string
  timezone: string
}

export interface ParsedFileData {
  metadata: ParsedFileMetadata
  content: string
  summary?: string  // AI-generated summary of the file
  quiz?: QuizQuestion[]  // Quiz questions for this file
}

export interface ParsedDataResponse {
  files: Record<string, ParsedFileData>
}


