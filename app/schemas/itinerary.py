from typing import List, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator

FreeLabel = Literal["FREE_FULL", "FREE_AUDIT", "FREEMIUM", "PAID", "UNKNOWN"]
ContentType = Literal["blog", "video", "docs", "course", "repo", "other"]

class ItineraryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=3, max_length=200)
    # IMPORTANT: keep as str (avoid JSON schema format="uri")
    url: str = Field(..., min_length=8, max_length=2048)
    content_type: ContentType
    minutes: int = Field(..., ge=10, le=180)
    why: str = Field(..., min_length=10, max_length=300)

    free_label: FreeLabel
    free_evidence: str = Field(..., min_length=5, max_length=240)

    @field_validator("url")
    @classmethod
    def url_must_be_http(cls, v: str) -> str:
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("url must start with http:// or https://")
        return v

class ItineraryDay(BaseModel):
    model_config = ConfigDict(extra="forbid")

    day: int = Field(..., ge=1, le=31)
    objective: str = Field(..., min_length=10, max_length=180)
    items: List[ItineraryItem] = Field(default_factory=list)

class Itinerary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    concept: str = Field(..., min_length=3, max_length=120)
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    days: int = Field(..., ge=1, le=31)

    project: str = Field(..., min_length=10, max_length=220)
    itinerary: List[ItineraryDay]
