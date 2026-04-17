from typing import Any, Literal

from pydantic import BaseModel, Field

NetworkTab = Literal["recommend", "nearby", "latest"]
NetworkScene = Literal["discover"]
NetworkEventType = Literal["click_card", "apply_friend", "chat_start", "dismiss", "block"]


class NetworkRecommendationItem(BaseModel):
    user_id: str
    nickname: str
    avatar_url: str
    intro: str | None = None
    industry_label: str | None = None
    city_name: str | None = None
    company_name: str | None = None
    job_title: str | None = None
    circle_names: list[str] = Field(default_factory=list)
    is_verified: bool = False
    active_text: str = "recently active"
    reason_tags: list[str] = Field(default_factory=list)
    reason_detail: dict[str, Any] = Field(default_factory=dict)
    score: float = 0


class NetworkRecommendationListData(BaseModel):
    request_id: str
    items: list[NetworkRecommendationItem] = Field(default_factory=list)
    next_cursor: str | None = None
    has_more: bool = False


class NetworkFilterOptionsData(BaseModel):
    cities: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)


class NetworkImpressionsBatchRequest(BaseModel):
    request_id: str | None = Field(default=None, max_length=64)
    scene: NetworkScene = "discover"
    tab: NetworkTab = "recommend"
    target_user_ids: list[str] = Field(default_factory=list, max_length=100)


class NetworkFeedbackRequest(BaseModel):
    request_id: str | None = Field(default=None, max_length=64)
    scene: NetworkScene = "discover"
    tab: NetworkTab = "recommend"
    target_user_id: str = Field(..., min_length=8, max_length=8)
    event_type: NetworkEventType
    ext: dict[str, Any] | None = None
