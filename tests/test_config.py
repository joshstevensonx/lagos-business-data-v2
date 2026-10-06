import pytest
from lagosdata.config import RunConfig

BASE={'pipeline':'magazine','areas':['X'],'core_areas':['X']}
def test_unknown_keys_rejected():
    with pytest.raises(Exception):RunConfig.model_validate({**BASE,'typo':True})
def test_invalid_concurrency_rejected():
    with pytest.raises(Exception):RunConfig.model_validate({**BASE,'sources':{'gmaps_browser':{'concurrency':7}}})
def test_places_disabled_by_default():
    cfg=RunConfig.model_validate(BASE);assert cfg.sources.places_api.enabled is False
