"""Structured prompts for LLM interactions."""
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate


# Question Generation Prompt
QUESTION_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert educator creating multiple-choice questions for a learning platform.
Generate a {difficulty} difficulty question about the following concept.

Course Context:
Topic: {topic}
Subtopic: {subtopic}
Concept: {concept_name}
Concept Description: {concept_description}
{content_context}

CRITICAL REQUIREMENTS FOR ANSWERS:
1. ALL answer options must be concrete, factual statements that can be objectively evaluated as true or false
2. NEVER use generic placeholders like "This is not the correct definition", "This is an unrelated concept", "None of the above", or similar opinion-based statements
3. Each incorrect answer should be a plausible alternative that demonstrates understanding of related concepts
4. All answers must be specific statements about the concept, related concepts, or common misconceptions
5. Answers should be educational - even wrong answers should teach something about the topic

Generate a multiple-choice question with {num_answers} answer options.
Each answer must be a complete, factual statement that can be objectively evaluated.

Return your response as a JSON object with this exact structure:
{{
    "question_text": "Your question here",
    "answers": [
        {{"text": "A specific factual statement about the concept", "is_correct": true, "explanation": "Why this is correct"}},
        {{"text": "A plausible alternative or related concept statement", "is_correct": false, "explanation": "Why this is incorrect"}},
        {{"text": "Another specific statement (could be a common misconception)", "is_correct": false, "explanation": "Why this is incorrect"}},
        ...
    ],
    "explanation": "Detailed explanation of the concept and why the correct answer is right"
}}

Make the question challenging and focused on understanding, not just memorization.
All answers must be concrete, factual statements - no generic placeholders allowed."""),
    ("human", "Generate the question.")
])


# Explanation Chat Prompt
EXPLANATION_CHAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful tutor assisting a student who just answered a question.

Question: {question_text}
Correct Answer: {correct_answer}
Student's Answer: {student_answer}
Was Correct: {was_correct}

Concept Context:
Topic: {topic}
Subtopic: {subtopic}
Concepts: {concepts}

Previous explanation given: {explanation}

Answer the student's follow-up question clearly and concisely. Use the concept context to provide accurate information.
Keep your response focused and educational."""),
    ("human", "{student_question}")
])


# Video Script Generation Prompt
VIDEO_SCRIPT_PROMPT = PromptTemplate.from_template("""You are creating a short educational video script (60-90 seconds when spoken).

Topic: {topic}
Subtopic: {subtopic}
Concept: {concept_name}
Description: {concept_description}

The student is struggling with this concept. Create an engaging, clear script that:
1. Introduces the concept in simple terms
2. Provides a concrete example or analogy
3. Explains why it matters
4. Ends with a key takeaway

Write the script in a conversational, engaging tone. Keep it concise and focused.
The script should be spoken aloud, so write naturally.

Return only the script text, no additional formatting or metadata.""")


# Adaptive Question Selection Prompt
TOPIC_SELECTION_PROMPT = PromptTemplate.from_template("""Based on the student's performance data, recommend which topic area to focus on next.

Performance Summary:
{performance_summary}

Available Topics and Concepts:
{available_topics}

Recommend the topic, subtopic, and concept that would be most beneficial for the student to practice.
Consider:
1. Areas with low accuracy (< 60%)
2. Concepts attempted but not mastered
3. Related concepts that build on weak areas
4. Balanced coverage of the course material

Return a JSON object:
{{
    "topic": "Recommended topic name",
    "subtopic": "Recommended subtopic name",
    "concept": "Recommended concept name",
    "reasoning": "Brief explanation of why this is recommended"
}}""")

