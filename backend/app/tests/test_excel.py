import io
import pytest
from sqlmodel import Session
from backend.app.services.excel import parse_price, parse_date, import_rows


def test_parse_price_ptbr():
    assert parse_price("R$ 1.234,56") == 1234.56
    assert parse_price("1234.56") == 1234.56
    assert parse_price("1.234,56") == 1234.56


def test_parse_date_formats():
    assert parse_date("01/09/2025").year == 2025
    assert parse_date("2025-09-01").month == 9


def test_import_rows_happy_path(session: Session):
    rows = [
        {
            "SKU": "ABC-1",
            "Product": "Produto X",
            "Category": "Geral",
            "Price": "R$ 10,00",
            "Quantity": 2,
            "Customer Name": "João",
            "Customer Email": "joao@example.com",
            "Sale Date": "01/09/2025",
        }
    ]
    result = import_rows(session, rows)
    assert result["inserted"] == 1
