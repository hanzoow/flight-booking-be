from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.config import Settings
from app.legacy.client import LegacyClient
from app.services.airports import AirportIndex


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_legacy_client(request: Request) -> LegacyClient:
    return request.app.state.legacy_client


def get_airport_index(request: Request) -> AirportIndex:
    return request.app.state.airport_index


SettingsDep = Annotated[Settings, Depends(get_settings)]
LegacyDep = Annotated[LegacyClient, Depends(get_legacy_client)]
AirportIndexDep = Annotated[AirportIndex, Depends(get_airport_index)]
