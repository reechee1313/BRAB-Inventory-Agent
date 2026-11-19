"""
brab_auction_tool.py
--------------------
IBM watsonx Orchestrate ADK tool wrapper for the BRAB auction vehicle search.

Exposes the existing search_auction_data.search() and summarise() functions
as a single @tool-decorated function that the Orchestrate agent can call.

The BRAB_Auction_Data.csv file is bundled in the same package directory and
is resolved at runtime via __file__, so no external data source is required.

This file is intentionally separate from search_auction_data.py and must not
be merged into it.
"""

import json
import os
from typing import Optional

from ibm_watsonx_orchestrate.agent_builder.tools import tool

# ---------------------------------------------------------------------------
# Local package import – search_auction_data.py is bundled in this directory
# ---------------------------------------------------------------------------
from search_auction_data import load_data, search, summarise

# Resolve the CSV path relative to this file's directory (same folder).
_HERE = os.path.dirname(os.path.abspath(__file__))
_CSV_PATH = os.path.join(_HERE, "BRAB_Auction_Data.csv")

# Maximum number of individual vehicle records returned to the agent.
# Summary statistics are always returned in full regardless of this limit.
_MAX_RECORDS = 25


@tool
def search_brab_auction_vehicles(
    make: Optional[str] = None,
    model: Optional[str] = None,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    odometer_max: Optional[int] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    color: Optional[str] = None,
    body: Optional[str] = None,
    transmission: Optional[str] = None,
    seller: Optional[str] = None,
    state: Optional[str] = None,
    condition_min: Optional[float] = None,
) -> str:
    """Search the BRAB auction vehicle inventory and return matching records with summary statistics.

    All string filters use case-insensitive substring matching (e.g. make='kia'
    matches 'Kia'). All parameters are optional; omitting a parameter means no
    filter is applied for that field. Up to 25 individual vehicle records are
    returned. Summary statistics cover the full matched set regardless of this
    limit.

    Args:
        make (Optional[str]): Vehicle make to filter by, e.g. 'BMW' or 'Kia'.
        model (Optional[str]): Vehicle model to filter by, e.g. 'Sorento' or '3 Series'.
        year_min (Optional[int]): Earliest model year to include (inclusive), e.g. 2013.
        year_max (Optional[int]): Latest model year to include (inclusive), e.g. 2015.
        odometer_max (Optional[int]): Maximum odometer reading in miles, e.g. 50000.
        price_min (Optional[int]): Minimum selling price in USD, e.g. 15000.
        price_max (Optional[int]): Maximum selling price in USD, e.g. 30000.
        color (Optional[str]): Exterior colour to filter by, e.g. 'white' or 'gray'.
        body (Optional[str]): Body style to filter by, e.g. 'SUV', 'Sedan', or 'Coupe'.
        transmission (Optional[str]): Transmission type, e.g. 'automatic' or 'manual'.
        seller (Optional[str]): Seller name substring to filter by, e.g. 'kia motors'.
        state (Optional[str]): Two-letter US state code, e.g. 'ca' or 'tx'.
        condition_min (Optional[float]): Minimum auction condition score, e.g. 3.5.

    Returns:
        str: A JSON string with two keys:
             - "summary": aggregate stats (count, avg/min/max selling price,
               avg odometer, avg MMR) for the full matched set.
             - "vehicles": list of up to 25 matching vehicle records, each
               containing all CSV fields (year, make, model, trim, body,
               transmission, vin, state, condition, odometer, color,
               interior, seller, mmr, sellingprice, saledate).
    """
    records = load_data(_CSV_PATH)

    matched = search(
        records,
        make=make,
        model=model,
        year_min=year_min,
        year_max=year_max,
        odometer_max=odometer_max,
        price_min=price_min,
        price_max=price_max,
        color=color,
        body=body,
        transmission=transmission,
        seller=seller,
        state=state,
        condition_min=condition_min,
    )

    summary = summarise(matched)
    vehicles = matched[:_MAX_RECORDS]

    result = {
        "summary": summary,
        "vehicles": vehicles,
    }

    return json.dumps(result, default=str)
