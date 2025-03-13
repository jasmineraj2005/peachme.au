# PeachMe FastAPI Backend

A modern, asynchronous API for the PeachMe chat application built with FastAPI and LangChain.

## Features

- Asynchronous API endpoints for chat functionality
- Integration with OpenAI's GPT models via LangChain
- Conversation and message persistence with SQLAlchemy
- Automatic API documentation with Swagger UI
- LangSmith tracing for monitoring and debugging

## Getting Started

### Prerequisites

- Python 3.9+
- Virtual environment (recommended)

### Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables in `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   LANGCHAIN_API_KEY=your_langchain_api_key
   LANGCHAIN_PROJECT=your_langchain_project
   DATABASE_URL=sqlite:///./peachme.db
   ```

### Running the Application

Run the application with:

```bash
python main.py
```

The API will be available at http://localhost:8000

API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

- `POST /api/chat`: Send a message to the chatbot
- `GET /api/conversations/{conversation_id}`: Get all messages in a conversation

## Project Structure

```
peachme_fastapi/
├── app/
│   ├── api/            # API routes
│   ├── core/           # Core functionality (LangChain integration)
│   ├── db/             # Database configuration
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   └── main.py         # FastAPI application
├── .env                # Environment variables
├── main.py             # Application entry point
└── README.md           # This file
```

## License

MIT 