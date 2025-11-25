"""Structured prompts for LLM interactions."""
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate


# Question Generation Prompt (optimized for speed)
QUESTION_GENERATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Create a {difficulty} multiple-choice question.

Topic: {topic} | Subtopic: {subtopic} | Concept: {concept_name}
Description: {concept_description}
{content_context}

Rules:
- {num_answers} answer options
- All answers must be concrete, factual statements
- No generic placeholders like "This is incorrect" or "None of the above"
- Each wrong answer should be a plausible alternative

Return JSON only:
{{
    "question_text": "Question text",
    "answers": [
        {{"text": "Factual statement", "is_correct": true, "explanation": "Brief explanation"}},
        {{"text": "Plausible alternative", "is_correct": false, "explanation": "Why wrong"}}
    ],
    "explanation": "Concise explanation"
}}"""),
    ("human", "Generate question.")
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


# Video Script Generation Prompt (Short-form Reel)
VIDEO_SCRIPT_PROMPT = PromptTemplate.from_template("""You are an expert educational content creator specializing in technical short-form video scripts. Create a clear, engaging script that helps a struggling student understand a specific technical concept with proper depth and accuracy.

CONTEXT:
Topic: {topic}
Subtopic: {subtopic}
Concept: {concept_name}
Concept Details: {concept_description}

IMPORTANT: The concept description above includes relevant content from the parsed course material (PDFs). Use this parsed content to inform your technical explanation. Reference specific technical details, examples, and information from the parsed content when creating the script. The parsed content provides the actual course material - use it as your primary source for technical accuracy.

OBJECTIVE:
The student needs help understanding this technical concept. Your script must be TECHNICALLY ACCURATE, include proper terminology, and provide substantive technical details while remaining accessible. Balance clarity with technical depth - don't oversimplify at the expense of accuracy.

SCRIPT STRUCTURE (15-60 seconds total, ~150 words per minute):

1. HOOK (3-5 seconds, ~12-20 words):
   - Start with a technical question, common technical mistake, or key technical insight
   - Connect to why this concept matters technically or in practice
   - Example: "Why does [technical phenomenon] happen? It's because of [technical concept]!"

2. PROBLEM SETUP (5-8 seconds, ~20-30 words):
   - Clearly state the technical problem or question this concept addresses
   - Use proper technical terminology from the concept description
   - Identify the core technical issue or mechanism
   - Make it technically specific, not generic

3. CORE EXPLANATION (30-45 seconds, ~75-110 words):
   - Break down the concept into 2-3 clear, TECHNICAL steps or components
   - Include proper technical terminology - define terms when first introduced
   - Use ONE concrete technical example that demonstrates the concept accurately
   - Reference specific technical details from the concept description
   - Explain HOW it works technically, not just WHAT it is
   - Include relevant technical specifications, mechanisms, or processes
   - Use technical analogies that preserve accuracy
   - Mention key technical considerations, limitations, or important details

4. KEY TAKEAWAY (3-5 seconds, ~12-20 words):
   - Summarize the most important TECHNICAL insight to remember
   - Include the key technical term or principle
   - End with a clear technical point or pattern

WRITING GUIDELINES:
- Tone: Conversational but technically precise - like a knowledgeable peer explaining
- Language: Use proper technical terminology - define terms naturally when first used
- Technical Depth: Include substantive technical details, mechanisms, and specifications
- Accuracy: Prioritize technical accuracy over simplification - explain correctly
- Sentences: Clear and technically precise (8-15 words average)
- Flow: Natural speaking rhythm with technical precision
- Clarity: Each sentence should build logically with proper technical progression
- Engagement: Use technical questions, emphasis on key technical points
- Educational Value: Teach the technical concept properly, not just entertain

CRITICAL TECHNICAL REQUIREMENTS:
- MUST use proper technical terminology from the concept description
- MUST include specific technical details, mechanisms, or processes
- MUST explain HOW it works technically, not just what it is
- MUST reference and incorporate details from the concept description
- MUST maintain technical accuracy - don't oversimplify incorrectly
- MUST include at least one concrete technical example with proper details
- MUST explain technical relationships, dependencies, or mechanisms when relevant
- Make it specific to THIS technical concept with proper depth
- Write exactly what should be spoken - no stage directions, brackets, or metadata
- Use natural punctuation for speech (commas for pauses, periods for stops)
- Avoid markdown, formatting, or special characters
- Target 100-150 words total for 15-60 second duration

OUTPUT FORMAT:
Return ONLY the script text that will be spoken aloud. No labels, no brackets, no timestamps, no notes. Just the words that should be read by the narrator. Include technical terms and details naturally in the flow.""")


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

