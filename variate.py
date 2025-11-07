"""
Question variation module - generates 5 variations per question.
"""

from pathlib import Path
from typing import List, Dict, Any
import time
import json

from models import ChapterQuestions, MCQQuestion, FillInBlankQuestion, ShortAnswerQuestion, LongAnswerQuestion
from llm_call import get_llm_client
from instructions import VARIATION_SYSTEM_PROMPT, get_variation_prompt
from utils import save_json


def _normalize_variation_item(item: Any, question_type: str) -> str:
    """
    Convert a variation response (string/dict) into a clean string.
    """
    if isinstance(item, str):
        return item.strip()

    if isinstance(item, dict):
        # Handle bundled variations like {"variation_1": "...", ...}
        if any(key.startswith("variation_") for key in item.keys()):
            values = [
                str(value).strip()
                for key, value in sorted(item.items())
                if key.startswith("variation_") and str(value).strip()
            ]
            if values:
                return " | ".join(values)

        # Common text fields
        for key in ("question", "variation_text", "variation", "text", "prompt"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                base = value.strip()
                break
        else:
            base = ""

        # Include options/answers for MCQs to preserve context
        if question_type == "MCQ":
            options = item.get("options")
            if isinstance(options, list):
                option_text = "; ".join(str(opt).strip() for opt in options if str(opt).strip())
                if option_text:
                    base = f"{base} | Options: {option_text}" if base else f"Options: {option_text}"
            answer = item.get("answer")
            if isinstance(answer, str) and answer.strip():
                base = f"{base} | Answer: {answer.strip()}" if base else f"Answer: {answer.strip()}"

        # Include outline data for long answers when present
        reference_points = item.get("reference_points")
        if isinstance(reference_points, list):
            outline = "; ".join(str(point).strip() for point in reference_points if str(point).strip())
            if outline:
                base = f"{base} | Key points: {outline}" if base else f"Key points: {outline}"

        reference_answer = item.get("reference_answer")
        if isinstance(reference_answer, str) and reference_answer.strip():
            base = f"{base} | Reference answer: {reference_answer.strip()}" if base else reference_answer.strip()

        if base:
            return base

        # Fallback to JSON dump if nothing usable extracted
        return json.dumps(item, ensure_ascii=False)

    # Generic fallback
    return str(item).strip()


def generate_variations_for_question(
    question: Any,
    question_type: str,
    bloom_level: str,
    topic: str
) -> List[str]:
    """
    Generate 5 variations for a single question.

    Args:
        question: Question object (MCQ, FillBlank, etc.)
        question_type: Type of question
        bloom_level: Bloom's taxonomy level
        topic: Topic name

    Returns:
        List of 5 variation strings
    """
    llm_client = get_llm_client()

    # Prepare question text and additional info based on type
    if isinstance(question, MCQQuestion):
        question_text = question.question
        additional_info = f"""Options:
{chr(10).join(f'- {opt}' for opt in question.options)}

Correct Answer: {question.answer}

For variations:
- Vary both the question and all options
- Maintain 4 plausible options
- Ensure one option is clearly correct"""

    elif isinstance(question, FillInBlankQuestion):
        question_text = question.question
        additional_info = f"""Answer: {question.answer}

For variations:
- Vary the sentence structure
- Keep the blank appropriate for the concept
- Answer may need to change to fit new context"""

    elif isinstance(question, ShortAnswerQuestion):
        question_text = question.question
        reference = question.reference_answer
        additional_info = f"""Reference Answer: {reference}

For variations:
- Vary the question phrasing
- Maintain the same concept being tested
- Keep expected answer length similar"""

    elif isinstance(question, LongAnswerQuestion):
        question_text = question.question
        if question.reference_points:
            reference_outline = "\n".join(f"- {point}" for point in question.reference_points)
            reference_header = f"Reference Points:\n{reference_outline}"
        else:
            reference_header = f"Legacy Reference Answer: {question.reference_answer or ''}"
        additional_info = f"""{reference_header}

For variations:
- Vary the question phrasing
- Maintain every reference point / key idea
- Keep the expected depth and structure (introduction, development, conclusion)"""

    else:
        # Fallback
        question_text = str(question)
        additional_info = ""

    # Get variation prompt
    user_prompt = get_variation_prompt(
        question_type=question_type,
        bloom_level=bloom_level,
        topic=topic,
        question_text=question_text,
        additional_info=additional_info
    )

    try:
        # Generate variations
        response = llm_client.generate_json(
            system_prompt=VARIATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.8  # Higher temperature for more diversity
        )

        # Extract variations
        if isinstance(response, dict) and 'variations' in response:
            raw_variations = response['variations']
        else:
            raw_variations = response

        if not isinstance(raw_variations, list):
            raw_variations = [raw_variations]

        variations = []
        for item in raw_variations:
            normalized = _normalize_variation_item(item, question_type)
            if normalized:
                variations.append(normalized)

        # Ensure we have 5 variations
        if len(variations) < 5:
            print(f"      WARNING: Only got {len(variations)} variations, expected 5")
            # Pad with duplicates if needed (not ideal but ensures structure)
            while len(variations) < 5:
                variations.append(variations[0] if variations else question_text)

        # Limit to 5
        variations = variations[:5]

        return variations

    except Exception as e:
        print(f"      ERROR generating variations: {e}")
        # Return empty variations on error
        return []


def add_variations_to_chapter(
    chapter_dir: Path,
    questions_data: ChapterQuestions
) -> ChapterQuestions:
    """
    Add variations to all questions in a chapter.

    Args:
        chapter_dir: Path to chapter directory
        questions_data: Chapter questions data

    Returns:
        Updated ChapterQuestions with variations
    """
    print(f"\n  Generating variations for all questions...")

    total_questions = 0
    total_variations = 0

    for topic_idx, topic in enumerate(questions_data.topics):
        print(f"    [{topic_idx + 1}/{len(questions_data.topics)}] Topic: {topic.topic}")

        # MCQs
        for bloom_group in topic.MCQs:
            bloom_level = bloom_group.bloom_taxonomy
            for q_idx, question in enumerate(bloom_group.questions):
                if not question.variations:  # Only generate if not already present
                    variations = generate_variations_for_question(
                        question, "MCQ", bloom_level, topic.topic
                    )
                    question.variations = variations
                    total_questions += 1
                    total_variations += len(variations)

                # Rate limiting
                time.sleep(0.5)

        # Fill in the Blanks
        for bloom_group in topic.fill_in_the_blanks:
            bloom_level = bloom_group.bloom_taxonomy
            for question in bloom_group.questions:
                if not question.variations:
                    variations = generate_variations_for_question(
                        question, "Fill in the Blank", bloom_level, topic.topic
                    )
                    question.variations = variations
                    total_questions += 1
                    total_variations += len(variations)

                time.sleep(0.5)

        # Short Answer
        for bloom_group in topic.short_answer:
            bloom_level = bloom_group.bloom_taxonomy
            for question in bloom_group.questions:
                if not question.variations:
                    variations = generate_variations_for_question(
                        question, "Short Answer", bloom_level, topic.topic
                    )
                    question.variations = variations
                    total_questions += 1
                    total_variations += len(variations)

                time.sleep(0.5)

        # Long Answer
        for bloom_group in topic.long_answer:
            bloom_level = bloom_group.bloom_taxonomy
            for question in bloom_group.questions:
                if not question.variations:
                    variations = generate_variations_for_question(
                        question, "Long Answer", bloom_level, topic.topic
                    )
                    question.variations = variations
                    total_questions += 1
                    total_variations += len(variations)

                time.sleep(0.5)

        print(f"      Completed variations for topic")

    print(f"  Variation generation complete:")
    print(f"    Questions processed: {total_questions}")
    print(f"    Total variations: {total_variations}")

    return questions_data
