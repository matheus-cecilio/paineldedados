from datetime import datetime
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from ...db.session import get_session
from ...models.models import Sale
from ...services.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"]) 

@router.get("/summary")
async def summary(start: str, end: str, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    sales = session.exec(select(Sale).where(Sale.sale_date >= start_dt, Sale.sale_date <= end_dt)).all()

    total_sales = sum(s.qty for s in sales)
    revenue = sum(s.total for s in sales)
    ticket_medio = (revenue / total_sales) if total_sales else 0

    # top produtos
    from collections import Counter
    c = Counter()
    for s in sales:
        c[s.product_id] += s.total
    top_products = [{"product_id": str(pid), "revenue": rev} for pid, rev in c.most_common(5)]

    # crescimento por período (dias)
    by_day = {}
    for s in sales:
        day = s.sale_date.date().isoformat()
        by_day.setdefault(day, 0)
        by_day[day] += s.total

    return {
        "total_sales": total_sales,
        "revenue": revenue,
        "ticket_medio": ticket_medio,
        "top_products": top_products,
        "series": sorted([{ "date": d, "revenue": v } for d, v in by_day.items()], key=lambda x: x["date"]),
    }
