from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Coordinate(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra='forbid')
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

class RouteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    start: Coordinate
    end: Coordinate
    preference: Literal['fastest', 'balanced', 'comfortable'] = 'comfortable'
