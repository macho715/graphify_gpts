"""Job lifecycle routes: /v1/graphify/jobs."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import require_bearer
from ..build_pipeline import run_build
from ..jobs import cancel, get, new_job_id, submit
from ..models import BuildRequest, Job

router = APIRouter(prefix="/v1/graphify", tags=["jobs"])


def _initial_job(job_id: str) -> Job:
    now = datetime.now(timezone.utc)
    return Job(
        job_id=job_id,
        status="queued",
        graph_id=None,
        message="queued",
        created_at=now,
        updated_at=now,
    )


@router.post(
    "/jobs",
    response_model=Job,
    operation_id="graphifyBuild",
    summary="Start a Graphify build job from an accessible URI.",
)
async def create_build_job(
    body: BuildRequest,
    _key: str = Depends(require_bearer),
) -> Job:
    job_id = new_job_id()
    initial = _initial_job(job_id)
    submit(
        initial=initial,
        work_fn=lambda: run_build(
            job_id,
            input_uri=str(body.input_uri),
            branch=body.branch,
            mode=body.mode,
            no_viz=body.no_viz,
        ),
    )
    return initial


@router.get(
    "/jobs/{job_id}",
    response_model=Job,
    operation_id="graphifyJobStatus",
    summary="Get Graphify job status.",
)
async def get_job(job_id: str, _key: str = Depends(require_bearer)) -> Job:
    job = get(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return job


@router.delete(
    "/jobs/{job_id}",
    response_model=Job,
    operation_id="graphifyJobCancel",
    summary="Cancel a queued or running job.",
)
async def cancel_job(job_id: str, _key: str = Depends(require_bearer)) -> Job:
    job = cancel(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="job not found")
    return job
