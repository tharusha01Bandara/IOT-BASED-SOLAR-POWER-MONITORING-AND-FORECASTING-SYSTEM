"""
Health Check Router

Provides endpoints for monitoring application health and status.
"""

from fastapi import APIRouter, Depends, status
from typing import Annotated

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.mongodb import mongodb_client
from app.schemas.readings import HealthCheckResponse

logger = get_logger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["health"]
)


@router.get(
    "",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the API and database are operational"
)
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)]
) -> HealthCheckResponse:
    """
    Perform health check on the application.
    
    Verifies that the API is running and database connection is healthy.
    
    Args:
        settings: Application settings (injected)
        
    Returns:
        Health status response
    """
    # Check database health
    db_status = "connected" if mongodb_client.health_check() else "disconnected"
    
    # Determine overall status
    overall_status = "healthy" if db_status == "connected" else "degraded"
    
    logger.debug(f"Health check: status={overall_status}, database={db_status}")
    
    return HealthCheckResponse(
        status=overall_status,
        database=db_status,
        version=settings.app_version
    )


@router.get(
    "/ping",
    status_code=status.HTTP_200_OK,
    summary="Simple ping",
    description="Simple endpoint to verify API is responding"
)
async def ping():
    """
    Simple ping endpoint for basic availability check.
    
    Returns:
        Simple success message
    """
    return {"status": "ok", "message": "pong"}
