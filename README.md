# PeachMe - AI-Powered Pitch Analysis Platform

PeachMe is an advanced AI platform that helps users analyze and improve their startup or project pitches. The platform combines speech-to-text capabilities with sophisticated AI analysis to provide structured feedback on pitch presentations.

## Features

- **Video Upload & Transcription**: Upload pitch videos and get accurate transcriptions using OpenAI's Whisper model
- **Structured Pitch Analysis**: Get detailed feedback on key pitch components:
  - Problem Statement
  - Solution Proposal
  - Target Market Analysis
  - Competitive Advantage
  - Business Viability
- **Real-time Chat Interface**: Interact with an AI coach for immediate feedback
- **Conversation Management**: Track and review previous pitch analyses
- **Streaming Responses**: Get real-time AI responses with server-sent events
- **Comprehensive API**: Well-documented REST API for easy integration

## Tech Stack

- **Backend**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **AI/ML**:
  - LangChain for AI orchestration
  - OpenAI GPT-4 for analysis
  - Whisper for speech-to-text
- **Development Tools**:
  - Python 3.8+
  - FFmpeg for audio processing
  - Poetry for dependency management

## Prerequisites

- Python 3.8 or higher
- FFmpeg installed on your system
- OpenAI API key
- LangChain API key (optional, for tracing)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/peachme.git
cd peachme
```

2. Install dependencies:
```bash
pip install -r peachme_fastapi/requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
OPENAI_API_KEY=your_openai_api_key
LANGCHAIN_API_KEY=your_langchain_api_key  # Optional
LANGCHAIN_PROJECT=peachme-chat
LANGCHAIN_TRACING_V2=true
```

## Running the Application

1. Start the FastAPI server:
```bash
cd peachme_fastapi
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

2. Access the API documentation:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## API Endpoints

### Video Analysis

- `POST /api/video/transcribe`: Upload and transcribe a video
  - Optional query parameter: `save_to_conversation=true/false`
  - Returns transcript and optional conversation ID

- `POST /api/video/analyze`: Analyze a transcript
  - Accepts transcript text
  - Returns structured feedback and conversation ID

### Chat Interface

- `POST /api/chat`: Regular chat endpoint
- `POST /api/chat/stream`: Streaming chat responses
- `POST /api/chat/structured`: Structured analysis responses
- `GET /api/conversations/{conversation_id}`: Retrieve conversation history

## Response Format

### Structured Feedback Example

```json
{
    "stated_problem": {
        "score": 4,
        "feedback": "Clear problem statement with good market context..."
    },
    "identified_solution": {
        "score": 4,
        "feedback": "Innovative solution that directly addresses the problem..."
    },
    "target_market": {
        "score": 3,
        "feedback": "Market segment identified but could be more specific..."
    },
    "competitive_advantage": {
        "score": 4,
        "feedback": "Strong differentiation from existing solutions..."
    },
    "viability_sustainability": {
        "score": 3,
        "feedback": "Business model shows promise but needs more detail..."
    },
    "overall_feedback": "Strong pitch with clear problem-solution fit..."
}
```

## Development

### Project Structure

```
peachme_fastapi/
├── app/
│   ├── api/          # API routes
│   ├── core/         # Core functionality
│   ├── db/           # Database models
│   ├── models/       # Pydantic models
│   ├── schemas/      # Data schemas
│   └── services/     # Business logic
├── media/            # Temporary media storage
└── requirements.txt  # Dependencies
```

### Adding New Features

1. Define schemas in `app/schemas/`
2. Add database models in `app/models/`
3. Implement services in `app/services/`
4. Add routes in `app/api/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.
