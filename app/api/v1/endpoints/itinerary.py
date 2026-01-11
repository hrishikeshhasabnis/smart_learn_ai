from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

from app.core.config import settings
from app.schemas.itinerary import Itinerary
from app.services.openai_itinerary_agent import generate_itinerary
from app.services.postprocess import enforce_constraints

router = APIRouter()

class ItineraryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept: str = Field(..., min_length=3, max_length=120)
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    days: int = Field(default=7, ge=1, le=14)
    hours_per_day: int = Field(default=2, ge=1, le=6)
    prefer_format: Literal["videos", "blogs", "mix"] = "mix"
    free_only: bool = True

@router.post("/itinerary", response_model=Itinerary)
def create_itinerary(req: ItineraryRequest):
    try:
        plan = generate_itinerary(
            concept=req.concept,
            level=req.level,
            days=req.days,
            hours_per_day=req.hours_per_day,
            prefer_format=req.prefer_format,
            free_only=req.free_only,
            max_links_per_day=settings.max_links_per_day,
            max_total_links=settings.max_total_links,
        )
        plan = enforce_constraints(
            plan,
            max_links_per_day=settings.max_links_per_day,
            max_total_links=settings.max_total_links,
            free_only=req.free_only,
        )
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
