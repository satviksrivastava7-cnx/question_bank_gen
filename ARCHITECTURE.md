# Architecture Documentation

## System Overview

A production-grade, three-stage pipeline for generating comprehensive educational question banks with AI-powered quality assurance and question variation.

## Core Components

### 1. **models.py** - Data Models
Pydantic models ensuring strict type safety and JSON schema validation.

**Key Models:**
- `MCQQuestion`, `FillInBlankQuestion`, `ShortAnswerQuestion`, `LongAnswerQuestion`
- `BloomTaxonomyGroup` - Groups questions by Bloom's level
- `TopicQuestions` - Complete question set for a topic
- `ChapterQuestions` - Full chapter with all topics
- `ChapterVerification` - Quality assurance results
- `QuestionVariation` - Generated variations

**Validation Features:**
- Required fields enforcement
- Min/max length constraints (e.g., exactly 4 MCQ options)
- Enum types for Bloom's levels
- Nested validation (topics → bloom groups → questions)

### 2. **instructions.py** - Prompt Engineering
Centralized repository of all LLM prompts.

**Prompts:**
- `QUESTION_GENERATION_SYSTEM_PROMPT` - Comprehensive question generation instructions
- `VERIFICATION_SYSTEM_PROMPT` - Quality criteria and issue detection
- `VARIATION_SYSTEM_PROMPT` - Variation generation strategies

**Design Principles:**
- Detailed Bloom's taxonomy explanations
- Quality standards for each question type
- Common pitfalls and how to avoid them
- Examples for clarity
- Strict formatting requirements

### 3. **llm_call.py** - LLM Integration
Robust API client with schema validation and error handling.

**Features:**
- `generate_structured()` - Returns validated Pydantic models
- `generate_json()` - Returns raw JSON for simple responses
- Automatic JSON cleanup (removes markdown, control chars)
- Retry logic with exponential backoff
- Gemini's `response_mime_type="application/json"` for guaranteed JSON
- Singleton pattern for efficient resource usage

**Error Handling:**
- 3 retry attempts by default
- Graceful degradation on failure
- Detailed error logging
- Clean error messages

### 4. **utils.py** - Utilities
Helper functions for file I/O and data management.

**Functions:**
- `save_json()` - Save Pydantic models or dicts
- `load_json()` - Load and parse JSON
- `save_backup_txt()` - Timestamped safety backups
- `get_chapter_info()` - Extract metadata from paths
- `read_topics_file()` - Parse topics.json

**Path Handling:**
- Supports both CBSE and Sample folder structures
- Extracts class, subject, chapter from path
- Creates backup directories automatically

### 5. **verify.py** - Quality Assurance
Multi-level verification of generated questions.

**Verification Checks:**
- Duplicate detection (exact and near-matches)
- Clarity and ambiguity analysis
- Answer correctness validation
- Bloom's taxonomy alignment
- Grammar and formatting
- Educational quality assessment

**Output:**
- `verification_report.json` with detailed issues
- Issue severity levels (Critical, High, Medium, Low)
- Suggestions for improvement
- Overall quality rating per topic

### 6. **variate.py** - Question Variation
Generates diverse variations while maintaining quality.

**Variation Strategy:**
- 5 variations per question
- Maintains concept and difficulty
- Different wording and context
- Type-specific variation (MCQ options vary, fill-blank context varies)

**Rate Limiting:**
- 0.5s delay between questions
- Prevents API throttling
- ~600 variations per topic (120 questions × 5)

### 7. **main.py** - Pipeline Orchestrator
Main entry point coordinating all stages.

**Workflow:**
```
Input: topics.json
  ↓
[Stage 1] Generate 120 questions per topic
  ↓
Save: questions.json + backup
  ↓
[Stage 2] Verify quality and detect issues
  ↓
Save: verification_report.json + backup
  ↓
[Stage 3] Generate 5 variations per question
  ↓
Save: final questions.json + backup
  ↓
Output: Complete question bank with variations
```

**Features:**
- Automatic chapter discovery
- Skip already processed chapters
- Progress tracking
- Summary statistics
- Comprehensive error handling

## Data Flow

```
┌─────────────┐
│ topics.json │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│  Question Generation    │
│  (120 q's per topic)    │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────┐
│  questions.json     │ ──► Backup (generated)
│  (initial)          │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────────┐
│   Verification          │
│   (quality checks)      │
└──────┬──────────────────┘
       │
       ▼
┌──────────────────────────┐
│ verification_report.json │ ──► Backup (verified)
└──────┬───────────────────┘
       │
       ▼
┌─────────────────────────┐
│   Variation             │
│   (5 per question)      │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────┐
│  questions.json     │ ──► Backup (varied)
│  (with variations)  │
└─────────────────────┘
```

## Technology Stack

- **Language**: Python 3.8+
- **LLM**: Google Gemini 2.0 Flash
- **Validation**: Pydantic v2
- **API**: google-generativeai
- **Config**: python-dotenv

## Design Patterns

### 1. Pipeline Pattern
Sequential stages with clear inputs/outputs:
- Generate → Verify → Variate
- Each stage can run independently
- Failures in later stages don't lose earlier work

### 2. Repository Pattern
Centralized prompt management in `instructions.py`:
- Single source of truth for prompts
- Easy updates and versioning
- Consistent across all modules

### 3. Singleton Pattern
Single LLM client instance:
- Efficient resource usage
- Shared configuration
- No redundant API connections

### 4. Factory Pattern
`get_llm_client()` creates/returns client:
- Lazy initialization
- Testability
- Easy mocking

## Error Handling Strategy

### Level 1: API Retries
- 3 attempts per LLM call
- Exponential backoff
- Different temperatures on retry

### Level 2: Stage Isolation
- Verification failure → continue to variation
- Variation failure → save without variations
- Partial success is acceptable

### Level 3: Graceful Degradation
- Missing variations → empty array
- Failed topic → log and continue
- Invalid JSON → retry with cleanup

### Level 4: Safety Backups
- Backup at each stage
- Timestamped for recovery
- Plain text for debugging

## Security Considerations

### API Key Management
- Environment variables only
- Never hardcoded
- .env file support
- .gitignore protection

### Data Privacy
- No PII in prompts
- Educational content only
- Local storage
- No data persistence in API

### Input Validation
- Pydantic schema validation
- Path traversal prevention
- File existence checks
- Sanitized file operations

## Performance Optimization

### API Efficiency
- JSON mode for guaranteed valid responses
- Batch processing where possible
- Rate limiting to prevent throttling
- Singleton client for connection reuse

### Memory Management
- Stream processing for large files
- Pydantic for memory-efficient validation
- Cleanup of intermediate data
- No global state accumulation

### Time Optimization
- Parallel topic processing (where safe)
- Skip already processed chapters
- Early failure detection
- Progress indicators

## Scalability

### Horizontal Scaling
- Process multiple folders in parallel
- Independent chapter processing
- No shared state between chapters
- Idempotent operations

### Vertical Scaling
- Memory-efficient data structures
- Stream processing support
- Configurable batch sizes
- Resource monitoring

## Testing Strategy

### Unit Tests
- Model validation
- Prompt formatting
- JSON parsing
- Path extraction

### Integration Tests
- LLM call mocking
- Pipeline stages
- File I/O operations
- Error scenarios

### End-to-End Tests
- Full pipeline run
- Verification accuracy
- Variation quality
- Backup integrity

## Monitoring & Logging

### Logging Levels
- INFO: Progress and milestones
- WARNING: Verification issues
- ERROR: Failures and retries
- DEBUG: Detailed API responses

### Metrics
- Questions generated
- Verification pass rate
- Average quality score
- Processing time per topic
- API usage and costs

## Future Enhancements

### Planned Features
1. Parallel topic processing
2. Question difficulty scoring
3. Adaptive retry strategies
4. Question bank analytics
5. Export to various formats (PDF, DOCX, etc.)

### Optimization Opportunities
1. Caching of common patterns
2. Batch API calls
3. Incremental verification
4. Delta updates for variations
5. Compressed backups

## Dependencies

### Required
- `google-generativeai>=0.3.0` - Gemini API
- `pydantic>=2.0.0` - Data validation
- `python-dotenv` - Environment config

### Optional
- `pytest` - Testing framework
- `black` - Code formatting
- `mypy` - Type checking
- `ruff` - Linting

## Version History

**v1.0.0** - Initial Release
- Three-stage pipeline (Generate, Verify, Variate)
- Pydantic model validation
- Comprehensive prompts
- Backup system
- Multi-folder support
