import uuid
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from sqlmodel import Session

from app.db.session import get_session
from app.models.all_models import ImportJob
from app.workers.import_worker import process_excel_file
from app.schemas.import_job import ImportJobRead, ImportJobCreate

router = APIRouter()

@router.post("/upload", response_model=ImportJobRead)
def upload_excel(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
):
    """
    Upload an Excel file for asynchronous processing.
    """
    # TODO: Add user_id from JWT token
    job = ImportJob(filename=file.filename)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Add the processing to background tasks
    background_tasks.add_task(process_excel_file, job_id=job.id, file_contents=file.file.read(), db_session=db)

    return job

@router.get("/status/{job_id}", response_model=ImportJobRead)
def get_import_status(job_id: uuid.UUID, db: Session = Depends(get_session)):
    """
    Get the status of an import job.
    """
    job = db.get(ImportJob, job_id)
    if not job:
        # You might want to raise an HTTPException here
        return {"error": "Job not found"}
    return job