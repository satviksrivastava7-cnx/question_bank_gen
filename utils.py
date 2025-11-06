"""
Utility functions for file I/O and backup.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
from pydantic import BaseModel


def save_json(data: Any, filepath: Path, indent: int = 2) -> None:
    """
    Save data to JSON file.

    Args:
        data: Data to save (Pydantic model or dict)
        filepath: Path to save file
        indent: JSON indentation level
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Convert Pydantic model to dict if needed
    if isinstance(data, BaseModel):
        json_data = data.model_dump()
    else:
        json_data = data

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=indent, ensure_ascii=False)


def load_json(filepath: Path) -> Dict[str, Any]:
    """
    Load JSON from file.

    Args:
        filepath: Path to JSON file

    Returns:
        Parsed JSON dictionary
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_backup_txt(
    data: Any,
    directory: Path,
    class_name: str,
    subject_name: str,
    chapter_name: str,
    stage: str = "generated"
) -> Path:
    """
    Save backup in text format for safety.

    Args:
        data: Data to backup
        directory: Directory to save backup
        class_name: Class name
        subject_name: Subject name
        chapter_name: Chapter name
        stage: Processing stage (generated, verified, varied)

    Returns:
        Path to backup file
    """
    backup_dir = directory / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_class = class_name.replace(' ', '_')
    safe_subject = subject_name.replace(' ', '_')
    safe_chapter = chapter_name.replace(' ', '_')

    filename = f"{safe_class}_{safe_subject}_{safe_chapter}_{stage}_{timestamp}.txt"
    filepath = backup_dir / filename

    # Convert to JSON string for text backup
    if isinstance(data, BaseModel):
        json_str = data.model_dump_json(indent=2)
    else:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"Backup: {class_name} - {subject_name} - {chapter_name}\n")
        f.write(f"Stage: {stage}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write("=" * 80 + "\n\n")
        f.write(json_str)

    return filepath


def get_chapter_info(chapter_dir: Path) -> Dict[str, str]:
    """
    Extract class, subject, and chapter info from directory path.

    Args:
        chapter_dir: Path to chapter directory

    Returns:
        Dictionary with class_name, subject_name, chapter_name
    """
    parts = chapter_dir.parts

    # Find CBSE or Sample in path
    root_folder = None
    for folder in ['CBSE', 'Sample']:
        if folder in parts:
            root_folder = folder
            break

    if not root_folder:
        raise ValueError(f"Could not find CBSE or Sample in path: {chapter_dir}")

    root_idx = parts.index(root_folder)

    # Different path structures
    if root_folder == 'Sample':
        # Sample/Class X/Subject/chapter Y
        class_name = parts[root_idx + 1] if root_idx + 1 < len(parts) else "Unknown"
        subject_name = parts[root_idx + 2] if root_idx + 2 < len(parts) else "Unknown"
        chapter_name = parts[root_idx + 3] if root_idx + 3 < len(parts) else "Unknown"
    else:
        # CBSE/Class X/Medium/Subject/chapter Y
        class_name = parts[root_idx + 1] if root_idx + 1 < len(parts) else "Unknown"
        # medium = parts[root_idx + 2]
        subject_name = parts[root_idx + 3] if root_idx + 3 < len(parts) else "Unknown"
        chapter_name = parts[root_idx + 4] if root_idx + 4 < len(parts) else "Unknown"

    return {
        "class_name": class_name,
        "subject_name": subject_name,
        "chapter_name": chapter_name
    }


def read_topics_file(topics_file: Path) -> Dict[str, Any]:
    """
    Read and parse topics.json file.

    Args:
        topics_file: Path to topics.json

    Returns:
        Parsed topics data
    """
    return load_json(topics_file)


def read_syllabus_file(subject_dir: Path) -> Dict[str, Any]:
    """
    Read and parse syllabus.json file from subject directory.

    Args:
        subject_dir: Path to subject directory

    Returns:
        Parsed syllabus data
    """
    syllabus_file = subject_dir / "syllabus.json"
    if not syllabus_file.exists():
        raise FileNotFoundError(f"syllabus.json not found in {subject_dir}")
    return load_json(syllabus_file)
