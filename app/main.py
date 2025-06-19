from fastapi import FastAPI
from app.routers import user_router
from app.database import Base, engine

app = FastAPI(
    title="FastAPI with PostgreSQL",
    description="Sample app with clean architecture",
    version="1.0.0",
)

# Base.metadata.create_all(bind=engine)

app.include_router(user_router.router)


@app.get("/")
def read_root():
    return {"message": "Welcome to Pharmacy API"}
