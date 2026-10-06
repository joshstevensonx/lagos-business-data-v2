"""Strict YAML configuration validation."""
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class SourceOptions(StrictModel):
    enabled: bool = True
    concurrency: int = 3
    zoom: int = 14
    via_browser: bool = False
    bbox_pad_km: float = 2.0
    max_searches: int | None = None
    max_runtime_minutes: int | None = None
    delay_seconds: tuple[float, float] = (2, 6)
    sites: list[str] = Field(default_factory=list)
    rate_per_second: float = 1.0
    contact_email: str = 'ops@example.invalid'
    max_sites: int = 0
    monthly_ceiling_pct: int = 80
    skus: list[str] = Field(default_factory=lambda: ['essentials'])

    @field_validator('concurrency')
    @classmethod
    def concurrency_limit(cls, value):
        if not 1 <= value <= 6: raise ValueError('concurrency must be between 1 and 6')
        return value


class Sources(StrictModel):
    places_api: SourceOptions = Field(default_factory=lambda: SourceOptions(enabled=False))
    osm: SourceOptions = Field(default_factory=SourceOptions)
    gmaps_browser: SourceOptions = Field(default_factory=SourceOptions)
    directories: SourceOptions = Field(default_factory=SourceOptions)
    site_contacts: SourceOptions = Field(default_factory=SourceOptions)


class TaxonomyOptions(StrictModel):
    mode: Literal['full_tree','subset'] = 'full_tree'
    terms: list[str] | None = None


class Bands(StrictModel):
    hot: int = 60
    warm: int = 40
    cool: int = 25


class DeliveryScoring(StrictModel):
    enabled: bool = True
    bands: Bands = Field(default_factory=Bands)
    keep_all: bool = True


class PlacePages(StrictModel):
    enabled: bool = False
    max_place_visits: int = 500
    order_by: Literal['reviews_desc'] = 'reviews_desc'


class Enrich(StrictModel):
    place_pages: PlacePages = Field(default_factory=PlacePages)


class Output(StrictModel):
    dir: str = 'out/'
    workbook: str = ''


class RunConfig(StrictModel):
    pipeline: Literal['magazine','delivery']
    run_id_prefix: str = ''
    areas: list[str]
    core_areas: list[str] = Field(default_factory=list)
    taxonomy: TaxonomyOptions = Field(default_factory=TaxonomyOptions)
    sources: Sources = Field(default_factory=Sources)
    delivery_scoring: DeliveryScoring = Field(default_factory=DeliveryScoring)
    enrich: Enrich = Field(default_factory=Enrich)
    output: Output = Field(default_factory=Output)

    @field_validator('core_areas')
    @classmethod
    def validate_core(cls, value, info):
        areas = info.data.get('areas', [])
        unknown = set(value) - set(areas)
        if unknown: raise ValueError(f'core_areas not present in areas: {sorted(unknown)}')
        return value


def load_config(path: str | Path) -> RunConfig:
    with Path(path).open(encoding='utf-8') as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict): raise ValueError('configuration must be a YAML mapping')
    return RunConfig.model_validate(data)
