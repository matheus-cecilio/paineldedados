from backend.app.services.excel import parse_price


def test_price_brazilian_formats():
    cases = {
        "R$ 1.234,56": 1234.56,
        "1.234,56": 1234.56,
        "1234.56": 1234.56,
        "R$0,00": 0.0,
    }
    for raw, expected in cases.items():
        assert parse_price(raw) == expected
