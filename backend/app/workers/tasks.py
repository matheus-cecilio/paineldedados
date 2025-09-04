import json
from datetime import datetime
import pandas as pd
from sqlmodel import Session
from ..db.session import engine
from ..models.models import ImportJob, ImportStatus
from ..services.excel import import_rows
from .celery_app import celery
import requests
import os

REQUIRED_COLUMNS = {"SKU", "Product", "Category", "Price", "Quantity", "Customer Name", "Customer Email", "Sale Date"}

@celery.task(name="app.workers.tasks.import_file")
def enqueue_import(job_id: str, filepath: str):
    with Session(engine) as session:
        job = session.get(ImportJob, job_id)
        if not job:
            return
        job.status = ImportStatus.RUNNING
        session.add(job)
        session.commit()

        try:
            # Pick reader by extension
            ext = os.path.splitext(filepath)[1].lower()
            if ext in (".xlsx", ".xls"): 
                df = pd.read_excel(filepath)
            else:
                df = pd.read_csv(filepath)

            missing = REQUIRED_COLUMNS - set(df.columns)
            if missing:
                raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")

            rows = df.to_dict(orient="records")
            result = import_rows(session, rows, dedupe=True)
            job.status = ImportStatus.DONE
            job.finished_at = datetime.utcnow()
            job.errors = None
            session.add(job)
            session.commit()

            # Optional webhook
            url = os.getenv("FRONTEND_WEBHOOK_URL")
            if url:
                try:
                    requests.post(url, json={"job_id": job_id, "result": result}, timeout=3)
                except Exception:
                    pass
        except Exception as e:
            job.status = ImportStatus.FAILED
            job.finished_at = datetime.utcnow()
            job.errors = {"error": str(e)}
            session.add(job)
            session.commit()
            raise
