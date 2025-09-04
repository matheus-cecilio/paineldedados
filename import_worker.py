from sqlmodel import Session
from app.models.all_models import ImportJob
from app.services.excel_parser import ExcelParser
import io
from datetime import datetime

def process_excel_file(job_id: str, file_contents: bytes, db_session: Session):
    """
    The main worker function to process the uploaded Excel file.
    This function is run in the background.
    """
    job = db_session.get(ImportJob, job_id)
    if not job:
        return

    job.status = "RUNNING"
    db_session.add(job)
    db_session.commit()

    try:
        file_like_object = io.BytesIO(file_contents)
        parser = ExcelParser(file_like_object, db_session)
        parser.run()
        job.status = "DONE"
    except Exception as e:
        job.status = "FAILED"
        job.errors = {"error": str(e)}
    finally:
        job.finished_at = datetime.utcnow()
        db_session.add(job)
        db_session.commit()