"""Entry point for the FastAPI application.

Run locally with:
    uvicorn app.main:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI

from .api import router

app = FastAPI(title="AI Health Assistant", version="0.1.0")
app.include_router(router)


@app.get("/")
def root() -> dict:
    return {"message": "AI health assistant backend ready"}
