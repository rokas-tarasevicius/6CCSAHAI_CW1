# AI-Powered Adaptive Learning Platform

A comprehensive educational platform that leverages AI to create personalized learning experiences. Upload PDF course materials, generate adaptive quizzes, get instant AI tutoring, and watch customized video content tailored to your learning needs.

## 🎯 Features

### 📚 Course Management
- **PDF Upload & Parsing**: Upload multiple PDF files with drag-and-drop support
- **Intelligent Content Extraction**: Automatically parse PDFs using LlamaCloud/LlamaParse
- **AI-Generated Summaries**: Get concise summaries of uploaded materials
- **Automatic Quiz Generation**: AI creates 5 questions per uploaded PDF
- **Course Library**: Manage and organize all your course materials in one place

### 📝 Interactive Quiz System
- **File-Based Quizzes**: Select specific PDFs to create custom quizzes
- **Multiple Choice Questions**: AI-generated questions with detailed explanations
- **Instant Feedback**: See if your answer is correct immediately
- **Progress Tracking**: Visual progress bar showing quiz completion
- **Auto-Advance**: Automatically moves to next question after 3 seconds
- **Question Shuffling**: Answer options are randomized for each question
- **Flexible Quiz Length**: Limit questions or use all available questions

### 💬 AI Tutor Chatbot
- **Real-Time Help**: Ask questions during quizzes and get instant hints
- **Context-Aware**: Understands the current question and provides relevant guidance
- **Conversational Interface**: Natural language interaction with the AI tutor
- **Smart Hints**: Never reveals answers directly, guides you to discover them

### 🎥 Video Content Generation
- **AI Script Writing**: Automatically generates educational scripts for concepts
- **Text-to-Speech**: Converts scripts to natural-sounding audio (ElevenLabs)
- **Dynamic Subtitles**: Word-by-word highlighting with synchronized timing
- **Video Assembly**: Combines audio, subtitles, and background footage
- **Content Caching**: Efficiently stores generated videos for quick access
- **Random Video Generation**: Discover new learning content

### 👤 User Profile & Progress
- **Rating System**: Track your performance with points (+10 correct, -5 incorrect)
- **Concept Tracking**: Records concepts you struggled with
- **Session Persistence**: Maintains progress during your learning session
- **Performance Analytics**: View your learning journey and weak areas

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11 or higher** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+ and npm** - [Download Node.js](https://nodejs.org/)
- **UV Package Manager** - Fast Python package manager (installation below)
- **FFmpeg** - For video generation (optional, see setup below)

### API Keys Required

1. **Mistral AI API Key** (Required) - For AI question generation and chatbot
   - Sign up at [Mistral AI](https://mistral.ai/)
   - Get your API key from the dashboard

2. **LlamaCloud API Key** (Required) - For PDF parsing
   - Sign up at [LlamaCloud](https://cloud.llamaindex.ai/)
   - Get your API key from the dashboard

3. **ElevenLabs API Key** (Optional) - For text-to-speech in videos
   - Sign up at [ElevenLabs](https://elevenlabs.io/)
   - Get your API key from the dashboard
   - **Note**: Video generation will work without this but won't produce audio

## 🚀 Installation

### Step 1: Install UV Package Manager

UV is a fast Python package and project manager. Install it using one of these methods:

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**With pip:**
```bash
pip install uv
```

After installation, restart your terminal or run:
```bash
source $HOME/.cargo/env  # macOS/Linux
```

Verify installation:
```bash
uv --version
# Should show: uv 0.6.x or higher
```

### Step 2: Clone and Navigate to Project

```bash
cd 6CCSAHAI_CW1
```

### Step 3: Install Python Dependencies

UV will automatically create a virtual environment and install all dependencies:

```bash
uv sync
```

This installs:
- FastAPI & Uvicorn (backend server)
- LangChain & Mistral AI (LLM integration)
- LlamaCloud services (PDF parsing)
- ElevenLabs (text-to-speech)
- FFmpeg-python (video processing)
- Pydantic (data validation)
- Pytest (testing)
- And more...

### Step 4: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

This installs:
- React 18 & React Router
- TypeScript
- Vite (build tool)
- Axios (HTTP client)
- Zustand (state management)
- Vitest (testing)

### Step 5: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
touch .env
```

Add the following environment variables to the `.env` file:

```bash
# ============================================================================
# REQUIRED API KEYS
# ============================================================================

# Mistral AI - Required for AI question generation and chatbot
# Get your key from: https://console.mistral.ai/
MISTRAL_API_KEY=your_mistral_api_key_here

# LlamaCloud - Required for PDF parsing
# Get your key from: https://cloud.llamaindex.ai/
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key_here

# ============================================================================
# OPTIONAL API KEYS & SETTINGS
# ============================================================================

# ElevenLabs - Optional, for text-to-speech in video generation
# Get your key from: https://elevenlabs.io/
# Without this key, videos will be generated without audio
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Session Secret - Optional, for session security
# Default: "your-secret-key-change-in-production"
# Change this in production for security
SESSION_SECRET_KEY=your_secret_session_key_here

# ============================================================================
# OPTIONAL VIDEO GENERATION SETTINGS
# ============================================================================

# Custom ElevenLabs voice ID (optional)
# If not set, uses default voice: "21m00Tcm4TlvDq8ikWAM"
# ELEVENLABS_CUSTOM_VOICE_ID=your_custom_voice_id

# ElevenLabs TTS model (optional)
# Options: eleven_turbo_v2 (default, fastest/cheapest), 
#          eleven_multilingual_v2, eleven_monolingual_v1
# ELEVENLABS_MODEL_ID=eleven_turbo_v2

# Minecraft source video path (optional)
# Default: backend/video_service/assets/minecraft_source.mp4
# MINECRAFT_REEL_SOURCE=/path/to/your/minecraft_video.mp4

# Subtitle settings (optional)
# REEL_SUBTITLE_FONT=DejaVuSans-Bold
# REEL_SUBTITLE_FONT_SIZE=56
# REEL_SUBTITLE_WRAP_CHARS=40
# REEL_SUBTITLE_MARGIN_V=60
# REEL_SUBTITLE_MAX_LINES=5
```

**Important Notes:**
- Replace `your_mistral_api_key_here` with your actual Mistral AI API key
- Replace `your_llama_cloud_api_key_here` with your actual LlamaCloud API key
- Optional keys can be omitted if you don't need those features
- **Never commit the `.env` file to version control** (it's in `.gitignore`)

### Step 6: Install FFmpeg (Optional - For Video Generation)

FFmpeg is required only if you want to generate videos with audio and subtitles.

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
1. Download from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract and add to PATH
3. Or use Chocolatey: `choco install ffmpeg`

Verify installation:
```bash
ffmpeg -version
```

### Step 7: (Optional) Add Minecraft Source Video

If you want to generate videos with background footage:

1. Place your Minecraft gameplay video at:
   ```
   backend/video_service/assets/minecraft_source.mp4
   ```

2. Or set a custom path in `.env`:
   ```bash
   MINECRAFT_REEL_SOURCE=/path/to/your/video.mp4
   ```

3. (Optional) Pre-scale video for faster generation:
   ```bash
   uv run python videos/pre_scaler.py
   ```
   This pre-processes the video to 1280x720, making generation 2-3x faster.

## 🎮 Running the Application

### Option 1: Using the Deployment Script (Recommended)

The deployment script starts both backend and frontend servers automatically:

```bash
chmod +x deploy.sh
./deploy.sh
```

This will:
- Check for required dependencies (UV, npm)
- Start the backend server on `http://localhost:8000`
- Start the frontend server on `http://localhost:5173`
- Display logs to `backend.log` and `frontend.log`
- Keep both servers running until you press Ctrl+C

**Access the application:**
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (interactive Swagger UI)

### Option 2: Running Servers Manually

If you prefer to run servers separately:

**Terminal 1 - Backend:**
```bash
cd backend
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The `--reload` flag enables hot-reloading for development.

## 📖 How to Use

### 1. Upload Course Materials

1. Navigate to the **Courses** page
2. Drag and drop PDF files or click "Browse Files"
3. Select up to 5 PDFs at once
4. Click "Upload Courses"
5. Wait for processing (parsing, summarization, quiz generation)
6. View your uploaded courses in the library

**Processing includes:**
- PDF text extraction using LlamaCloud
- AI-generated summary of content
- 5 quiz questions automatically generated per PDF

### 2. Select Quiz Files

1. On the **Courses** page, you'll see all uploaded PDFs
2. Each PDF shows the number of available quiz questions
3. Click the checkbox icon to select/deselect files for your quiz
4. Use "Select All" / "Deselect All" for bulk selection
5. Selected files appear in the quiz counter

### 3. Take a Quiz

1. Go to the **Home** page (dashboard)
2. Review your selected quiz files and total question count
3. (Optional) Set a question limit to take a shorter quiz
4. Click "Start Selected Quiz"
5. Answer each multiple-choice question
6. Click "Submit Answer" to check if you're correct
7. View instant feedback and explanations
8. Quiz auto-advances to next question after 3 seconds
9. Complete all questions to see your results

**Quiz Features:**
- Visual progress bar
- Real-time feedback on answers
- Detailed explanations for each question
- Rating points: +10 for correct, -5 for incorrect
- Auto-advance or manual next button

### 4. Use AI Tutor During Quiz

1. While taking a quiz, the chatbot panel is available on the right
2. Type your question in the chat input
3. The AI tutor provides hints without revealing the answer
4. It understands the current question context
5. Use it to clarify concepts or get guidance

**Chatbot capabilities:**
- Context-aware responses
- Pedagogical hints (no direct answers)
- Concept explanations
- Real-time interaction with Mistral AI

### 5. Generate and Watch Videos

1. Navigate to the **Videos** page
2. Click "Generate Random Video" to create new content
3. The system will:
   - Select a concept (random or based on weak areas)
   - Generate an educational script using AI
   - Convert script to speech (if ElevenLabs API key is set)
   - Create synchronized subtitles
   - Assemble video with background footage
4. Watch generated videos directly in the browser
5. Videos are cached for future viewing

**Video Generation Requirements:**
- ElevenLabs API key (for audio)
- FFmpeg installed (for video assembly)
- Minecraft source video (for background)

### 6. View Your Profile

1. Go to the **Profile** page
2. See your current rating (starts at 1000)
3. Review concepts you answered incorrectly
4. Use this to identify areas needing more practice



## 🛠️ Technology Stack

### Backend
| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Programming language | 3.11+ |
| **FastAPI** | Web framework | 0.104.0+ |
| **Uvicorn** | ASGI server | 0.24.0+ |
| **LangChain** | LLM orchestration | 0.1.0+ |
| **Mistral AI** | Large language model | mistral-small-latest |
| **LlamaCloud** | PDF parsing service | 0.6.81+ |
| **ElevenLabs** | Text-to-speech | 0.2.0+ |
| **FFmpeg** | Video processing | 7.0+ |
| **Pydantic** | Data validation | 2.0.0+ |
| **Pytest** | Testing framework | 7.4.0+ |
| **UV** | Package manager | 0.6.0+ |

### Frontend
| Technology | Purpose | Version |
|------------|---------|---------|
| **React** | UI framework | 18.2.0 |
| **TypeScript** | Type safety | 5.2.2 |
| **Vite** | Build tool | 5.0.8 |
| **React Router** | Navigation | 6.20.0 |
| **Axios** | HTTP client | 1.6.2 |
| **Zustand** | State management | 4.4.7 |
| **Vitest** | Testing framework | 4.0.8 |

### AI & Machine Learning
- **Mistral AI**: `mistral-small-latest` model for text generation
- **Embeddings**: Mistral embeddings for semantic search
- **Temperature**: 0.7 (balanced creativity)
- **Max Tokens**: 1000 (standard), 800 (questions)

## ⚙️ Configuration

### Backend Configuration

Edit `backend/shared/utils/config.py` to customize:

**LLM Settings:**
```python
MISTRAL_MODEL = "mistral-small-latest"  # Mistral model
TEMPERATURE = 0.7                        # Creativity (0.0-1.0)
MAX_TOKENS = 1000                        # Response length
QUESTION_MAX_TOKENS = 800                # Question length
```

**Quiz Settings:**
```python
QUESTIONS_PER_SESSION = 10   # Questions per session
MIN_ANSWERS = 2              # Minimum answer options
MAX_ANSWERS = 5              # Maximum answer options
QUESTION_CACHE_SIZE = 50     # Cached questions
```

**Video Settings:**
```python
VIDEO_WIDTH = 1280           # Video width (pixels)
VIDEO_HEIGHT = 720           # Video height (pixels)
VIDEO_FPS = 24               # Frames per second
VIDEO_CODEC = "libx264"      # Video codec
REEL_DURATION_TARGET_MIN = 15  # Min duration (seconds)
REEL_DURATION_TARGET_MAX = 60  # Max duration (seconds)
```

### Frontend Configuration

Edit `frontend/src/services/api.ts` to change API endpoints:

```typescript
const API_BASE_URL = 'http://localhost:8000/api'
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "MISTRAL_API_KEY environment variable is required"

**Problem**: Mistral API key is not set or not found.

**Solution**:
```bash
# Ensure .env file exists in project root
cat .env

# Add your API key
echo "MISTRAL_API_KEY=your_key_here" >> .env
```

#### 2. "LLAMA_CLOUD_API_KEY environment variable not set"

**Problem**: LlamaCloud API key is missing.

**Solution**:
```bash
# Add LlamaCloud API key to .env
echo "LLAMA_CLOUD_API_KEY=your_key_here" >> .env
```

#### 3. "UV package manager not found"

**Problem**: UV is not installed or not in PATH.

**Solution**:
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
source $HOME/.cargo/env

# Verify
uv --version
```

#### 4. PDF Upload Fails or Times Out

**Problem**: PDF is too large or parsing is taking too long.

**Solution**:
- Try a smaller PDF (< 50 pages recommended)
- Check your LlamaCloud API quota
- Wait up to 5 minutes for complex PDFs
- Check backend logs: `tail -f backend.log`

#### 5. Video Generation Shows Warning

**Problem**: Video generation requires additional setup.

**Solution**:
```bash
# Install FFmpeg
brew install ffmpeg  # macOS

# Add ElevenLabs API key to .env
echo "ELEVENLABS_API_KEY=your_key_here" >> .env

# Add Minecraft source video
# Place video at: backend/video_service/assets/minecraft_source.mp4
```

#### 6. Quiz Questions Not Appearing

**Problem**: No questions available or quiz not selected.

**Solution**:
1. Go to Courses page
2. Check if PDFs have been processed (shows "Quiz available: X questions")
3. Select quiz files using checkboxes
4. Return to Home page and start quiz

#### 7. Frontend Not Loading / CORS Error

**Problem**: Backend not running or CORS configuration issue.

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# If not running, start backend
cd backend
uv run uvicorn api.main:app --reload --port 8000
```

#### 8. "Module not found" Errors

**Problem**: Dependencies not installed correctly.

**Solution**:
```bash
# Backend
uv sync

# Frontend
cd frontend
npm install
```

#### 9. Rating Not Updating

**Problem**: Session state issue.

**Solution**:
- Refresh the page (rating is session-based)
- Rating changes are immediate during quiz
- Check Profile page to see current rating

#### 10. Videos Not Playing

**Problem**: Video file path or format issue.

**Solution**:
- Check video was generated successfully
- Verify FFmpeg is installed: `ffmpeg -version`
- Check backend logs for video generation errors
- Ensure browser supports MP4 playback


## 📚 API Documentation

Once the backend is running, visit:

**Interactive API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Key Endpoints:**

### Course Management
- `GET /api/course/` - Get all parsed courses
- `POST /api/course/upload` - Upload and parse PDF
- `DELETE /api/course/{file_key}` - Delete a course
- `POST /api/course/generate-quiz/{file_key}` - Regenerate quiz

### Quiz
- `POST /api/questions/start-file-quiz` - Start file-based quiz
- `POST /api/questions/complete` - Submit quiz results

### Chatbot
- `POST /api/chatbot/ask` - Ask the AI tutor a question

### Videos
- `POST /api/videos/generate` - Generate video for concept
- `POST /api/videos/generate-random` - Generate random video
- `GET /api/videos/cached` - List cached videos
- `GET /api/videos/file/{filename}` - Stream video file

### User Profile
- `GET /api/user/profile` - Get user profile
- `PUT /api/user/profile/rating` - Set rating
- `PATCH /api/user/profile/rating` - Update rating
- `POST /api/user/profile/incorrect-concepts` - Record incorrect concepts

---

**Made with ❤️ for adaptive learning**

*Last updated: December 2025*
