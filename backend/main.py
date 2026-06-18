import os
from contextlib import asynccontextmanager
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from fraud_patterns import ingest_patterns
from rag_pipeline import analyse

load_dotenv()


class AnalyseRequest(BaseModel):
    message: str


class AnalyseResponse(BaseModel):
    verdict: Literal["FRAUD", "SUSPICIOUS", "LEGITIMATE"]
    confidence: int
    pattern: str
    explanation: str
    recommendation: str
    language: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    ingest_patterns()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyse", response_model=AnalyseResponse)
def analyse_message(request: AnalyseRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    result = analyse(request.message)
    return result
