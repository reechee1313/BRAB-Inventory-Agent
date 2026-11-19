"""
search_auction_data.py
----------------------
BRAB Inventory Agent – Auction Data Search Tool

Loads BRAB_Auction_Data.csv (expected in the same directory as this script)
and exposes functions to query/filter auction records.

Self-tests are included at the bottom (run with: python search_auction_data.py)
or via: python -m unittest search_auction_data
"""

import csv
import os
import unittest
from typing import Any

# ---------------------------------------------------------------------------
# Path configuration
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(_HERE, "BRAB_Auction_Data.csv")

# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

def load_data(csv_path: str = CSV_PATH) -> list[dict]:
    """
    Load auction records from a CSV file.

    Returns a list of dicts, one per row.  Numeric fields (year, odometer,
    condition, mmr, sellingprice) are coerced to float/int where possible;
    missing or non-numeric values are stored as None.
    """
    numeric_fields = {
        "year": int,
        "odometer": int,
        "condition": float,
        "mmr": int,
        "sellingprice": int,
    }
    records = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # Strip trailing empty key that sometimes appears in CSVs
            clean = {k.strip(): v.strip() for k, v in row.items() if k and k.strip()}
            for field, cast in numeric_fields.items():
                raw = clean.get(field, "")
                try:
                    clean[field] = cast(float(raw)) if raw else None
                except (ValueError, TypeError):
                    clean[field] = None
            records.append(clean)
    return records


# ---------------------------------------------------------------------------
# Search / filter helpers
# ---------------------------------------------------------------------------

def search(
    records: list[dict],
    *,
    make: str | None = None,
    model: str | None = None,
    year_min: int | None = None,
    year_max: int | None = None,
    odometer_max: int | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    color: str | None = None,
    body: str | None = None,
    transmission: str | None = None,
    seller: str | None = None,
    state: str | None = None,
    condition_min: float | None = None,
) -> list[dict]:
    """
    Filter auction records by any combination of criteria.

    All string comparisons are case-insensitive substring matches so that,
    for example, make='kia' will match 'Kia'.

    Parameters
    ----------
    records       : list returned by load_data()
    make          : vehicle make (substring match)
    model         : vehicle model (substring match)
    year_min      : earliest model year (inclusive)
    year_max      : latest model year (inclusive)
    odometer_max  : maximum odometer reading
    price_min     : minimum selling price
    price_max     : maximum selling price
    color         : exterior colour (substring match)
    body          : body style, e.g. 'SUV', 'Sedan' (substring match)
    transmission  : 'automatic' or 'manual' (substring match)
    seller        : seller name (substring match)
    state         : two-letter state code, e.g. 'ca'
    condition_min : minimum auction condition score

    Returns
    -------
    list of matching records (original dicts, not copies)
    """

    def _matches(value: Any, pattern: str) -> bool:
        return pattern.lower() in str(value).lower()

    results = []
    for rec in records:
        if make and not _matches(rec.get("make", ""), make):
            continue
        if model and not _matches(rec.get("model", ""), model):
            continue
        if year_min is not None and (rec.get("year") is None or rec["year"] < year_min):
            continue
        if year_max is not None and (rec.get("year") is None or rec["year"] > year_max):
            continue
        if odometer_max is not None and (rec.get("odometer") is None or rec["odometer"] > odometer_max):
            continue
        if price_min is not None and (rec.get("sellingprice") is None or rec["sellingprice"] < price_min):
            continue
        if price_max is not None and (rec.get("sellingprice") is None or rec["sellingprice"] > price_max):
            continue
        if color and not _matches(rec.get("color", ""), color):
            continue
        if body and not _matches(rec.get("body", ""), body):
            continue
        if transmission and not _matches(rec.get("transmission", ""), transmission):
            continue
        if seller and not _matches(rec.get("seller", ""), seller):
            continue
        if state and not _matches(rec.get("state", ""), state):
            continue
        if condition_min is not None and (rec.get("condition") is None or rec["condition"] < condition_min):
            continue
        results.append(rec)
    return results


def summarise(records: list[dict]) -> dict:
    """
    Return basic summary statistics for a list of auction records.

    Returns a dict with keys:
        count, avg_selling_price, min_selling_price, max_selling_price,
        avg_odometer, avg_mmr
    """
    if not records:
        return {
            "count": 0,
            "avg_selling_price": None,
            "min_selling_price": None,
            "max_selling_price": None,
            "avg_odometer": None,
            "avg_mmr": None,
        }

    prices = [r["sellingprice"] for r in records if r.get("sellingprice") is not None]
    odometers = [r["odometer"] for r in records if r.get("odometer") is not None]
    mmrs = [r["mmr"] for r in records if r.get("mmr") is not None]

    def _avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else None

    return {
        "count": len(records),
        "avg_selling_price": _avg(prices),
        "min_selling_price": min(prices) if prices else None,
        "max_selling_price": max(prices) if prices else None,
        "avg_odometer": _avg(odometers),
        "avg_mmr": _avg(mmrs),
    }


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

class TestLoadData(unittest.TestCase):
    """Tests for the load_data() function."""

    @classmethod
    def setUpClass(cls):
        cls.records = load_data()

    def test_records_loaded(self):
        """CSV must load at least one record."""
        self.assertGreater(len(self.records), 0, "No records loaded from CSV")

    def test_required_columns_present(self):
        """Every record must contain the expected column keys."""
        required = {
            "year", "make", "model", "trim", "body", "transmission",
            "vin", "state", "condition", "odometer", "color", "interior",
            "seller", "mmr", "sellingprice", "saledate",
        }
        for rec in self.records:
            missing = required - set(rec.keys())
            self.assertEqual(missing, set(), f"Missing columns in record: {missing}")

    def test_year_coerced_to_int(self):
        """Year field must be an int (or None for blank rows)."""
        for rec in self.records:
            if rec["year"] is not None:
                self.assertIsInstance(rec["year"], int, f"year is not int: {rec['year']!r}")

    def test_sellingprice_coerced(self):
        """sellingprice must be numeric or None."""
        for rec in self.records:
            self.assertIn(
                type(rec["sellingprice"]), (int, type(None)),
                f"sellingprice unexpected type: {type(rec['sellingprice'])}",
            )


class TestSearch(unittest.TestCase):
    """Tests for the search() filter function."""

    @classmethod
    def setUpClass(cls):
        cls.records = load_data()

    def test_filter_by_make(self):
        """Filtering by make='kia' returns only Kia records."""
        results = search(self.records, make="kia")
        self.assertGreater(len(results), 0, "Expected Kia records")
        for rec in results:
            self.assertIn("kia", rec["make"].lower())

    def test_filter_by_make_case_insensitive(self):
        """make filter is case-insensitive."""
        lower = search(self.records, make="bmw")
        upper = search(self.records, make="BMW")
        self.assertEqual(len(lower), len(upper))

    def test_filter_by_year_range(self):
        """year_min / year_max boundaries are both inclusive."""
        results = search(self.records, year_min=2014, year_max=2014)
        for rec in results:
            self.assertEqual(rec["year"], 2014)

    def test_filter_by_price_range(self):
        """price_min and price_max filter sellingprice correctly."""
        results = search(self.records, price_min=20000, price_max=25000)
        for rec in results:
            self.assertGreaterEqual(rec["sellingprice"], 20000)
            self.assertLessEqual(rec["sellingprice"], 25000)

    def test_filter_by_body(self):
        """Body style filter returns only matching body types."""
        results = search(self.records, body="suv")
        self.assertGreater(len(results), 0, "Expected SUV records")
        for rec in results:
            self.assertIn("suv", rec["body"].lower())

    def test_no_match_returns_empty_list(self):
        """A filter that matches nothing returns an empty list, not an error."""
        results = search(self.records, make="NONEXISTENTBRAND99")
        self.assertEqual(results, [])

    def test_multiple_filters(self):
        """Combining make + body + year_max narrows the result set."""
        all_kia = search(self.records, make="kia")
        filtered = search(self.records, make="kia", body="suv", year_max=2015)
        self.assertLessEqual(len(filtered), len(all_kia))

    def test_odometer_max(self):
        """odometer_max excludes high-mileage vehicles."""
        results = search(self.records, odometer_max=5000)
        for rec in results:
            if rec["odometer"] is not None:
                self.assertLessEqual(rec["odometer"], 5000)


class TestSummarise(unittest.TestCase):
    """Tests for the summarise() statistics helper."""

    @classmethod
    def setUpClass(cls):
        cls.records = load_data()

    def test_empty_input(self):
        """summarise([]) returns a zero-count dict without raising."""
        result = summarise([])
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["avg_selling_price"])

    def test_count_matches(self):
        """count in summary equals len(records)."""
        result = summarise(self.records)
        self.assertEqual(result["count"], len(self.records))

    def test_price_bounds(self):
        """min_selling_price <= avg_selling_price <= max_selling_price."""
        result = summarise(self.records)
        if result["avg_selling_price"] is not None:
            self.assertLessEqual(result["min_selling_price"], result["avg_selling_price"])
            self.assertGreaterEqual(result["max_selling_price"], result["avg_selling_price"])

    def test_kia_summary(self):
        """Kia subset summary returns non-None averages."""
        kia = search(self.records, make="kia")
        result = summarise(kia)
        self.assertGreater(result["count"], 0)
        self.assertIsNotNone(result["avg_selling_price"])


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"CSV path : {CSV_PATH}")
    print(f"CSV exists: {os.path.exists(CSV_PATH)}\n")
    unittest.main(verbosity=2)
