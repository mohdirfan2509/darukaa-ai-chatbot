from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.environmental_data import EnvironmentalObservation
from app.schemas.environment import (
    EnvironmentAnalyzeRequest,
    EnvironmentAnalyzeResponse,
    ObservationCreate,
    ObservationOut,
)
from app.services.environment.service import EnvironmentService

router = APIRouter(prefix="/environment", tags=["environment"])


@router.post("/analyze", response_model=EnvironmentAnalyzeResponse)
async def analyze_environment(
    body: EnvironmentAnalyzeRequest,
) -> EnvironmentAnalyzeResponse:
    service = EnvironmentService()
    result = await service.analyze(text=body.text, variables=body.variables)
    return EnvironmentAnalyzeResponse(**result)


@router.post("/observations", response_model=ObservationOut)
def create_observation(
    body: ObservationCreate,
    db: Session = Depends(get_db),
) -> EnvironmentalObservation:
    obs = EnvironmentalObservation(
        metric=body.metric,
        value=body.value,
        value_text=body.value_text,
        unit=body.unit,
        source=body.source,
        quality=body.quality,
        latitude=body.latitude,
        longitude=body.longitude,
        region=body.region,
        conversation_id=body.conversation_id,
        notes=body.notes,
        metadata_=body.metadata,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs


@router.get("/observations", response_model=List[ObservationOut])
def list_observations(
    db: Session = Depends(get_db),
) -> list[EnvironmentalObservation]:
    return (
        db.query(EnvironmentalObservation)
        .order_by(EnvironmentalObservation.created_at.desc())
        .limit(100)
        .all()
    )
