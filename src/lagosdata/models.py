"""Canonical records shared by every collector and pipeline stage."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Business:
    name: str
    place_id: str = ''
    area: str = ''
    zone: str = ''
    street: str = ''
    addr: str = ''
    lat: float | str = ''
    lng: float | str = ''
    group: str = ''
    sub: str = ''
    legacy18: str = ''
    label: str = ''
    phone: str = ''
    phones_all: str = ''
    whatsapp: str = ''
    website: str = ''
    email: str = ''
    instagram: str = ''
    facebook: str = ''
    twitter: str = ''
    linkedin: str = ''
    tiktok: str = ''
    contact_channels: int = 0
    rating: float | str = ''
    reviews: int | str = ''
    additional_info: dict[str, Any] = field(default_factory=dict)
    delivery_text_signals: list[str] = field(default_factory=list)
    priority: str = ''
    package: str = ''
    contactable: str = ''
    verification: str = ''
    sales_status: str = 'Not Contacted'
    notes: str = ''
    score: float | str = ''
    band: str = ''
    score_components: dict[str, Any] = field(default_factory=dict)
    score_basis: str = ''
    delivery_category: str = ''
    source: str = ''
    sources_all: list[str] = field(default_factory=list)
    maps: str = ''
    added: str = ''
    conflicts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Business":
        fields = cls.__dataclass_fields__
        return cls(**{key: item for key, item in value.items() if key in fields})
