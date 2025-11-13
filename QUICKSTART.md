# Quick Start Guide

## Installation & Setup

1. **Sync dependencies:**
```bash
uv sync
```

2. **Verify setup (optional but recommended):**
```bash
uv run python verify_setup.py
```

You should see: `✅ All checks passed!`

3. **Run the application:**

**Option 1: Use the deployment script (recommended):**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Option 2: Run manually:**

Backend:
```bash
cd backend
uv run uvicorn api.main:app --reload --port 8000
```

Frontend (in a new terminal):
```bash
cd frontend
npm install
npm run dev
```

The backend will be at `http://localhost:8000`  
The frontend will be at `http://localhost:5173`

## Using the Platform

### 1. Home Page (Dashboard)
- View your overall progress and statistics
- See trophy score, accuracy, and mastery level
- Get personalized insights

### 2. Quiz Page
Start answering adaptive questions:
- Questions adjust to your skill level
- Immediate feedback on answers
- Detailed explanations for each question
- AI chat for follow-up questions

**How it works:**
- First few questions are medium difficulty
- System tracks performance per concept
- Weak areas get more practice
- Strong areas increase in difficulty

### 3. Video Feed Page
Watch personalized learning videos:
- Videos recommended based on your weak areas
- AI-generated scripts tailored to concepts you struggle with
- Estimated watch times provided

## Running Tests

Run all unit tests:
```bash
uv run pytest tests/unit/
```

Run specific test file:
```bash
uv run pytest tests/unit/test_models.py -v
```

Run with coverage:
```bash
uv run pytest --cov=src tests/unit/
```

LLM quality tests (requires API calls):
```bash
uv run pytest tests/llm/
```

## Project Structure

```
coursework_1/
├── backend/              # FastAPI backend
│   └── api/            # API routes
├── frontend/            # React frontend
│   └── src/           # React components and pages
├── src/                 # Shared Python code
│   ├── models/          # Data models (Pydantic)
│   ├── services/        # Business logic
│   │   ├── llm/       # Mistral & LangChain
│   │   ├── question/  # Question generation
│   │   ├── tracking/  # Performance tracking
│   │   └── video/     # Video generation
│   └── utils/          # Utilities
├── tests/               # Test suite
│   ├── unit/          # Unit tests
│   └── llm/           # LLM quality tests
└── data/               # Course material
```

## API Keys

Set up your API keys by copying the example file and editing it:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required:
- `MISTRAL_API_KEY`: Your Mistral AI API key

Optional:
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key (for video generation)

## Customizing Course Material

Edit `data/course_material.json` to change the course content:

```json
{
  "title": "Your Course Title",
  "topics": [
    {
      "name": "Topic Name",
      "subtopics": [
        {
          "name": "Subtopic Name",
          "concepts": [
            {
              "name": "Concept",
              "description": "Description",
              "keywords": ["keyword1", "keyword2"]
            }
          ]
        }
      ]
    }
  ]
}
```

## Features at a Glance

✅ **Adaptive Question Generation** - Questions adapt to your level  
✅ **Performance Tracking** - Track progress per topic/subtopic/concept  
✅ **Weak Area Detection** - Identifies concepts needing practice  
✅ **Difficulty Adjustment** - Auto-adjusts based on accuracy  
✅ **AI Explanations** - Get detailed explanations with examples  
✅ **Follow-up Chat** - Ask questions about any concept  
✅ **Video Recommendations** - Personalized video content  
✅ **Trophy System** - Gamification to motivate learning  
✅ **Real-time Insights** - Get suggestions on what to study  

## Troubleshooting

**Question generation seems slow:**
- First question takes longer as it initializes the LLM
- Subsequent questions are faster

**Video generation shows warning:**
- Video generation requires ElevenLabs API key for TTS
- Without API key, you'll see script previews only

**Progress resets on refresh:**
- This is expected (POC uses in-memory storage)
- For persistent storage, would need database integration

## Next Steps

After exploring the platform:
1. Answer 10-15 questions to see adaptive behavior
2. Check the Video Feed for personalized recommendations
3. Experiment with different course materials
4. Review the test suite for implementation details

Enjoy your adaptive learning experience! 🚀

