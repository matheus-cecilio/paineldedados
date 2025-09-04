import uuid
from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship, JSON, Column


class Category(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="category.id")
    
    products: List["Product"] = Relationship(back_populates="category")


class Customer(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    sales: List["Sale"] = Relationship(back_populates="customer")


class Product(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    sku: str = Field(index=True, unique=True)
    name: str
    price: float
    stock: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    category_id: uuid.UUID = Field(foreign_key="category.id")
    category: Category = Relationship(back_populates="products")
    sales: List["Sale"] = Relationship(back_populates="product")


class Sale(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    quantity: int
    price_unit: float
    total: float
    sale_date: datetime
    source: str = "excel_import"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    product_id: uuid.UUID = Field(foreign_key="product.id")
    product: Product = Relationship(back_populates="sales")
    customer_id: uuid.UUID = Field(foreign_key="customer.id")
    customer: Customer = Relationship(back_populates="sales")

class ImportJob(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    filename: str
    status: str = Field(default="PENDING", index=True) # PENDING, RUNNING, FAILED, DONE
    errors: Optional[dict] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None