"""Bantuan Checker – FastAPI application.

All scheme logic lives in rules.json and engine.py.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from engine import check_eligibility

BASE_DIR = Path(__file__).parent
RULES_PATH = BASE_DIR / "rules.json"

app = FastAPI(title="Bantuan Checker", version="0.2.0")


# ---------- Models ----------
class Applicant(BaseModel):
    age: int = Field(..., ge=0, le=120)
    state: str = "Selangor"
    household_income: float = Field(..., ge=0, description="Monthly household income in RM")
    household_size: int = Field(1, ge=1)
    children_under_18: int = Field(0, ge=0)
    marital_status: str = Field("single", pattern="^(single|married|widowed|divorced)$")
    occupation: str = Field("working", pattern="^(student|working|unemployed|retired)$")
    religion: Optional[str] = None
    has_ptptn: bool = False


class SchemeResult(BaseModel):
    id: str
    name: str
    agency: str
    summary: str
    benefit: str
    url: str
    documents: list[str]


class CheckSchemeResult(SchemeResult):
    reason: str


class CheckResponse(BaseModel):
    likely: list[SchemeResult]
    check: list[CheckSchemeResult]
    disclaimer: str


# ---------- Rules loader ----------
def load_rules() -> dict[str, Any]:
    with RULES_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------- API ----------
@app.post("/api/check", response_model=CheckResponse)
def check(applicant: Applicant) -> CheckResponse:
    rules = load_rules()
    result = check_eligibility(applicant.model_dump(), rules)
    return CheckResponse(
        likely=result["likely"],
        check=result["check"],
        disclaimer=rules["disclaimer"],
    )


@app.get("/api/schemes")
def schemes() -> dict[str, Any]:
    rules = load_rules()
    return {
        "version": rules["version"],
        "schemes": [
            {k: s[k] for k in ("id", "name", "agency", "summary", "benefit", "url")}
            for s in rules["schemes"]
        ],
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
