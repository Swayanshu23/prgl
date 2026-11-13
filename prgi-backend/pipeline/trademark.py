"""
Trademark / brand conflict checker.
Cross-checks submitted title against a curated brand-name list.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict

from rapidfuzz import fuzz

DATA_DIR = Path(__file__).parent.parent / "data"

_DEFAULT_TRADEMARKS = [
    "Amazon", "Apple", "Google", "Meta", "Microsoft", "Samsung",
    "Reliance", "Tata", "Infosys", "Wipro", "Adani", "Airtel",
    "Jio", "Vodafone", "HDFC", "ICICI", "SBI", "Paytm", "Flipkart",
    "Snapdeal", "Myntra", "Swiggy", "Zomato", "Ola", "Uber", "Byju",
    "Unacademy", "Razorpay", "Zerodha", "PhonePe", "BharatPe", "CRED",
    "Meesho", "ShareChat", "IndiaMart", "PolicyBazaar", "Nykaa",
    "Boat", "Noise", "OnePlus", "Realme", "Oppo", "Vivo", "Xiaomi",
    "Motorola", "Nokia", "Lenovo", "Asus", "Dell", "HP", "LG", "Sony",
    "Panasonic", "Toyota", "Honda", "Maruti", "Hyundai", "Mahindra",
    "Bajaj", "Hero", "TVS", "Royal Enfield", "Forbes", "Bloomberg",
    "Reuters", "BBC", "CNN", "Al Jazeera", "NDTV", "Aaj Tak",
    "India Today", "ABP News", "Zee News", "Star India", "Sun TV",
    "Asianet", "ETV", "News18",
]


def _load_trademarks() -> List[str]:
    path = DATA_DIR / "trademarks.json"
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return _DEFAULT_TRADEMARKS


def check_trademark(tokens: List[str], full_title: str) -> Dict:
    """Flag if any part of the title closely matches a registered trademark."""
    brands = _load_trademarks()
    full_lower = full_title.lower()

    for brand in brands:
        b_lower = brand.lower()
        # Exact token match
        if b_lower in tokens:
            return {
                "name": "Trademark Conflict",
                "status": "fail",
                "val": brand,
                "issue": {
                    "type": "trademark",
                    "detail": f'Title contains trademarked brand name: "{brand}"',
                },
            }
        # Fuzzy partial match (only for longer brands to avoid false positives)
        if len(brand) >= 5:
            score = fuzz.partial_ratio(b_lower, full_lower)
            if score >= 92:
                return {
                    "name": "Trademark Conflict",
                    "status": "warn",
                    "val": f"≈ {brand} ({score}%)",
                    "issue": None,
                }

    return {"name": "Trademark Conflict", "status": "pass", "val": "Clear", "issue": None}
