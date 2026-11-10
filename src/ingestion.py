import os
import re
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
import requests

@dataclass
class HotelRecord:
    brandname: str
    revenue: float
    order: int
    email: str
    row_index: int


def load_hotel_data(file_path: Optional[str] = None, google_sheet_url: Optional[str] = None) -> List[HotelRecord]:
    """
    Ingests hotel weekly performance data from a local Excel/CSV file or a public Google Sheet URL.
    Strips footer notes, empty rows, and normalizes column headers and data types.
    """
    df: Optional[pd.DataFrame] = None

    if google_sheet_url and google_sheet_url.strip():
        url = google_sheet_url.strip()
        # Convert standard edit URL to CSV export URL if needed
        if "/edit" in url:
            url = re.sub(r"/edit.*", "/export?format=csv", url)
        elif not url.endswith("export?format=csv"):
            if "?" in url:
                url += "&export=format=csv"
            else:
                url += "/export?format=csv"

        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        import io
        df = pd.read_csv(io.StringIO(resp.text))
    else:
        path = file_path or "data/hotel_performance.xlsx"
        if not os.path.exists(path):
            raise FileNotFoundError(f"Performance data file not found at: {path}")

        if path.endswith(".csv"):
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)

    # Standardize column headers (lowercase, trimmed)
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Map expected columns
    brand_col = next((c for c in df.columns if "brand" in c or "hotel" in c or "name" in c), None)
    rev_col = next((c for c in df.columns if "rev" in c), None)
    order_col = next((c for c in df.columns if "order" in c or "booking" in c), None)
    email_col = next((c for c in df.columns if "gmail" in c or "email" in c or "mail" in c), None)

    if not all([brand_col, rev_col, order_col, email_col]):
        raise ValueError(
            f"Missing required columns. Found: {list(df.columns)}. "
            f"Expected brandname, revenue, Order, Boss Gmail."
        )

    records: List[HotelRecord] = []

    for idx, row in df.iterrows():
        raw_brand = row[brand_col]
        if pd.isna(raw_brand):
            continue

        brand_str = str(raw_brand).strip()
        # Filter out spreadsheet footer notes or non-hotel content
        if brand_str.lower().startswith("note:") or "testing purposes" in brand_str.lower():
            continue
        if len(brand_str) == 0:
            continue

        # Clean revenue
        raw_rev = row[rev_col]
        try:
            if pd.isna(raw_rev):
                clean_rev = 0.0
            else:
                clean_rev = float(str(raw_rev).replace(",", "").replace("$", "").strip())
        except (ValueError, TypeError):
            clean_rev = 0.0

        # Clean order
        raw_order = row[order_col]
        try:
            if pd.isna(raw_order):
                clean_order = 0
            else:
                clean_order = int(float(str(raw_order).replace(",", "").strip()))
        except (ValueError, TypeError):
            clean_order = 0

        # Clean email
        raw_email = row[email_col]
        clean_email = str(raw_email).strip() if not pd.isna(raw_email) else ""

        records.append(
            HotelRecord(
                brandname=brand_str,
                revenue=clean_rev,
                order=clean_order,
                email=clean_email,
                row_index=len(records) + 1  # 1-indexed relative to hotels
            )
        )

    return records
