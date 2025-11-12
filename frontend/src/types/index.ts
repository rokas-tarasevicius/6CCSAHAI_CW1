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

export interface Performance {
  total_questions_answered: number
  total_correct: number
  total_incorrect: number
  trophy_score: number
  overall_accuracy: number
  topic_scores: Record<string, TopicScore>
}

export interface TopicScore {
  overall_accuracy: number
  subtopic_scores: Record<string, SubtopicScore>
}

export interface SubtopicScore {
  overall_accuracy: number
  concept_scores: Record<string, ConceptScore>
}

export interface ConceptScore {
  attempts: number
  correct: number
  incorrect: number
  accuracy: number
  is_weak: boolean
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
  relevance_score: number
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


