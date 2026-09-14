import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from src.service.ask import handle_ask
from src.service.actions import handle_actions

app = FastAPI(title="ACPL Sales Assistant")


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    status: str
    evidence: list[dict]
    cost_usd: float
    latency_ms: float


class ActionItem(BaseModel):
    finding: str
    rule_id: str
    action: str
    state: str


class ActionsRequest(BaseModel):
    scope: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest):
    result = handle_ask(body.question)
    return AskResponse(**result)


@app.post("/actions", response_model=list[ActionItem])
def actions(body: ActionsRequest):
    return handle_actions(body.scope)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("src.service.main:app", host="0.0.0.0", port=port)