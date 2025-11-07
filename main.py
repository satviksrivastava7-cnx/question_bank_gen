"""
Main pipeline for question generation, verification, and variation.

Usage:
    python -m app.main /path/to/folder
    python -m app.main /path/to/CBSE  (process all chapters)
    python -m app.main /path/to/CBSE/Class10/Medium/Math/chapter1  (single chapter)
"""

import sys
from pathlib import Path
import time
from typing import List

from models import (
    ChapterQuestions,
    TopicQuestions,
    MCQSectionResponse,
    FillBlankSectionResponse,
    ShortAnswerSectionResponse,
    LongAnswerSectionResponse
)
from llm_call import get_llm_client
from instructions import QUESTION_GENERATION_SYSTEM_PROMPT, get_section_generation_prompt
from utils import (
    save_json,
    save_backup_txt,
    get_chapter_info,
    read_topics_file,
    read_syllabus_file,
    load_json
)

from verify import verify_chapter_questions
from variate import add_variations_to_chapter

def extract_topic_content(full_content: str, topic_name: str, max_chars: int = 3000) -> str:
    """
    Extract topic-specific content from full chapter content.

    Args:
        full_content: Full chapter content
        topic_name: Topic name (e.g., "9.1 What Are Solute, Solvent, and Solution?")
        max_chars: Maximum characters to return

    Returns:
        Topic-specific content excerpt
    """
    import re

    # Try to find the topic heading in the content
    # Remove numbering from topic name for flexible matching
    topic_pattern = re.escape(topic_name)
    # Also try without the number prefix
    topic_without_number = re.sub(r'^\d+\.\d+\s+', '', topic_name)

    # Search for topic heading (as markdown heading or plain text)
    patterns = [
        f"#+ {topic_pattern}",  # Markdown heading
        f"# {topic_pattern}",
        topic_pattern,
        topic_without_number
    ]

    topic_start = -1
    for pattern in patterns:
        match = re.search(pattern, full_content, re.IGNORECASE)
        if match:
            topic_start = match.start()
            break

    if topic_start == -1:
        # Topic not found, return first max_chars of chapter
        return full_content[:max_chars]

    # Extract content from topic start
    # Try to find next topic heading or end of content
    next_topic_match = re.search(r'\n#+ \d+\.\d+', full_content[topic_start + len(topic_name):])

    if next_topic_match:
        topic_end = topic_start + len(topic_name) + next_topic_match.start()
    else:
        # No next topic found, take max_chars from topic start
        topic_end = topic_start + max_chars

    topic_content = full_content[topic_start:topic_end]

    # If still too large, truncate
    if len(topic_content) > max_chars:
        topic_content = topic_content[:max_chars] + "\n\n[Content truncated for API limits]"

    return topic_content


def generate_questions_for_topic(
    topic_name: str,
    topic_content: str,
    class_name: str,
    subject_name: str,
    chapter_name: str,
    questions_per_level: int = 5
) -> TopicQuestions:
    """Generate questions for a single topic."""
    print(f"    Generating questions for: {topic_name}")

    llm_client = get_llm_client()

    section_schemas = [
        ("MCQs", "MCQ", MCQSectionResponse, "MCQs"),
        ("fill_in_the_blanks", "Fill-in-the-Blank", FillBlankSectionResponse, "fill_in_the_blanks"),
        ("short_answer", "Short Answer", ShortAnswerSectionResponse, "short_answer"),
        ("long_answer", "Long Answer", LongAnswerSectionResponse, "long_answer"),
    ]

    section_results = {}
    questions_per_type = questions_per_level * 6

    for section_key, display_name, schema, attr in section_schemas:
        print(f"      -> {display_name} questions")
        section_prompt = get_section_generation_prompt(
            question_type_key=section_key,
            topic=topic_name,
            content=topic_content,
            class_name=class_name,
            subject_name=subject_name,
            chapter_name=chapter_name,
            questions_per_level=questions_per_level
        )

        try:
            section_response = llm_client.generate_structured(
                system_prompt=QUESTION_GENERATION_SYSTEM_PROMPT,
                user_prompt=section_prompt,
                response_schema=schema,
                temperature=0.6
            )
            section_results[attr] = getattr(section_response, attr)
            print(f"        ✓ Generated {questions_per_type} {display_name.lower()} questions")
        except Exception as section_error:
            print(f"        ✗ ERROR generating {display_name.lower()} questions: {section_error}")
            raise

    total_questions = questions_per_type * len(section_schemas)
    print(f"      ✓ Combined total: {total_questions} questions (4 types × 6 levels × {questions_per_level} questions)")

    return TopicQuestions(
        topic=topic_name,
        content=topic_content,
        MCQs=section_results["MCQs"],
        fill_in_the_blanks=section_results["fill_in_the_blanks"],
        short_answer=section_results["short_answer"],
        long_answer=section_results["long_answer"]
    )


def process_chapter(chapter_dir: Path, skip_if_exists: bool = True) -> bool:
    """
    Process a single chapter: generate, verify, and variate questions.

    Args:
        chapter_dir: Path to chapter directory
        skip_if_exists: Whether to skip if questions.json already exists

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"Processing chapter: {chapter_dir.name}")
    print(f"{'='*80}")

    # Check if questions.json already exists
    questions_file = chapter_dir / "questions.json"
    if skip_if_exists and questions_file.exists():
        print(f"  ⏭  Skipping (questions.json already exists)")
        return True

    # Get chapter info
    try:
        chapter_info = get_chapter_info(chapter_dir)
        class_name = chapter_info['class_name']
        subject_name = chapter_info['subject_name']
        chapter_name = chapter_info['chapter_name']
    except Exception as e:
        print(f"  ✗ ERROR: Could not extract chapter info: {e}")
        return False

    print(f"  Class: {class_name}")
    print(f"  Subject: {subject_name}")
    print(f"  Chapter: {chapter_name}")

    # Get subject directory (parent of chapter_dir)
    subject_dir = chapter_dir.parent

    # Read syllabus.json from subject directory
    try:
        syllabus_data = read_syllabus_file(subject_dir)
    except Exception as e:
        print(f"  ✗ ERROR: Could not read syllabus.json: {e}")
        return False

    # Find the chapter in syllabus
    chapters_list = syllabus_data.get('chapters', syllabus_data.get('Chapters', []))
    current_chapter_data = None

    # Extract chapter number from directory name (e.g., "chapter 9" -> "9")
    import re
    chapter_number_match = re.search(r'\d+', chapter_dir.name)
    chapter_number = chapter_number_match.group() if chapter_number_match else None

    for chapter_entry in chapters_list:
        # Support both 'Chapter' and 'chapter' keys
        syllabus_chapter = (chapter_entry.get('Chapter') or chapter_entry.get('chapter', '')).lower()

        # Try multiple matching strategies
        if syllabus_chapter == chapter_name.lower() or \
           chapter_dir.name.lower() in syllabus_chapter or \
           (chapter_number and syllabus_chapter == chapter_number):
            current_chapter_data = chapter_entry
            break

    if not current_chapter_data:
        print(f"  ✗ ERROR: Chapter '{chapter_name}' not found in syllabus.json")
        print(f"  Available chapters: {[c.get('chapter', c.get('Chapter')) for c in chapters_list[:5]]}")
        return False

    # Get topics from syllabus (support both 'Topics' and 'topics')
    topics_list = current_chapter_data.get('topics', current_chapter_data.get('Topics', []))

    if not topics_list:
        print(f"  ✗ ERROR: No topics found for chapter in syllabus.json")
        return False

    print(f"  Topics: {len(topics_list)}")

    # Determine questions per level based on topic count
    if len(topics_list) < 5:
        questions_per_level = 8  # Can be 8-12, using 8 as default
        print(f"  Questions per level: 8-12 (fewer than 5 topics)")
    else:
        questions_per_level = 5  # Can be 5-8, using 5 as default
        print(f"  Questions per level: 5-8 (5+ topics)")

    # Read chapter_content.json for full content
    chapter_content_file = chapter_dir / "chapter_content.json"
    if not chapter_content_file.exists():
        print(f"  ⚠ WARNING: chapter_content.json not found, using empty content")
        chapter_full_content = ""
    else:
        chapter_content_data = load_json(chapter_content_file)
        chapter_full_content = chapter_content_data.get('content', '')

    # STAGE 1: Generate Questions
    print(f"\n  [STAGE 1] Generating questions...")
    print(f"  {'-'*76}")

    topic_questions = []
    failed_topics = []

    for idx, topic_name in enumerate(topics_list, 1):
        # Topics from syllabus.json are just strings
        print(f"  [{idx}/{len(topics_list)}] {topic_name}")

        # Extract topic-specific content from full chapter (find section with topic heading)
        topic_content = extract_topic_content(chapter_full_content, topic_name)

        try:
            questions = generate_questions_for_topic(
                topic_name,
                topic_content,
                class_name,
                subject_name,
                chapter_name,
                questions_per_level
            )
            topic_questions.append(questions)

            # Rate limiting
            time.sleep(2)

        except Exception as e:
            print(f"      ✗ Failed to generate questions: {e}")
            failed_topics.append(topic_name)
            continue

    if failed_topics:
        print(f"\n  ⚠ WARNING: Failed to generate {len(failed_topics)} topics")
        for missing_topic in failed_topics:
            print(f"    - {missing_topic}")

    if not topic_questions:
        print("\n  ✗ ERROR: No topics were generated successfully; skipping chapter")
        return False

    # Create chapter questions object
    chapter_questions = ChapterQuestions(
        class_name=class_name,
        subject_name=subject_name,
        chapter_name=chapter_name,
        total_topics=len(topic_questions),
        topics=topic_questions
    )

    # Save initial questions
    save_json(chapter_questions, questions_file)
    print(f"\n  ✓ Initial questions saved to: questions.json")

    # Save backup
    backup_path = save_backup_txt(
        chapter_questions,
        chapter_dir,
        class_name,
        subject_name,
        chapter_name,
        stage="generated"
    )
    print(f"  ✓ Backup saved to: {backup_path.name}")

    # STAGE 2: Verify Questions
    print(f"\n  [STAGE 2] Verifying questions...")
    print(f"  {'-'*76}")

    try:
        verification = verify_chapter_questions(chapter_dir, chapter_questions)

        if not verification.overall_pass:
            print(f"\n  ⚠ WARNING: Verification found {verification.total_issues} issues")
            print(f"  Review verification_report.json for details")
        else:
            print(f"  ✓ Verification passed with {verification.total_issues} minor issues")

        # Save backup after verification
        backup_path = save_backup_txt(
            chapter_questions,
            chapter_dir,
            class_name,
            subject_name,
            chapter_name,
            stage="verified"
        )

    except Exception as e:
        print(f"  ✗ Verification error: {e}")
        print(f"  Continuing to variation generation...")

    # STAGE 3: Generate Variations
    print(f"\n  [STAGE 3] Generating variations...")
    print(f"  {'-'*76}")

    try:
        chapter_questions_with_variations = add_variations_to_chapter(
            chapter_dir,
            chapter_questions
        )

        # Save final questions with variations
        save_json(chapter_questions_with_variations, questions_file)
        print(f"\n  ✓ Final questions saved to: questions.json")

        # Save final backup
        backup_path = save_backup_txt(
            chapter_questions_with_variations,
            chapter_dir,
            class_name,
            subject_name,
            chapter_name,
            stage="varied"
        )
        print(f"  ✓ Final backup saved to: {backup_path.name}")

    except Exception as e:
        print(f"  ✗ Variation generation error: {e}")
        print(f"  Questions saved without variations")

    print(f"\n{'='*80}")
    print(f"✓ Chapter processing complete!")
    print(f"{'='*80}")

    return True


def find_chapters_to_process(root_path: Path) -> List[Path]:
    """
    Find all chapter directories that need processing.
    Now looks for chapter_content.json instead of topics.json.

    Args:
        root_path: Root path to search

    Returns:
        List of chapter directory paths
    """
    chapters = []

    if root_path.is_dir():
        # Check if this is a chapter directory (has chapter_content.json)
        if (root_path / "chapter_content.json").exists():
            chapters.append(root_path)
        else:
            # Recursively find chapter directories
            for content_file in root_path.rglob("chapter_content.json"):
                chapter_dir = content_file.parent
                chapters.append(chapter_dir)

    return sorted(chapters)


def main(folder_path: str):
    """
    Main entry point for question generation pipeline.

    Args:
        folder_path: Path to folder to process
    """
    root_path = Path(folder_path)

    if not root_path.exists():
        print(f"ERROR: Path does not exist: {folder_path}")
        sys.exit(1)

    print("="*80)
    print("QUESTION GENERATION PIPELINE")
    print("="*80)
    print(f"Root path: {root_path}")

    # Find chapters to process
    chapters = find_chapters_to_process(root_path)

    if not chapters:
        print(f"\nNo chapters found with chapter_content.json")
        sys.exit(1)

    print(f"\nFound {len(chapters)} chapters to process")

    # Process each chapter
    processed = 0
    skipped = 0
    failed = 0

    for idx, chapter_dir in enumerate(chapters, 1):
        print(f"\n[{idx}/{len(chapters)}]")

        try:
            success = process_chapter(chapter_dir, skip_if_exists=True)
            if success:
                if (chapter_dir / "questions.json").stat().st_size > 0:
                    processed += 1
                else:
                    skipped += 1
            else:
                failed += 1
        except Exception as e:
            print(f"ERROR processing chapter: {e}")
            failed += 1

    # Summary
    print("\n" + "="*80)
    print("PIPELINE COMPLETE")
    print("="*80)
    print(f"Processed: {processed}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print("="*80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.main <folder_path>")
        print("\nExamples:")
        print("  python -m app.main /path/to/CBSE")
        print("  python -m app.main /path/to/Sample")
        print("  python -m app.main /path/to/CBSE/Class10/Medium/Math/chapter1")
        sys.exit(1)

    folder_path = sys.argv[1]
    main(folder_path)
