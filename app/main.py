from fastapi import FastAPI
from app.routers import auth_router, user_router

# from app.database import Base, engine
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FastAPI with PostgreSQL",
    description="Sample app with clean architecture",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://adnex-bi-fe-809785955233.asia-east1.run.app",
        "https://adnex-bi-fe-dev-809785955233.asia-east1.run.app",
    ],
    # allow_origins=["*"],
    allow_credentials=True,  # Cookie
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,  # cache time(seconds)
)
# Base.metadata.create_all(bind=engine)

Routers = [
    user_router.router,
    auth_router.router,
]

for r in Routers:
    app.include_router(r)


@app.get("/")
def read_root():
    return {"message": "Welcome to Pharmacy API"}
