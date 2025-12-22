from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.routers import (
    auth_router,
    business_module_router,
    org_router,
    role_router,
    si_router,
    user_router,
    permission_router,
)
from starlette.middleware.cors import CORSMiddleware

app = FastAPI(
    title="FastAPI with PostgreSQL",
    description="Sample app with clean architecture",
    version="1.0.0",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add Bearer token security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Set Bearer as default security for all endpoints
    openapi_schema["security"] = [{"Bearer": []}]
    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi

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
    si_router.router,
    org_router.org_router,
    org_router.si_router,
    business_module_router.router,
    role_router.si_router,
    role_router.org_router,
    role_router.role_router,
    permission_router.si_router,
    permission_router.perm_router,
]

for r in Routers:
    app.include_router(r)


@app.get("/")
def read_root():
    return {"message": "Welcome to Pharmacy API"}
