"""
Unit tests for all data parsers.
Tests use real-world-shaped XML/text samples — no network calls.
"""
import pytest
from datetime import timezone

from app.parsers.form4 import parse_form4
from app.parsers.form13f import parse_form13f
from app.parsers.congress import parse_amount_bracket, parse_house_xml
from app.parsers.finra_short import parse_finra_short_file
from app.parsers.base import safe_decimal, safe_date, safe_int, business_days_between


# ── base helpers ──────────────────────────────────────────────────────────────

def test_safe_decimal_handles_commas():
    assert float(safe_decimal("1,234,567.89")) == pytest.approx(1_234_567.89)

def test_safe_decimal_handles_dollar_sign():
    assert float(safe_decimal("$45.67")) == pytest.approx(45.67)

def test_safe_decimal_returns_none_for_na():
    assert safe_decimal("N/A") is None
    assert safe_decimal("") is None
    assert safe_decimal(None) is None

def test_safe_date_multiple_formats():
    assert safe_date("2024-03-15").year == 2024
    assert safe_date("03/15/2024").month == 3
    assert safe_date("20240315").day == 15

def test_business_days():
    from datetime import datetime
    mon = datetime(2024, 1, 1, tzinfo=timezone.utc)   # Monday
    fri = datetime(2024, 1, 5, tzinfo=timezone.utc)   # Friday
    assert business_days_between(mon, fri) == 4


# ── Form 4 parser ─────────────────────────────────────────────────────────────

FORM4_XML = b"""<?xml version="1.0"?>
<ownershipDocument>
  <issuer>
    <issuerCik>0000320193</issuerCik>
    <issuerName>Apple Inc.</issuerName>
    <issuerTradingSymbol>AAPL</issuerTradingSymbol>
  </issuer>
  <reportingOwner>
    <reportingOwnerId>
      <rptOwnerName>Cook Timothy D</rptOwnerName>
    </reportingOwnerId>
    <reportingOwnerRelationship>
      <isOfficer>1</isOfficer>
      <officerTitle>Chief Executive Officer</officerTitle>
    </reportingOwnerRelationship>
  </reportingOwner>
  <nonDerivativeTable>
    <nonDerivativeTransaction>
      <securityTitle><value>Common Stock</value></securityTitle>
      <transactionDate><value>2024-03-01</value></transactionDate>
      <transactionCoding>
        <transactionCode>P</transactionCode>
      </transactionCoding>
      <transactionAmounts>
        <transactionShares><value>10000</value></transactionShares>
        <transactionPricePerShare><value>180.50</value></transactionPricePerShare>
        <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
      </transactionAmounts>
    </nonDerivativeTransaction>
  </nonDerivativeTable>
</ownershipDocument>"""

def test_form4_parse_basic():
    trades = parse_form4(FORM4_XML, form_url="https://sec.gov/test")
    assert len(trades) == 1
    t = trades[0]
    assert t["ticker"] == "AAPL"
    assert t["transaction_type"] == "buy"
    assert t["shares"] == 10_000
    assert t["price_per_share"] == pytest.approx(180.50)
    assert t["total_value"] == pytest.approx(1_805_000.0)
    assert t["insider_name"] == "Cook Timothy D"
    assert "CEO" in t["insider_title"] or "Chief" in t["insider_title"]

def test_form4_sell_transaction():
    xml = FORM4_XML.replace(b"<transactionCode>P</transactionCode>",
                             b"<transactionCode>S</transactionCode>")
    trades = parse_form4(xml)
    assert trades[0]["transaction_type"] == "sell"

def test_form4_empty_ticker_skipped():
    xml = FORM4_XML.replace(b"<issuerTradingSymbol>AAPL</issuerTradingSymbol>",
                             b"<issuerTradingSymbol></issuerTradingSymbol>")
    trades = parse_form4(xml)
    assert len(trades) == 0

def test_form4_invalid_xml_raises():
    with pytest.raises(ValueError):
        parse_form4(b"<broken xml")


# ── 13F parser ────────────────────────────────────────────────────────────────

FORM13F_XML = b"""<?xml version="1.0"?>
<informationTable>
  <infoTable>
    <nameOfIssuer>APPLE INC</nameOfIssuer>
    <titleOfClass>COM</titleOfClass>
    <cusip>037833100</cusip>
    <value>5000000</value>
    <shrsOrPrnAmt>
      <sshPrnamt>28000</sshPrnamt>
      <sshPrnamtType>SH</sshPrnamtType>
    </shrsOrPrnAmt>
    <investmentDiscretion>SOLE</investmentDiscretion>
  </infoTable>
</informationTable>"""

def test_13f_parse_basic():
    holdings = parse_form13f(FORM13F_XML, "0001234567", "Test Fund", "2024-03-31")
    assert len(holdings) == 1
    h = holdings[0]
    assert h["cusip"] == "037833100"
    assert h["value_usd"] == pytest.approx(5_000_000_000.0)  # thousands * 1000
    assert h["shares"] == 28_000
    assert h["issuer_name"] == "APPLE INC"


# ── Congress parser ───────────────────────────────────────────────────────────

def test_amount_bracket_standard():
    lo, hi = parse_amount_bracket("$15,001 - $50,000")
    assert lo == 15_001
    assert hi == 50_000

def test_amount_bracket_over():
    lo, hi = parse_amount_bracket("Over $5,000,000")
    assert lo == 5_000_001

def test_amount_bracket_unknown_returns_zero():
    lo, hi = parse_amount_bracket("Unknown bracket")
    assert lo == 0 and hi == 0


# ── FINRA parser ──────────────────────────────────────────────────────────────

FINRA_SAMPLE = """Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market
20240315|AAPL|5000000|12000|10000000|FINRA
20240315|TSLA|2000000|5000|4000000|FINRA
20240315|invalid_ticker_too_long_to_pass|100|0|200|FINRA
Date|Total|7000100|17000|14000200|
"""

def test_finra_parse_basic():
    prints = parse_finra_short_file(FINRA_SAMPLE)
    tickers = [p["ticker"] for p in prints]
    assert "AAPL" in tickers
    assert "TSLA" in tickers

def test_finra_short_pct_calculated():
    prints = parse_finra_short_file(FINRA_SAMPLE)
    aapl = next(p for p in prints if p["ticker"] == "AAPL")
    assert aapl["short_pct"] == pytest.approx(50.0)

def test_finra_totals_row_skipped():
    prints = parse_finra_short_file(FINRA_SAMPLE)
    tickers = [p["ticker"] for p in prints]
    assert "Date" not in tickers
    assert "Total" not in tickers

def test_finra_long_ticker_skipped():
    prints = parse_finra_short_file(FINRA_SAMPLE)
    tickers = [p["ticker"] for p in prints]
    assert "INVALID_TICKER_TOO_LONG_TO_PASS" not in tickers
