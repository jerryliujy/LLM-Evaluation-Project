from fastapi import FastAPI
from .db import database
from . import models  # Import models module
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# 配置CORS
origins = [
    "http://localhost:8080",  # Vue 默认端口
    "http://localhost:5173",  # Vite 默认端口
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routers import (
    raw_questions, 
    raw_answers, 
    expert_answers, 
    data_import, 
    datasets, 
    std_questions, 
    std_answers, 
    tags, 
    overview, 
    auth,
    relationship_records,
    std_qa_management,
    std_qa_manual,
    expert,
    evaluations,
    dataset_versions
)

app.include_router(auth.router)
app.include_router(expert.router)
app.include_router(raw_questions.router)
app.include_router(raw_answers.router)
app.include_router(expert_answers.router)
app.include_router(data_import.router)
app.include_router(datasets.router)
app.include_router(std_questions.router)
app.include_router(std_answers.router)
app.include_router(std_qa_manual.router)
app.include_router(tags.router)
app.include_router(overview.router)
app.include_router(relationship_records.router)
app.include_router(std_qa_management.router)
app.include_router(dataset_versions.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Database PJ API"}