# Adaptive Learning Platform

An AI-powered adaptive learning platform that generates personalized questions, tracks performance, and creates custom video content using React, FastAPI, LangChain, and Mistral AI.

## Features

- 🎯 **Adaptive Questions**: AI-generated multiple-choice questions that adapt to your skill level
- 📊 **Performance Tracking**: Real-time tracking across topics, subtopics, and concepts
- 💬 **AI Tutor Chat**: Ask follow-up questions and get instant explanations
- 🎥 **Personalized Videos**: AI-generated video content for concepts you struggle with
- 🏆 **Gamification**: Trophy score system to motivate learning

## Architecture

```
coursework_1/
├── backend/             # FastAPI backend
│   └── api/            # API routes and endpoints
├── frontend/            # React frontend
│   └── src/            # React components and pages
├── src/                 # Shared Python code
│   ├── models/          # Pydantic data models
│   ├── services/        # Business logic
│   │   ├── llm/        # Mistral & LangChain integration
│   │   ├── question/   # Question generation & adaptation
│   │   ├── tracking/   # Performance tracking
│   │   └── video/      # Video generation pipeline
│   └── utils/          # Utilities
├── tests/               # Pytest & DeepEval tests
└── data/                # Course material JSON
```

## Setup

### Prerequisites

- Python 3.11+
- UV package manager
- Mistral API key
- (Optional) ElevenLabs API key for TTS
- (Optional) FFmpeg for video generation

### Installation

1. Install UV if not already installed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone and navigate to the project:
```bash
cd coursework_1
```

3. Install dependencies:
   ```bash
   uv sync
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```
   
   Required:
   - `MISTRAL_API_KEY`: Your Mistral AI API key
   
   Optional:
   - `ELEVENLABS_API_KEY`: Your ElevenLabs API key (for video generation)

## Usage

### Run the Application

**Backend (FastAPI):**
```bash
cd backend
uv run uvicorn api.main:app --reload --port 8000
```

**Frontend (React):**
```bash
cd frontend
npm install
npm run dev
```

The backend will be available at `http://localhost:8000`  
The frontend will be available at `http://localhost:5173`

**Or use the deployment script:**
```bash
./deploy.sh
```

### Run Tests

Run all tests:
```bash
uv run pytest
```

Run only unit tests:
```bash
uv run pytest tests/unit/
```

Run LLM quality tests (requires API calls):
```bash
uv run pytest tests/llm/ --run-all
```

## Course Material

The platform uses a JSON file for course content. The default course covers Python programming basics. To use your own course material:

1. Create a JSON file following this structure:
```json
{
  "title": "Course Title",
  "description": "Course description",
  "topics": [
    {
      "name": "Topic Name",
      "description": "Topic description",
      "subtopics": [
        {
          "name": "Subtopic Name",
          "description": "Subtopic description",
          "concepts": [
            {
              "name": "Concept Name",
              "description": "Concept description",
              "keywords": ["keyword1", "keyword2"]
            }
          ],
          "content": "Additional content for context"
        }
      ]
    }
  ]
}
```

2. Place it in `data/course_material.json`

## How It Works

### Adaptive Learning Algorithm

1. **Initial Questions**: Start with medium difficulty
2. **Performance Tracking**: Track accuracy per concept
3. **Adaptive Selection**: 
   - 40% focus on weak areas (< 60% accuracy)
   - 40% priority concepts from analytics
   - 20% new/untried concepts
4. **Difficulty Adjustment**:
   - High accuracy (>80%) → increase difficulty
   - Low accuracy (<60%) → decrease difficulty
5. **Feedback Loop**: Continuous adaptation based on performance

### Video Generation Pipeline

1. Identify weak concepts from performance data
2. Generate educational script using Mistral AI
3. Convert script to speech (TTS)
4. Combine audio with static images using FFmpeg
5. Recommend based on relevance to learning needs

## Technology Stack

- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI + Python
- **LLM**: Mistral AI via LangChain
- **Embeddings**: Mistral Embeddings (cosine similarity)
- **TTS**: ElevenLabs API
- **Video**: FFmpeg
- **Testing**: Pytest, DeepEval
- **Package Manager**: UV (Python), npm (Node.js)

## Configuration

Edit `src/utils/config.py` to customize:

- Model parameters (temperature, max tokens)
- Video settings (resolution, codec)
- Question generation settings
- API endpoints

## Development

### Project Structure

- **Models**: Pydantic models for type safety and validation
- **Services**: Separated business logic by domain
- **Backend API**: FastAPI routes exposing service logic
- **Frontend**: React components and pages
- **Tests**: Comprehensive unit and LLM quality tests

### Adding New Features

1. Define models in `src/models/`
2. Implement service logic in `src/services/`
3. Create API routes in `backend/api/routes/`
4. Create React components in `frontend/src/components/`
5. Add tests in `tests/`

## Known Limitations (POC)

- Session-based storage (progress resets on refresh)
- Video generation requires external API keys
- Limited to course material provided in JSON
- No user authentication/multi-user support

## Future Enhancements

- Persistent storage (database)
- User authentication
- Multi-modal content (interactive exercises)
- Advanced analytics dashboard
- Mobile app support

## License

MIT

## Contact

For questions or issues, please open a GitHub issue.
