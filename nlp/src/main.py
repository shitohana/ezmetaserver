from __future__ import annotations
import os
import sys

sys.path.insert(0, os.environ.get('APP_DIR', ''))

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import yaml
from fastapi import FastAPI, HTTPException
import uvicorn

from hugface import HugFace_Model, ModelType

class TextEntry(BaseModel):
    id: str
    text: str


class ProcessRequest(BaseModel):
    entries: List[TextEntry]
    model_type: str = Field("aioner", description="Model type to use for processing")


class ProcessResult(BaseModel):
    id: str
    result: Dict[str, List[str]]


class ProcessResponse(BaseModel):
    results: List[ProcessResult]

def init_aioner_model():
    config_path = os.environ.get('CONFIG_FILE')
    if not config_path:
        raise ValueError("CONFIG_FILE environment variable not set")

    with open(config_path) as file:
        config = yaml.safe_load(file)

    model = HugFace_Model(
        checkpoint_path=config["models"]["aioner"]["checkpoint"],
        lowercase=config["models"]["aioner"]["lowercase"],
        model_type=ModelType(config["models"]["aioner"]["model_type"])
    )
    model.load_model(config["models"]["aioner"]["path"])
    return model

app = FastAPI(
    title="EzMetaNLP Processing API",
    description="API for processing text with NLP models",
    version="1.0.0",
    root_path="/api/v1/nlp"
)

AIONER_MODEL = None

@app.on_event("startup")
async def startup_event():
    global AIONER_MODEL
    AIONER_MODEL = init_aioner_model()

@app.post("/process", response_model=ProcessResponse)
async def process_text(request: ProcessRequest):
    """
    Process text with the NLP model

    This endpoint accepts a list of text entries and returns the processed results
    """
    if not AIONER_MODEL:
        raise HTTPException(
            status_code=503,
            detail="Model not initialized. Please try again later."
        )

    response = []
    for entry in request.entries:
        processed = AIONER_MODEL.process_text(entry.text)
        print(processed)
        assembled = AIONER_MODEL.assemble_output(processed)
        print(assembled)
        response.append(ProcessResult(id=entry.id, result=assembled))

    return ProcessResponse(results=response)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "NLP service is running", "python_version": sys.version}
