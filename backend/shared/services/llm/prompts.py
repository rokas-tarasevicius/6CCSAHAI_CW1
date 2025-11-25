"""Structured prompts for LLM interactions."""
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate


# Question Generation Prompt (optimized for speed)
QUESTION_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "{system_instruction}"),
    ("human", 
    """
    {{
    "topic": "{topic}",
    "subtopic": "{subtopic}",
    "concept_name": "{concept_name}",
    "concept_description": "{concept_description}",
    "content_context": "{content_context}",
    "difficulty": "{difficulty}"
    }}
    """
    )
])

CHOICE_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "{system_instruction}"),
    ("human", 
    """
    {{
    "question": "{question}",
    "topic": "{topic}",
    "subtopic": "{subtopic}",
    "concept_name": "{concept_name}",
    "concept_description": "{concept_description}",
    "content_context": "{content_context}",
    "difficulty": "{difficulty}"
    }}
    """
    )
])


# QUESTION_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
#     ("system", """Create a {difficulty} multiple-choice question.
# Topic: {topic} | Subtopic: {subtopic} | Concept: {concept_name}
# Description: {concept_description}
# {content_context}

# Rules:
# - {num_answers} answer options
# - All answers must be concrete, factual statements
# - No generic placeholders like "This is incorrect" or "None of the above"
# - Each wrong answer should be a plausible alternative

# Return JSON only:
 

#     ("human", "Generate question.")
# ])


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

