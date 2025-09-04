from fastapi import APIRouter, Depends
from ...services.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/verify")
async def verify(user = Depends(get_current_user)):
    return {"ok": True, "user": user}
