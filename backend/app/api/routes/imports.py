import os
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlmodel import Session, select
from ...db.session import get_session
from ...models.models import ImportJob, ImportStatus
from ...services.auth import get_current_user
from ...workers.tasks import enqueue_import
import uuid

router = APIRouter(prefix="/import", tags=["import"]) 

UPLOAD_DIR = "/app/data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
async def import_excel(
    background: BackgroundTasks,
    file: Optional[UploadFile] = File(default=None),
    url: Optional[str] = None,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    if not file and not url:
        raise HTTPException(400, "Provide file or url")

    job = ImportJob(filename=file.filename if file else url or "", uploaded_by=user.get("sub"))
    session.add(job)
    session.commit()
    session.refresh(job)

    ext = ".xlsx"
    if file and "." in file.filename:
        ext = os.path.splitext(file.filename)[1].lower() or ".xlsx"
    elif url and "." in url:
        ext = os.path.splitext(url)[1].lower() or ".xlsx"

    filepath = os.path.join(UPLOAD_DIR, f"{job.id}{ext}")
    if file:
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
    else:
        # Download URL
        import requests
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(r.content)

    # enqueue Celery task
    enqueue_import.delay(str(job.id), filepath)

    return {"job_id": str(job.id), "status": job.status}

@router.get("/{job_id}/status")
async def import_status(job_id: str, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    job = session.get(ImportJob, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {"id": str(job.id), "status": job.status, "errors": job.errors, "finished_at": job.finished_at}
