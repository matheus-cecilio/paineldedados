from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ...db.session import get_session
from ...models.models import ImportJob
from ...services.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"]) 

@router.get("/imports")
async def list_imports(session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    jobs = session.exec(select(ImportJob).order_by(ImportJob.created_at.desc())).all()
    return [{"id": str(j.id), "filename": j.filename, "status": j.status, "created_at": j.created_at, "finished_at": j.finished_at} for j in jobs]
