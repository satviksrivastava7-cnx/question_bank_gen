# Question Generation Pipeline

A comprehensive, production-grade pipeline for generating, verifying, and varying educational questions using AI.

## 🏗️ Architecture

```
app/
├── __init__.py          # Package initialization
├── main.py             # Main pipeline orchestrator
├── models.py           # Pydantic models for strict validation
├── instructions.py     # All LLM prompts and instructions
├── llm_call.py         # LLM API client with JSON schema validation
├── utils.py            # Utility functions (file I/O, backups)
├── verify.py           # Question quality verification
└── variate.py          # Question variation generation
```

## 🔄 Pipeline Workflow

### Stage 1: Question Generation
1. Reads `syllabus.json` from subject directory to get topics
2. Reads `chapter_content.json` from chapter directory for content
3. For each topic, generates:
   - 4 question types (MCQ, Fill Blank, Short Answer, Long Answer)
   - 6 Bloom's levels (Remember, Understand, Apply, Analyze, Evaluate, Create)
   - **5-8 questions per level** if 5+ topics (default: 5)
   - **8-12 questions per level** if < 5 topics (default: 8)
4. Saves to `questions.json`
5. Creates backup in `backups/` folder

### Stage 2: Verification
1. Analyzes all generated questions
2. Checks for:
   - Duplicate questions
   - Clarity and ambiguity
   - Correct answers
   - Bloom's taxonomy alignment
   - Grammar and formatting
3. Saves `verification_report.json`
4. Creates verified backup

### Stage 3: Variation
1. For each question, generates 5 variations
2. Variations maintain:
   - Same concept
   - Same difficulty level
   - Same Bloom's level
   - Different wording/context
3. Saves final `questions.json` with variations
4. Creates final backup

## 📊 Data Models

### Question Types

**MCQ:**
```python
{
  "question": "What is...?",
  "options": ["A", "B", "C", "D"],
  "answer": "B",
  "explanation": "Because...",
  "variations": ["Variation 1", "Variation 2", ...]
}
```

**Fill in the Blank:**
```python
{
  "question": "The Earth revolves around the _____.",
  "answer": "Sun",
  "variations": [...]
}
```

**Short Answer:**
```python
{
  "question": "Explain photosynthesis.",
  "reference_answer": "2-4 sentence answer...",
  "variations": [...]
}
```

**Long Answer:**
```python
{
  "question": "Describe the water cycle in detail.",
  "reference_answer": "5-8 sentence comprehensive answer...",
  "variations": [...]
}
```

## 🚀 Usage

### Process entire folder:
```bash
python -m app.main /path/to/CBSE
```

### Process specific subject:
```bash
python -m app.main /path/to/CBSE/Class10/Medium/Math
```

### Process single chapter:
```bash
python -m app.main /path/to/CBSE/Class10/Medium/Math/chapter1
```

## 📁 Output Structure

```
subject_folder/
├── syllabus.json                # Input (topics extracted here)
└── chapter_folder/
    ├── chapter_content.json     # Input (combined content)
    ├── questions.json           # Generated questions with variations
    ├── verification_report.json # Quality verification report
    └── backups/                 # Timestamped backups
        ├── Class_10_Math_chapter1_generated_20250106_143022.txt
        ├── Class_10_Math_chapter1_verified_20250106_143145.txt
        └── Class_10_Math_chapter1_varied_20250106_144530.txt
```

## 🎯 Features

### Strict Schema Validation
- Uses Pydantic models for type safety
- Gemini's `response_mime_type="application/json"` for guaranteed JSON
- Automatic retry with validation on failure

### Quality Assurance
- Duplicate detection across all questions
- Bloom's taxonomy alignment verification
- Grammar and clarity checks
- Answer correctness validation

### Robust Error Handling
- Automatic retries on API failures
- Graceful degradation (skips variations if generation fails)
- Comprehensive logging
- Timestamped backups at each stage

### Scalability
- Processes entire curriculum trees
- Skip already processed chapters
- Rate limiting to respect API limits
- Progress tracking with detailed logging

## 🔧 Configuration

### Environment Variables
```bash
export GEMINI_API_KEY='your-api-key-here'
```

### Model Configuration
Default: `gemini-2.0-flash-exp`

Change in `llm_call.py`:
```python
LLMClient(model_name="gemini-2.0-flash-exp")
```

### Temperature Settings
- Question Generation: 0.7 (balanced creativity)
- Verification: 0.3 (consistent analysis)
- Variation: 0.8 (high diversity)

## 📝 Prompts

All prompts are centralized in `instructions.py`:

- `QUESTION_GENERATION_SYSTEM_PROMPT` - Detailed instructions for question creation
- `VERIFICATION_SYSTEM_PROMPT` - Quality verification criteria
- `VARIATION_SYSTEM_PROMPT` - Variation generation guidelines

Each prompt includes:
- Comprehensive instructions
- Examples
- Quality standards
- Common pitfalls to avoid

## 🔍 Verification Criteria

### Issue Types
- **Duplicate**: Identical or near-identical questions
- **Unclear**: Ambiguous or confusing wording
- **Incorrect**: Wrong answers or explanations
- **Poor Quality**: Low educational value
- **Grammatical**: Language errors

### Severity Levels
- **Critical**: Unusable (wrong answer, duplicate)
- **High**: Major quality impact (unclear, misaligned)
- **Medium**: Minor issues (grammar, formatting)
- **Low**: Cosmetic improvements

## 📈 Output Statistics

**For chapters with 5+ topics (5 questions/level):**
- **Per topic**: 120 base questions
- **With variations**: 720 total items per topic (120 + 600 variations)
- **Example**: 5 topics = 3,600 total question items

**For chapters with < 5 topics (8 questions/level):**
- **Per topic**: 192 base questions
- **With variations**: 1,152 total items per topic (192 + 960 variations)
- **Example**: 3 topics = 3,456 total question items

## 🛡️ Safety Features

### Backups
- Automatic timestamped backups at each stage
- Plain text format for easy recovery
- Includes metadata (class, subject, chapter, timestamp)

### Validation
- Pydantic ensures correct data structure
- JSON schema validation via Gemini
- Multi-level verification (schema → content → quality)

### Error Recovery
- Failed questions don't block chapter
- Partial results are saved
- Detailed error logging for debugging

## 🎓 Bloom's Taxonomy Coverage

Each question type covers all 6 levels:

1. **Remember**: Recall facts
2. **Understand**: Explain concepts
3. **Apply**: Use in new situations
4. **Analyze**: Make connections
5. **Evaluate**: Justify decisions
6. **Create**: Produce original work

## 💡 Best Practices

1. **Always run verification** - Don't skip Stage 2
2. **Review verification reports** - Check for patterns in issues
3. **Keep backups** - Don't delete backup folder
4. **Monitor API usage** - Check rate limits and costs
5. **Validate topics first** - Ensure topics.json is accurate

## 🐛 Troubleshooting

### "GEMINI_API_KEY not found"
```bash
export GEMINI_API_KEY='your-key'
# Or add to .env file
```

### "No topics found"
Ensure `syllabus.json` exists in subject folder with format:
```json
{
  "Subject": "Math",
  "Chapters": [
    {
      "Chapter": "chapter 1",
      "Title": "Introduction to Algebra",
      "Topics": ["1.1 Variables", "1.2 Expressions", "1.3 Equations"]
    }
  ]
}
```

### Validation Errors
Check `verification_report.json` for specific issues.
Common fixes:
- Regenerate questions for poor quality topics
- Manual review for critical issues
- Adjust temperature for better results

## 📊 Performance

Approximate processing time per topic:
- Generation: ~30-60 seconds
- Verification: ~20-30 seconds
- Variation (120 questions × 5): ~10-15 minutes

Total per topic: ~15-20 minutes
Total per chapter (5 topics): ~1.5-2 hours

## 🔒 Data Privacy

- All processing is local
- API calls only send educational content
- No PII or sensitive data transmitted
- Backups stored locally only
