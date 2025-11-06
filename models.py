"""
Pydantic models for strict JSON schema validation.
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


# ============================================================================
# Question Models
# ============================================================================

class MCQOption(BaseModel):
    """Single MCQ option"""
    text: str = Field(..., description="Option text")


class MCQQuestion(BaseModel):
    """Multiple Choice Question"""
    question: str = Field(..., description="The question text")
    options: List[str] = Field(..., min_length=4, max_length=4, description="Exactly 4 options")
    answer: str = Field(..., description="The correct answer (must match one option)")
    explanation: str = Field(..., description="Brief explanation of why this is correct")
    variations: List[str] = Field(default=[], description="Question variations")


class FillInBlankQuestion(BaseModel):
    """Fill in the Blank Question"""
    question: str = Field(..., description="Question with blank indicated by _____")
    answer: str = Field(..., description="The correct answer to fill the blank")
    variations: List[str] = Field(default=[], description="Question variations")


class ShortAnswerQuestion(BaseModel):
    """Short Answer Question (2-4 sentences)"""
    question: str = Field(..., description="The question text")
    reference_answer: str = Field(..., description="Expected answer (2-4 sentences)")
    variations: List[str] = Field(default=[], description="Question variations")


class LongAnswerQuestion(BaseModel):
    """Long Answer Question (5-8 sentences)"""
    question: str = Field(..., description="The question text")
    reference_answer: str = Field(..., description="Detailed answer (5-8 sentences)")
    variations: List[str] = Field(default=[], description="Question variations")


# ============================================================================
# Bloom's Taxonomy Groups
# ============================================================================

class BloomTaxonomyGroup(BaseModel):
    """Group of questions for a specific Bloom's taxonomy level"""
    bloom_taxonomy: Literal["remember", "understand", "apply", "analyze", "evaluate", "create"] = Field(
        ..., description="Bloom's taxonomy level"
    )
    questions: List = Field(..., min_length=5, max_length=12, description="5-12 questions depending on topic count")


class MCQBloomGroup(BloomTaxonomyGroup):
    """MCQ questions grouped by Bloom's level"""
    questions: List[MCQQuestion] = Field(..., min_length=1)


class FillBlankBloomGroup(BloomTaxonomyGroup):
    """Fill in the blank questions grouped by Bloom's level"""
    questions: List[FillInBlankQuestion] = Field(..., min_length=1)


class ShortAnswerBloomGroup(BloomTaxonomyGroup):
    """Short answer questions grouped by Bloom's level"""
    questions: List[ShortAnswerQuestion] = Field(..., min_length=1)


class LongAnswerBloomGroup(BloomTaxonomyGroup):
    """Long answer questions grouped by Bloom's level"""
    questions: List[LongAnswerQuestion] = Field(..., min_length=1)


# ============================================================================
# Topic Questions
# ============================================================================

class TopicQuestions(BaseModel):
    """All questions for a single topic"""
    topic: str = Field(..., description="Topic name")
    content: str = Field(..., description="Topic content/description")
    MCQs: List[MCQBloomGroup] = Field(..., min_length=6, max_length=6, description="6 Bloom's levels")
    fill_in_the_blanks: List[FillBlankBloomGroup] = Field(..., min_length=6, max_length=6)
    short_answer: List[ShortAnswerBloomGroup] = Field(..., min_length=6, max_length=6)
    long_answer: List[LongAnswerBloomGroup] = Field(..., min_length=6, max_length=6)


# ============================================================================
# Chapter Questions
# ============================================================================

class ChapterQuestions(BaseModel):
    """Complete question bank for a chapter"""
    class_name: str = Field(..., description="Class name (e.g., 'Class 10')")
    subject_name: str = Field(..., description="Subject name")
    chapter_name: str = Field(..., description="Chapter name")
    total_topics: int = Field(..., ge=1, description="Number of topics")
    topics: List[TopicQuestions] = Field(..., min_length=1, description="Questions for each topic")


# ============================================================================
# Verification Models
# ============================================================================

class QuestionIssue(BaseModel):
    """Issue found in a question"""
    issue_type: Literal["duplicate", "unclear", "incorrect", "poor_quality", "grammatical"] = Field(
        ..., description="Type of issue"
    )
    description: str = Field(..., description="Description of the issue")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Issue severity")


class QuestionVerification(BaseModel):
    """Verification result for a single question"""
    question_index: int = Field(..., description="Index of the question")
    is_valid: bool = Field(..., description="Whether the question is valid")
    issues: List[QuestionIssue] = Field(default=[], description="Issues found (if any)")
    suggestion: Optional[str] = Field(None, description="Suggestion for improvement")


class TopicVerification(BaseModel):
    """Verification results for a topic"""
    topic: str = Field(..., description="Topic name")
    mcq_verifications: List[QuestionVerification] = Field(default=[])
    fill_blank_verifications: List[QuestionVerification] = Field(default=[])
    short_answer_verifications: List[QuestionVerification] = Field(default=[])
    long_answer_verifications: List[QuestionVerification] = Field(default=[])
    overall_quality: Literal["excellent", "good", "fair", "poor"] = Field(..., description="Overall quality rating")
    has_duplicates: bool = Field(..., description="Whether duplicates were found")


class ChapterVerification(BaseModel):
    """Verification results for entire chapter"""
    chapter_name: str = Field(..., description="Chapter name")
    topic_verifications: List[TopicVerification] = Field(..., description="Verifications per topic")
    overall_pass: bool = Field(..., description="Whether chapter passes quality check")
    total_issues: int = Field(..., description="Total number of issues found")


# ============================================================================
# Variation Models
# ============================================================================

class QuestionVariation(BaseModel):
    """A variation of a question"""
    variation_text: str = Field(..., description="The varied question text")
    maintains_difficulty: bool = Field(..., description="Whether difficulty level is maintained")
    maintains_concept: bool = Field(..., description="Whether core concept is maintained")
