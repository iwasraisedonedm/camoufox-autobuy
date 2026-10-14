"""Monitoring-job routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from autobuy.control_plane.dependencies import Coordinator, DbSession
from autobuy.control_plane.schemas import MonitoringJobCreate, MonitoringJobRead
from autobuy.control_plane.services.jobs import create_monitoring_job, start_monitoring_job
from autobuy.domain.enums import WorkflowMode
from autobuy.persistence.models import MonitoringJob

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("", response_model=MonitoringJobRead, status_code=status.HTTP_201_CREATED)
async def create_job_route(
    payload: MonitoringJobCreate,
    session: DbSession,
) -> MonitoringJob:
    try:
        workflow_mode = WorkflowMode(payload.workflow_mode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid workflow mode") from exc

    return await create_monitoring_job(
        session,
        customer_id=payload.customer_id,
        entitlement_id=payload.entitlement_id,
        retailer_profile_id=payload.retailer_profile_id,
        purchase_target_id=payload.purchase_target_id,
        workflow_mode=workflow_mode,
        max_unit_price=payload.max_unit_price,
        currency=payload.currency,
        quantity_requested=payload.quantity_requested,
        success_limit=payload.success_limit,
        expires_at=payload.expires_at,
    )


@router.get("/{job_id}", response_model=MonitoringJobRead)
async def get_job(job_id: UUID, session: DbSession) -> MonitoringJob:
    job = await session.get(MonitoringJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job



@router.post("/{job_id}/start", response_model=MonitoringJobRead)
async def start_job(
    job_id: UUID,
    session: DbSession,
    coordinator: Coordinator,
) -> MonitoringJob:
    return await start_monitoring_job(session, coordinator, job_id=job_id)
