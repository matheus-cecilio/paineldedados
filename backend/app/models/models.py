from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
import uuid

class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

class Customer(SQLModel, table=True):
    __tablename__ = "customers"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    email: Optional[str] = Field(default=None, unique=True, index=True)
    phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    sales: list["Sale"] = Relationship(back_populates="customer")

class Category(SQLModel, table=True):
    __tablename__ = "categories"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, unique=True)
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="categories.id")

class Product(SQLModel, table=True):
    __tablename__ = "products"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    sku: str = Field(index=True, unique=True)
    name: str
    category_id: Optional[uuid.UUID] = Field(default=None, foreign_key="categories.id")
    price: float = 0.0
    stock: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    category: Optional["Category"] = Relationship()
    sales: list["Sale"] = Relationship(back_populates="product")

class Sale(SQLModel, table=True):
    __tablename__ = "sales"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    product_id: uuid.UUID = Field(foreign_key="products.id")
    customer_id: Optional[uuid.UUID] = Field(default=None, foreign_key="customers.id")
    qty: int
    price_unit: float
    total: float
    sale_date: datetime
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    product: "Product" = Relationship(back_populates="sales")
    customer: Optional["Customer"] = Relationship(back_populates="sales")

class ImportStatus(str):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    DONE = "DONE"

class ImportJob(SQLModel, table=True):
    __tablename__ = "imports"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    filename: str
    uploaded_by: Optional[str] = None  # Supabase user id (string)
    status: str = Field(default=ImportStatus.PENDING, index=True)
    errors: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
