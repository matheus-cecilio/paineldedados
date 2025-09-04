import re
from datetime import datetime
from typing import Optional, Tuple

from sqlmodel import Session, select
from ..models.models import Category, Customer, Product, Sale

PRICE_PATTERN = re.compile(r"[^0-9,.-]+")

def parse_price(raw: str) -> float:
    if raw is None:
        return 0.0
    s = str(raw).strip()
    if not s:
        return 0.0
    # Remove currency symbols and spaces
    s = PRICE_PATTERN.sub("", s)
    # Handle Brazilian format R$ 1.234,56 -> 1234.56
    if s.count(",") == 1 and s.count(".") >= 1 and s.rfind(",") > s.rfind("."):
        s = s.replace(".", "").replace(",", ".")
    # Handle 1.234,56 -> 1234.56
    elif "," in s and "." not in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_date(raw: str) -> datetime:
    s = str(raw).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    # last resort
    return datetime.fromisoformat(s)


def get_or_create_category(session: Session, name: Optional[str]) -> Optional[Category]:
    if not name:
        return None
    stmt = select(Category).where(Category.name == name)
    cat = session.exec(stmt).first()
    if not cat:
        cat = Category(name=name)
        session.add(cat)
        session.commit()
        session.refresh(cat)
    return cat


def get_or_create_product(session: Session, sku: str, name: str, category: Optional[Category], price: float) -> Product:
    stmt = select(Product).where(Product.sku == sku)
    prod = session.exec(stmt).first()
    if not prod:
        prod = Product(sku=sku, name=name, category_id=category.id if category else None, price=price)
        session.add(prod)
    else:
        # update basic fields
        if name:
            prod.name = name
        if category:
            prod.category_id = category.id
        if price:
            prod.price = price
    session.commit()
    session.refresh(prod)
    return prod


def get_or_create_customer(session: Session, name: Optional[str], email: Optional[str]) -> Optional[Customer]:
    if not (name or email):
        return None
    if email:
        stmt = select(Customer).where(Customer.email == email)
        cust = session.exec(stmt).first()
        if not cust:
            cust = Customer(name=name or email, email=email)
            session.add(cust)
            session.commit()
            session.refresh(cust)
        return cust
    # emailless customer keyed by name
    stmt = select(Customer).where(Customer.name == (name or ""))
    cust = session.exec(stmt).first()
    if not cust:
        cust = Customer(name=name or "")
        session.add(cust)
        session.commit()
        session.refresh(cust)
    return cust


DEDUP_KEYS = ("sku", "sale_date", "customer_email")

def compute_dedupe_key(row: dict) -> Tuple:
    return (row.get("sku"), row.get("sale_date"), row.get("customer_email"))


def import_rows(session: Session, rows: list[dict], dedupe: bool = True) -> dict:
    seen = set()
    inserted = 0
    skipped = 0

    for row in rows:
        # Normalize
        sku = str(row.get("SKU", "")).strip()
        product_name = str(row.get("Product", "")).strip() or sku
        category_name = (row.get("Category") or None)
        price = parse_price(row.get("Price"))
        qty = int(float(row.get("Quantity", 0) or 0))
        customer_name = (row.get("Customer Name") or None)
        customer_email = (row.get("Customer Email") or None)
        sale_date = parse_date(row.get("Sale Date"))

        # Dedupe key
        key = (sku, sale_date.date().isoformat(), (customer_email or "").lower())
        if dedupe and key in seen:
            skipped += 1
            continue
        seen.add(key)

        # Upserts
        category = get_or_create_category(session, category_name)
        product = get_or_create_product(session, sku, product_name, category, price)
        customer = get_or_create_customer(session, customer_name, customer_email)

        total = round(price * qty, 2)
        sale = Sale(product_id=product.id, customer_id=customer.id if customer else None, qty=qty, price_unit=price, total=total, sale_date=sale_date, source="excel")
        session.add(sale)
        session.commit()
        inserted += 1

    return {"inserted": inserted, "skipped": skipped}
