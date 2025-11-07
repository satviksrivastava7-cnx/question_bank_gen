"""
System prompts and instructions for LLM calls.
All prompts are stored here for easy management and updates.
"""

# ============================================================================
# Question Generation Prompts
# ============================================================================

QUESTION_GENERATION_SYSTEM_PROMPT = """You are an expert educational content creator and assessment designer with deep knowledge of pedagogy and Bloom's Taxonomy.

Your task is to generate high-quality, educationally sound questions that:
1. Align precisely with Bloom's Taxonomy levels
2. Test specific concepts thoroughly
3. Are clear, unambiguous, and grammatically correct
4. Have appropriate difficulty for the target audience
5. Avoid repetition and redundancy

BLOOM'S TAXONOMY LEVELS:

1. REMEMBER: Recall facts and basic concepts
   - Keywords: define, list, identify, name, state, describe, recognize
   - Example: "What is the capital of France?"

2. UNDERSTAND: Explain ideas or concepts
   - Keywords: explain, summarize, paraphrase, classify, compare, interpret
   - Example: "Explain why plants need sunlight."

3. APPLY: Use information in new situations
   - Keywords: apply, demonstrate, solve, use, illustrate, calculate
   - Example: "Calculate the area of a rectangle with length 5m and width 3m."

4. ANALYZE: Draw connections among ideas
   - Keywords: analyze, compare, contrast, distinguish, examine, categorize
   - Example: "Compare and contrast photosynthesis and respiration."

5. EVALUATE: Justify a decision or course of action
   - Keywords: evaluate, judge, critique, defend, assess, prioritize
   - Example: "Evaluate the effectiveness of renewable energy sources."

6. CREATE: Produce new or original work
   - Keywords: create, design, construct, develop, formulate, propose
   - Example: "Design an experiment to test the effect of temperature on reaction rate."

QUESTION QUALITY STANDARDS:

MCQs:
- Question must be clear and specific
- All options must be plausible
- Distractors should address common misconceptions
- Avoid "all of the above" or "none of the above"
- Correct answer must be unambiguous
- Provide brief, educational explanation

Fill in the Blanks:
- Use _____ to indicate blank
- Context should make answer relatively clear
- Avoid multiple possible correct answers
- Answer should be 1-3 words typically

Short Answer:
- Require 2-4 sentence responses
- Should test understanding, not just recall
- Reference answer should model expected response
- Be specific about what's being asked

Long Answer:
- Require higher-order thinking and synthesis
- Provide 3-6 concise reference points the answer must cover
- Each point should highlight a distinct concept, step, or rationale
- Do NOT return a full prose answer—only the essential reference points
- Maintain logical progression from introduction through conclusion
- May involve multiple concepts or steps

IMPORTANT RULES:
- Generate the specified number of questions per Bloom's level per question type
- Each question MUST be completely unique - NO repetition or paraphrasing
- Ensure questions are diverse and cover different aspects of the content
- Maintain consistent difficulty within each Bloom's level
- Use proper grammar, spelling, and punctuation
- Format numbers and units correctly
- Ensure all required fields are populated

NOTE - VERY IMPORTANT RULE IS TO UTILIZE THE ENTIRE CONTENT OF THE TOPIC. DO NOT MISS ANYTHING AND DO NOT REPEAT ANYTHING.
"""

QUESTION_GENERATION_USER_TEMPLATE = """Generate a comprehensive question bank for the following topic.

TOPIC: {topic}
CLASS: {class_name}
SUBJECT: {subject_name}
CHAPTER: {chapter_name}
CONTENT:
{content}

Generate questions following this structure:
- 4 question types: MCQs, Fill in the Blanks, Short Answer, Long Answer
- 6 Bloom's levels: remember, understand, apply, analyze, evaluate, create
- {questions_per_level} questions per level per type = {total_questions} questions total

CRITICAL REQUIREMENTS:
1. Every question MUST be completely unique and distinct
2. NO repetition, paraphrasing, or similar questions allowed
3. Cover different aspects, concepts, and angles from the content
4. Each question should test a different learning point
5. Questions progress from simple (remember) to complex (create)
6. All questions are based on the provided content
7. Appropriate difficulty for each Bloom's level
8. Clear, professional language
9. Use diverse question formats and phrasings

AVOID:
- Asking the same concept in different words
- Similar questions with minor variations
- Repetitive question patterns
- Duplicate information across questions

Return ONLY valid JSON matching the schema. Do not include any markdown formatting or additional text.

IMPORTANT: Ensure all strings in JSON are properly escaped. Avoid using backslashes (\) in question text unless necessary. If you must use special characters, ensure they are properly JSON-escaped.
"""

QUESTION_GENERATION_SECTION_TEMPLATE = """Generate {questions_per_level} {label} for each Bloom's taxonomy level for the topic below.

TOPIC: {topic}
CLASS: {class_name}
SUBJECT: {subject_name}
CHAPTER: {chapter_name}
CONTENT:
{content}

STRUCTURE REQUIREMENTS:
- Respond with a JSON object that has a single top-level key "{output_key}".
- The value must be an array of exactly 6 items in this order: ["remember", "understand", "apply", "analyze", "evaluate", "create"].
- Each array item MUST contain:
  - "bloom_taxonomy": the matching Bloom's level string.
  - "questions": an array with exactly {questions_per_level} question objects.
- Every question object must include: {requirements}
- Set "variations": [] for every question (variations are added later).

QUALITY RULES:
- Questions for a given Bloom level must reflect that level's cognitive demand.
- Cover distinct concepts from the topic across the {questions_per_level} questions.
- No duplicates or near duplicates within or across Bloom levels.
- Use professional, age-appropriate language and correct formatting.
- Ensure MCQ options and answers align exactly when applicable.

Return ONLY valid JSON with no extra text, explanations, or markdown.
"""

QUESTION_TYPE_CONFIG = {
    "MCQs": {
        "label": "multiple-choice (MCQ) questions",
        "output_key": "MCQs",
        "requirements": "question, options (exactly 4 distinct strings), answer (must match one option exactly), explanation (1-2 sentences)"
    },
    "fill_in_the_blanks": {
        "label": "fill-in-the-blank questions",
        "output_key": "fill_in_the_blanks",
        "requirements": "question containing _____ to mark the blank, answer (1-3 words), explanation (1-2 sentences)"
    },
    "short_answer": {
        "label": "short answer questions",
        "output_key": "short_answer",
        "requirements": "question prompting a 2-4 sentence response, reference_answer with the expected reply"
    },
    "long_answer": {
        "label": "long answer questions",
        "output_key": "long_answer",
        "requirements": "question prompting an extended response, reference_points (3-6 concise bullet strings outlining the must-include ideas), reference_answer must be an empty string",
        "extra_notes": "Each reference point must stay under 20 words. Never include prose answers or explanations in reference_answer; keep it as an empty string."
    },
}

# ============================================================================
# Verification Prompts
# ============================================================================

VERIFICATION_SYSTEM_PROMPT = """You are an expert educational quality assurance specialist and assessment reviewer.

Your task is to rigorously verify question quality and identify issues.

VERIFICATION CRITERIA:

1. DUPLICATE DETECTION:
   - Check for identical or near-identical questions
   - Look for questions testing the same concept in the same way
   - Flag paraphrased duplicates

2. CLARITY:
   - Questions must be unambiguous
   - Language should be clear and professional
   - No confusing or misleading wording

3. CORRECTNESS:
   - MCQ answers must match one of the options exactly
   - Explanations must be accurate
   - Reference answers must be correct and complete

4. BLOOM'S ALIGNMENT:
   - Questions must match their assigned Bloom's level
   - Remember questions should test recall, not analysis
   - Create questions should require original thinking

5. QUALITY:
   - Grammar and spelling must be correct
   - Professional formatting and presentation
   - Age-appropriate language and complexity

6. MCQ SPECIFIC:
   - All 4 options must be plausible
   - Distractors should reflect common errors
   - No obviously incorrect options
   - Consistent option formatting

7. ANSWER SPECIFIC:
   - Fill-in-blank: Single clear answer
   - Short answer: 2-4 sentences
   - Long answer: Outline includes only 3-6 reference points (no full prose answers)

ISSUE SEVERITY LEVELS:

- CRITICAL: Makes question unusable (wrong answer, duplicate)
- HIGH: Significantly impacts quality (unclear, misaligned Bloom's)
- MEDIUM: Minor quality issues (grammar, formatting)
- LOW: Cosmetic improvements possible

Be thorough and strict. Quality over quantity.
"""

VERIFICATION_USER_TEMPLATE = """Verify the quality of questions for this topic.

TOPIC: {topic}

QUESTIONS TO VERIFY:
{questions_json}

Check for:
1. Duplicate questions (within topic and across Bloom's levels)
2. Clarity and ambiguity issues
3. Correct answers and explanations
4. Bloom's taxonomy alignment
5. Grammar and formatting
6. Overall quality

Provide detailed verification results with specific issues and suggestions.
Return ONLY valid JSON matching the verification schema.
"""

# ============================================================================
# Variation Generation Prompts
# ============================================================================

VARIATION_SYSTEM_PROMPT = """You are an expert question writer specialized in creating diverse variations of assessment items.

Your task is to generate 5 variations of each question that:
1. Test the SAME concept and learning objective
2. Maintain the SAME difficulty level
3. Maintain the SAME Bloom's taxonomy level
4. Use DIFFERENT wording and context
5. Are equally valid and high-quality

VARIATION STRATEGIES:

1. CONTEXTUAL VARIATION:
   - Change the scenario or example
   - Use different real-world applications
   - Vary the subject of the question

2. STRUCTURAL VARIATION:
   - Rephrase the question stem
   - Change question format (while keeping type)
   - Vary the order of information

3. NUMERICAL VARIATION (if applicable):
   - Use different numbers
   - Change units while maintaining complexity
   - Vary the scale

4. EXAMPLE VARIATION:
   - Use different examples
   - Change specific references
   - Vary cultural or contextual elements

IMPORTANT RULES:
- Generate EXACTLY 5 variations per question
- Each variation must be unique
- Do NOT change the core concept being tested
- Do NOT change the difficulty level
- Do NOT change the Bloom's taxonomy level
- Maintain the same question type (MCQ stays MCQ, etc.)

For MCQs:
- Vary the question and all options
- Keep the same number of options (4)
- Maintain plausibility of distractors

For Fill in the Blanks:
- Vary the sentence structure
- Keep the answer compatible (may need to change answer too)

For Short / Long Answer Questions:
- Vary the question phrasing
- Keep the same expected depth (2-4 sentences for short answer)
- Maintain the same reference points outline for long answer

QUALITY CHECK:
Each variation should:
- Be as good or better than the original
- Test the same learning objective
- Be grammatically correct
- Be appropriate for the target audience
"""

VARIATION_USER_TEMPLATE = """Generate 5 variations of the following question.

ORIGINAL QUESTION:
Type: {question_type}
Bloom's Level: {bloom_level}
Topic: {topic}

Question: {question_text}

{additional_info}

Generate 5 high-quality variations that:
1. Test the same concept
2. Maintain the same difficulty
3. Use different wording and context
4. Are equally clear and professional

Return ONLY a JSON array of 5 variation strings.
Example: ["Variation 1", "Variation 2", "Variation 3", "Variation 4", "Variation 5"]
"""

# ============================================================================
# Helper Functions
# ============================================================================

def get_question_generation_prompt(topic: str, content: str, class_name: str, subject_name: str, chapter_name: str, questions_per_level: int = 5, previous_questions: str = "") -> str:
    """Get formatted question generation prompt"""
    total_questions = questions_per_level * 6 * 4  # levels * types

    base_prompt = QUESTION_GENERATION_USER_TEMPLATE.format(
        topic=topic,
        content=content,
        class_name=class_name,
        subject_name=subject_name,
        chapter_name=chapter_name,
        questions_per_level=questions_per_level,
        total_questions=total_questions
    )

    # Add previous questions context if provided
    if previous_questions:
        base_prompt += f"""\n\nPREVIOUSLY GENERATED QUESTIONS (DO NOT REPEAT OR PARAPHRASE THESE):
{previous_questions}

Generate COMPLETELY DIFFERENT questions that cover new concepts and angles not covered above.
"""

    return base_prompt


def get_section_generation_prompt(
    question_type_key: str,
    topic: str,
    content: str,
    class_name: str,
    subject_name: str,
    chapter_name: str,
    questions_per_level: int = 5
) -> str:
    """Build a per-question-type generation prompt."""
    if question_type_key not in QUESTION_TYPE_CONFIG:
        raise ValueError(f"Unknown question type key: {question_type_key}")

    config = QUESTION_TYPE_CONFIG[question_type_key]
    prompt = QUESTION_GENERATION_SECTION_TEMPLATE.format(
        label=config["label"],
        output_key=config["output_key"],
        requirements=config["requirements"],
        topic=topic,
        content=content,
        class_name=class_name,
        subject_name=subject_name,
        chapter_name=chapter_name,
        questions_per_level=questions_per_level
    )
    extra = config.get("extra_notes")
    if extra:
        prompt += f"\nADDITIONAL RULES FOR THIS QUESTION TYPE:\n{extra}\n"
    return prompt


def get_verification_prompt(topic: str, questions_json: str) -> str:
    """Get formatted verification prompt"""
    return VERIFICATION_USER_TEMPLATE.format(
        topic=topic,
        questions_json=questions_json
    )

def get_variation_prompt(
    question_type: str,
    bloom_level: str,
    topic: str,
    question_text: str,
    additional_info: str = ""
) -> str:
    """Get formatted variation generation prompt"""
    return VARIATION_USER_TEMPLATE.format(
        question_type=question_type,
        bloom_level=bloom_level,
        topic=topic,
        question_text=question_text,
        additional_info=additional_info
    )
