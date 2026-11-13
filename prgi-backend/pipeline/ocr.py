"""
OCR text extraction from uploaded images.
Uses pytesseract (local) — falls back gracefully if not installed.
Tesseract must be installed on the system: https://github.com/UB-Mannheim/tesseract/wiki

To install all Indian language packs, run (as Administrator):
    PowerShell: .\\setup_tesseract.ps1
"""
from __future__ import annotations
import io
import os
from typing import Optional

try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter

    # Windows: point pytesseract at the Tesseract binary
    for _tess_exe in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Users\secha\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
    ]:
        if os.path.exists(_tess_exe):
            pytesseract.pytesseract.tesseract_cmd = _tess_exe
            break

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# ---------------------------------------------------------------------------
# All Indian state / UT official languages supported by Tesseract tessdata.
# Languages that use Devanagari script (Konkani, Dogri, Bodo, Sindhi) are
# covered by "hin".  Latin-script languages (Mizo, Khasi, Garo, English-only
# states) are covered by "eng".
# ---------------------------------------------------------------------------
_INDIAN_LANGS = "+".join([
    "eng",  # all UTs, Arunachal Pradesh, Meghalaya, Nagaland, Mizoram
    "hin",  # Hindi — most states + Devanagari script (Konkani, Dogri, Bodo)
    "ben",  # Bengali — West Bengal, Tripura, Jharkhand
    "tel",  # Telugu — Andhra Pradesh, Telangana
    "mar",  # Marathi — Maharashtra, Goa
    "tam",  # Tamil — Tamil Nadu, Puducherry
    "urd",  # Urdu — J&K, Telangana, UP, Bihar
    "guj",  # Gujarati — Gujarat, Dadra & NH, Daman & Diu
    "kan",  # Kannada — Karnataka
    "mal",  # Malayalam — Kerala, Lakshadweep, Puducherry
    "ori",  # Odia — Odisha
    "pan",  # Punjabi (Gurmukhi) — Punjab, Chandigarh, Delhi
    "asm",  # Assamese — Assam
    "san",  # Sanskrit — classical / Devanagari
    "nep",  # Nepali — Sikkim
    # "mai" (Maithili) — not available in official tessdata
])


def _preprocess(img):
    """Enhance image contrast and sharpness for better OCR accuracy."""
    img = img.convert("L")                          # greyscale
    # Upscale small images — Tesseract performs poorly below ~300 DPI equivalent
    w, h = img.size
    if w < 1000:
        scale = max(2, 1000 // w)
        img = img.resize((w * scale, h * scale), Image.LANCZOS)
    img = ImageEnhance.Contrast(img).enhance(2.0)  # boost contrast
    img = img.filter(ImageFilter.SHARPEN)           # sharpen
    return img


def _collect_words(data: dict, min_conf: int = 10) -> tuple[list, list]:
    """Return (words, confidences) from pytesseract DICT output above min_conf."""
    words, confs = [], []
    for text, conf in zip(data["text"], data["conf"]):
        c = int(conf)
        if c > min_conf and text.strip():
            words.append(text.strip())
            confs.append(c)
    return words, confs


def extract_text(image_bytes: bytes, lang: str = _INDIAN_LANGS) -> dict:
    """
    Extract title text from image bytes.
    Returns {"text", "confidence", "available", "error"}

    Strategy:
    1. Try fast Devanagari+Latin pass (hin+eng) with PSM 3/6/11
    2. If result is empty, fall back to full Indian language set
    Keeping the first pass to 2 languages avoids confusion from 15 models.
    """
    if not OCR_AVAILABLE:
        return {
            "text": "", "confidence": 0.0, "available": False,
            "error": "pytesseract not installed. Run: pip install pytesseract Pillow",
        }

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = _preprocess(img)

        best_words: list = []
        best_confs: list = []

        # PSM modes tried in order:
        #   3  = fully automatic page segmentation (default, good for photos)
        #   6  = single uniform text block
        #   11 = sparse text — best for titles / mastheads
        psm_modes = [11, 3, 6]

        # Pass 1 — fast: Hindi + English covers most Indian newspaper titles
        for psm in psm_modes:
            data = pytesseract.image_to_data(
                img, lang="hin+eng",
                output_type=pytesseract.Output.DICT,
                config=f"--psm {psm}",
            )
            words, confs = _collect_words(data, min_conf=10)
            if len(words) > len(best_words):
                best_words, best_confs = words, confs

        # Pass 2 — full Indian language set (only if pass 1 yielded nothing)
        if not best_words:
            for psm in psm_modes:
                data = pytesseract.image_to_data(
                    img, lang=lang,
                    output_type=pytesseract.Output.DICT,
                    config=f"--psm {psm}",
                )
                words, confs = _collect_words(data, min_conf=5)
                if len(words) > len(best_words):
                    best_words, best_confs = words, confs

        extracted = " ".join(best_words)
        avg_conf  = round(sum(best_confs) / len(best_confs) / 100, 2) if best_confs else 0.0

        return {"text": extracted, "confidence": avg_conf, "available": True, "error": None}

    except Exception as e:
        return {"text": "", "confidence": 0.0, "available": True, "error": str(e)}
