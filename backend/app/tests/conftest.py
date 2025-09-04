import os
import pytest
from sqlmodel import SQLModel, create_engine, Session

# Use sqlite for tests to avoid need for Postgres
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})

@pytest.fixture(scope="session", autouse=True)
def _create_test_db():
    from backend.app.models.models import SQLModel as Base
    from backend.app.models import models  # ensure import
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture()
def session():
    with Session(engine) as s:
        yield s
