"""
Question verification module - ensures quality and detects duplicates.
"""

from pathlib import Path
from typing import Dict, Any
import json

from models import ChapterQuestions, ChapterVerification, TopicVerification, QuestionVerification
from llm_call import get_llm_client
from instructions import VERIFICATION_SYSTEM_PROMPT, get_verification_prompt
from utils import save_backup_txt


def verify_topic_questions(
    topic_name: str,
    topic_questions: Dict[str, Any]
) -> TopicVerification:
    """
    Verify questions for a single topic.

    Args:
        topic_name: Name of the topic
        topic_questions: Questions data for the topic

    Returns:
        TopicVerification with issues and quality rating
    """
    print(f"    Verifying topic: {topic_name}")

    llm_client = get_llm_client()

    # Convert topic questions to JSON string
    questions_json = json.dumps(topic_questions, indent=2)

    # Get verification prompt
    user_prompt = get_verification_prompt(topic_name, questions_json)

    try:
        # Call LLM for verification
        verification_result = llm_client.generate_structured(
            system_prompt=VERIFICATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_schema=TopicVerification,
            temperature=0.4  # Lower temperature for more consistent verification
        )

        # Log results
        print(f"      Quality: {verification_result.overall_quality}")
        print(f"      Duplicates: {'Yes' if verification_result.has_duplicates else 'No'}")

        total_issues = (
            len(verification_result.mcq_verifications) +
            len(verification_result.fill_blank_verifications) +
            len(verification_result.short_answer_verifications) +
            len(verification_result.long_answer_verifications)
        )
        print(f"      Issues found: {total_issues}")

        return verification_result

    except Exception as e:
        print(f"      ERROR during verification: {e}")
        # Return a default failed verification
        return TopicVerification(
            topic=topic_name,
            overall_quality="poor",
            has_duplicates=False
        )


def verify_chapter_questions(
    chapter_dir: Path,
    questions_data: ChapterQuestions
) -> ChapterVerification:
    """
    Verify all questions in a chapter.

    Args:
        chapter_dir: Path to chapter directory
        questions_data: Generated chapter questions

    Returns:
        ChapterVerification with overall results
    """
    print(f"\n  Verifying chapter questions...")

    topic_verifications = []
    total_issues = 0

    for topic in questions_data.topics:
        # Convert topic to dict for verification
        topic_dict = topic.model_dump()

        # Verify this topic
        verification = verify_topic_questions(topic.topic, topic_dict)
        topic_verifications.append(verification)

        # Count issues
        for verif_list in [
            verification.mcq_verifications,
            verification.fill_blank_verifications,
            verification.short_answer_verifications,
            verification.long_answer_verifications
        ]:
            for v in verif_list:
                total_issues += len(v.issues)

    # Determine if chapter passes
    overall_pass = True
    for verification in topic_verifications:
        if verification.overall_quality in ["poor", "fair"]:
            overall_pass = False
            break
        if verification.has_duplicates:
            overall_pass = False
            break

    # Create chapter verification
    chapter_verification = ChapterVerification(
        chapter_name=questions_data.chapter_name,
        topic_verifications=topic_verifications,
        overall_pass=overall_pass,
        total_issues=total_issues
    )

    # Save verification report
    verification_file = chapter_dir / "verification_report.json"
    verification_file.write_text(
        chapter_verification.model_dump_json(indent=2),
        encoding='utf-8'
    )

    print(f"  Verification complete:")
    print(f"    Overall pass: {overall_pass}")
    print(f"    Total issues: {total_issues}")

    return chapter_verification
