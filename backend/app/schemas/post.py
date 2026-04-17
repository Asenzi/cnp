from typing import Literal

from pydantic import BaseModel, Field, field_validator

PostMode = Literal["cooperate", "resource", "venue"]
PostSort = Literal["latest", "popular"]


class ResourcePostCreateRequest(BaseModel):
    mode: PostMode = "cooperate"
    title: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=5, max_length=5000)
    industry_label: str | None = Field(default=None, max_length=64)
    images: list[str] = Field(default_factory=list, max_length=9)
    sync_circle_codes: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("images", mode="before")
    @classmethod
    def normalize_images(cls, value):  # noqa: ANN206
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("images must be list")
        normalized: list[str] = []
        for item in value:
            text = str(item or "").strip()
            if not text:
                continue
            normalized.append(text[:255])
        return normalized[:9]

    @field_validator("sync_circle_codes", mode="before")
    @classmethod
    def normalize_sync_circle_codes(cls, value):  # noqa: ANN206
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("sync_circle_codes must be list")
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            code = str(item or "").strip().upper()
            if not code or code in seen:
                continue
            seen.add(code)
            normalized.append(code[:16])
        return normalized[:5]


class ResourcePostLikePayload(BaseModel):
    liked: bool = True


class ResourcePostStatusPayload(BaseModel):
    status: Literal["active", "offline"] = "active"


class ResourcePostPinPayload(BaseModel):
    pinned: bool = True
