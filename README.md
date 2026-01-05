# Todo Full-Stack Application - Backend

A FastAPI backend for the Todo application.

## Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the server
uvicorn src.main:app --reload
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── src/
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── api/          # API endpoints
│   ├── services/     # Business logic
│   └── main.py       # FastAPI app
├── tests/
├── alembic/          # Database migrations
├── requirements.txt
└── .env
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `DATABASE_URL`: SQLite database URL (e.g., sqlite:///./todos.db)
- `API_V1_PREFIX`: API prefix (default: /api/v1)
- `DEBUG`: Enable debug mode (default: true)
