## 🚀 Quick Start Guide - Question Generation Pipeline

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API Key

```bash
export GEMINI_API_KEY='your-gemini-api-key-here'
```

Or create a `.env` file:
```
GEMINI_API_KEY=your-gemini-api-key-here
```

### 3. Ensure Prerequisites

Your chapter folder must have `chapter_content.json` and subject must have `syllabus.json`:

```
Sample/
├── Class 8/
│   └── syllabus.json  ← Must exist at subject level!
│       └── Forces/
│           └── chapter_content.json  ← Must exist!
```

### 4. Run Pipeline

**Process single chapter:**
```bash
python -m app.main "Sample/Class 8/Forces"
```

**Process entire folder:**
```bash
python -m app.main Sample
```

**Process CBSE curriculum:**
```bash
python -m app.main CBSE
```

### 5. Check Output

After completion, your chapter folder will have:

```
Sample/Class 8/Forces/
├── chapter_content.json         ← Input (combined chapter pages)
├── questions.json              ← Generated questions with variations
├── verification_report.json    ← Quality report
└── backups/                    ← Safety backups
```

### 6. Review Results

**Check question count:**
```bash
python -c "import json; data=json.load(open('Sample/Class 8/Forces/questions.json')); print(f'Topics: {data[\"total_topics\"]}')"
```

**Check verification:**
```bash
cat "Sample/Class 8/Forces/verification_report.json"
```

### Expected Output Format

**questions.json:**
```json
{
  "class_name": "Class 8",
  "subject_name": "Forces",
  "chapter_name": "chapter 5",
  "total_topics": 6,
  "topics": [
    {
      "topic": "Introduction to Forces",
      "content": "...",
      "MCQs": [
        {
          "bloom_taxonomy": "remember",
          "questions": [
            {
              "question": "What is force?",
              "options": ["A push or pull", "Energy", "Mass", "Speed"],
              "answer": "A push or pull",
              "explanation": "Force is defined as a push or pull...",
              "variations": [
                "Define force in physics.",
                "What do we call a push or pull?",
                "How is force described?",
                "What is the definition of force?",
                "Explain what force means."
              ]
            },
            ...4 more questions
          ]
        },
        ...5 more Bloom's levels
      ],
      "fill_in_the_blanks": [...],
      "short_answer": [...],
      "long_answer": [...]
    },
    ...more topics
  ]
}
```

### Troubleshooting

**Error: "syllabus.json not found"**
```bash
# Generate syllabus first from subject directory
# Make sure syllabus.json exists at subject level
```

**Error: "chapter_content.json not found"**
```bash
# Combine chapter content first
python combine_content.py
```

**Error: "GEMINI_API_KEY not found"**
```bash
export GEMINI_API_KEY='your-key'
```

**Processing takes too long**
- This is normal! Each topic takes 15-20 minutes
- The pipeline generates 120 questions + 600 variations per topic
- For 5 topics: expect 1.5-2 hours

**Verification shows issues**
- Check `verification_report.json` for details
- Most issues are minor (LOW/MEDIUM severity)
- CRITICAL issues mean questions need regeneration

### Pipeline Stages

1. **Generation** (~5 min/topic)
   - Creates 120 questions per topic
   - Saves `questions.json`

2. **Verification** (~2 min/topic)
   - Checks quality and duplicates
   - Saves `verification_report.json`

3. **Variation** (~15 min/topic)
   - Generates 5 variations per question
   - Updates `questions.json`

Total: ~22 minutes per topic

### What's Generated

**Per topic (for 5+ topics):**
- **MCQs**: 30 questions (6 levels × 5 questions)
- **Fill in Blanks**: 30 questions
- **Short Answer**: 30 questions
- **Long Answer**: 30 questions
- **Total**: 120 questions per topic

**Per topic (for < 5 topics):**
- **MCQs**: 48 questions (6 levels × 8 questions)
- **Fill in Blanks**: 48 questions
- **Short Answer**: 48 questions
- **Long Answer**: 48 questions
- **Total**: 192 questions per topic

With variations:
- **Each question** × **5 variations**
- **Example (5 topics)**: 600 base + 3,000 variations = 3,600 total items

### Tips

✅ **Run during off-hours** - Processing is time-intensive
✅ **Check backups folder** - Contains timestamped safety copies
✅ **Review verification** - Identifies quality issues early
✅ **Monitor API costs** - Track usage in Google Cloud Console
✅ **Keep .env secure** - Don't commit API keys to git

### Next Steps

1. Review generated questions
2. Check verification report
3. Use questions in your application
4. Generate more chapters as needed
