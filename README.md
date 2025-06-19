# FastAPI Simple App

A clean, layered template built with **FastAPI + PostgreSQL + SQLAlchemy + Alembic**, featuring:

- **app/entities/**: SQLAlchemy ORM models
- **app/dtos/**: Pydantic request/response schemas
- **app/repositories/**: Database CRUD operations
- **app/services/**: Business logic layer
- **app/routers/**: API route definitions
- **app/database.py**: Database connection & Base metadata
- **alembic/**: Migration configuration
- **app/main.py**: FastAPI entrypoint with Swagger

## Project Structure

```
fastapi-simple-app/
├── alembic/                # Alembic migration scripts
├── app/
│   ├── entities/
│   │   └── user_entity.py
│   ├── dtos/
│   │   └── user_dto.py
│   ├── repositories/
│   │   └── user_repository.py
│   ├── services/
│   │   └── user_service.py
│   ├── routers/
│   │   └── user_router.py
│   ├── database.py
│   └── main.py
├── .env                    # Environment variables (DATABASE_URL)
├── requirements.txt
└── README.md
```

## Quick Start

```bash
# 1. Clone the repo
git clone
cd fastapi-simple-app

# 2. Create & activate a virtual environment
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure database
# Edit .env:
# DATABASE_URL=postgresql://user:password@localhost:5432/your_db

# 5. Run migrations
alembic upgrade head

# 6. Start development server
uvicorn app.main:app --reload
```

Open your browser to

```
http://localhost:8000/docs
```

to explore the Swagger UI.
