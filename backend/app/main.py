from fastapi import FastAPI
from .db import database
from . import models  # Import models module
from .routers import *
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

app.include_router(raw_questions.router)
app.include_router(raw_answers.router)
app.include_router(expert_answers.router)
app.include_router(experts.router)
from .routers import data_import, datasets, std_questions, std_answers
app.include_router(data_import.router)
app.include_router(datasets.router)
app.include_router(std_questions.router)
app.include_router(std_answers.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Database PJ API"}