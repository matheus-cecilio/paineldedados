from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import select
from sqlmodel import Session
from ...db.session import get_session
from ...models.models import Product, Customer, Category, Sale
from ...services.auth import get_current_user

router = APIRouter(tags=["crud"]) 

# Utility pagination

def paginate(query, page: int, per_page: int):
    offset = (page - 1) * per_page
    return query.offset(offset).limit(per_page)

# Products

@router.get("/products", response_model=List[Product])
async def list_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    stmt = select(Product)
    if q:
        stmt = stmt.where((Product.name.ilike(f"%{q}%")) | (Product.sku.ilike(f"%{q}%")))
    if category:
        # Allow category by UUID or by name
        try:
            from uuid import UUID
            cat_id = UUID(category)
            stmt = stmt.where(Product.category_id == cat_id)
        except Exception:
            cat = session.exec(select(Category).where(Category.name == category)).first()
            if cat:
                stmt = stmt.where(Product.category_id == cat.id)
            else:
                # no results if category not found
                stmt = stmt.where(Product.category_id == None)  # noqa: E711
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)
    stmt = stmt.order_by(Product.created_at.desc())
    results = session.exec(paginate(stmt, page, per_page)).all()
    return results

@router.post("/products", response_model=Product)
async def create_product(data: Product, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    session.add(data)
    session.commit()
    session.refresh(data)
    return data

@router.get("/products/{item_id}", response_model=Product)
async def get_product(item_id: str, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    obj = session.get(Product, item_id)
    if not obj:
        raise HTTPException(404, "Product not found")
    return obj

@router.put("/products/{item_id}", response_model=Product)
async def update_product(item_id: str, data: Product, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    obj = session.get(Product, item_id)
    if not obj:
        raise HTTPException(404, "Product not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(obj, field, value)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

@router.delete("/products/{item_id}")
async def delete_product(item_id: str, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    obj = session.get(Product, item_id)
    if not obj:
        raise HTTPException(404, "Product not found")
    session.delete(obj)
    session.commit()
    return {"ok": True}

# Customers

@router.get("/customers", response_model=List[Customer])
async def list_customers(page: int = 1, per_page: int = 20, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    stmt = select(Customer).order_by(Customer.created_at.desc())
    return session.exec(paginate(stmt, page, per_page)).all()

@router.post("/customers", response_model=Customer)
async def create_customer(data: Customer, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    session.add(data)
    session.commit()
    session.refresh(data)
    return data

@router.get("/customers/{item_id}", response_model=Customer)
async def get_customer(item_id: str, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    obj = session.get(Customer, item_id)
    if not obj:
        raise HTTPException(404, "Customer not found")
    return obj

@router.put("/customers/{item_id}", response_model=Customer)
async def update_customer(item_id: str, data: Customer, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    obj = session.get(Customer, item_id)
    if not obj:
        raise HTTPException(404, "Customer not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(obj, field, value)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

@router.delete("/customers/{item_id}")
async def delete_customer(item_id: str, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    obj = session.get(Customer, item_id)
    if not obj:
        raise HTTPException(404, "Customer not found")
    session.delete(obj)
    session.commit()
    return {"ok": True}

# Categories

@router.get("/categories", response_model=List[Category])
async def list_categories(page: int = 1, per_page: int = 50, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    stmt = select(Category).order_by(Category.name.asc())
    return session.exec(paginate(stmt, page, per_page)).all()

@router.post("/categories", response_model=Category)
async def create_category(data: Category, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    session.add(data)
    session.commit()
    session.refresh(data)
    return data

@router.get("/categories/{item_id}", response_model=Category)
async def get_category(item_id: str, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    obj = session.get(Category, item_id)
    if not obj:
        raise HTTPException(404, "Category not found")
    return obj

@router.put("/categories/{item_id}", response_model=Category)
async def update_category(item_id: str, data: Category, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    obj = session.get(Category, item_id)
    if not obj:
        raise HTTPException(404, "Category not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(obj, field, value)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

@router.delete("/categories/{item_id}")
async def delete_category(item_id: str, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    obj = session.get(Category, item_id)
    if not obj:
        raise HTTPException(404, "Category not found")
    session.delete(obj)
    session.commit()
    return {"ok": True}

# Sales

@router.get("/sales", response_model=List[Sale])
async def list_sales(
    start: Optional[str] = None,
    end: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
    session: Session = Depends(get_session),
    user: dict = Depends(get_current_user),
):
    stmt = select(Sale)
    if start:
        from datetime import datetime
        stmt = stmt.where(Sale.sale_date >= datetime.fromisoformat(start))
    if end:
        from datetime import datetime
        stmt = stmt.where(Sale.sale_date <= datetime.fromisoformat(end))
    stmt = stmt.order_by(Sale.sale_date.desc())
    return session.exec(paginate(stmt, page, per_page)).all()

@router.post("/sales", response_model=Sale)
async def create_sale(data: Sale, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    session.add(data)
    session.commit()
    session.refresh(data)
    return data

@router.get("/sales/{item_id}", response_model=Sale)
async def get_sale(item_id: str, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    obj = session.get(Sale, item_id)
    if not obj:
        raise HTTPException(404, "Sale not found")
    return obj

@router.put("/sales/{item_id}", response_model=Sale)
async def update_sale(item_id: str, data: Sale, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    obj = session.get(Sale, item_id)
    if not obj:
        raise HTTPException(404, "Sale not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(obj, field, value)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj

@router.delete("/sales/{item_id}")
async def delete_sale(item_id: str, session: Session = Depends(get_session), user: dict = Depends(get_current_user)):
    obj = session.get(Sale, item_id)
    if not obj:
        raise HTTPException(404, "Sale not found")
    session.delete(obj)
    session.commit()
    return {"ok": True}
