from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database import engine, Base
from backend.api import (
    testcase, task, dashboard, generator,
    project, environment, variable,
    suite, webhook, schedule, debug, account, auth
)
import os

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Auto Test Platform API",
    description="API for managing test cases and execution tasks",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(testcase.router)
app.include_router(task.router)
app.include_router(dashboard.router)
app.include_router(generator.router)
app.include_router(project.router)
app.include_router(environment.router)
app.include_router(variable.router)
app.include_router(suite.router)
app.include_router(webhook.router)
app.include_router(schedule.router)
app.include_router(debug.router)
app.include_router(account.router)
app.include_router(auth.router)

# Mount static files for reports
reports_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports", "allure-report")
os.makedirs(reports_dir, exist_ok=True)
app.mount("/reports", StaticFiles(directory=reports_dir), name="reports")


@app.get("/")
def read_root():
    return {"message": "Welcome to Auto Test Platform API"}
