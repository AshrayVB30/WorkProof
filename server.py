import os
import re
import io
import numpy as np
import requests
import logging
import difflib
import time
import copy
import pytesseract
from collections import defaultdict
from typing import Dict, Any
from PIL import Image, ImageEnhance

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Avoid Paddle oneDNN/PIR runtime crashes seen in some Linux container builds.
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_enable_pir_api", "0")
os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

from paddleocr import PaddleOCR

from backend.engine.new_field_definitions import FIELD_DEFINITIONS

try:
    import multipart  # type: ignore # noqa: F401
    MULTIPART_AVAILABLE = True
except Exception:
    MULTIPART_AVAILABLE = False


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Simple in-memory cache for repeated URL scrapes
# ---------------------------------------------------------
CACHE_TTL_SECONDS = 1800
CACHE_MAX_ITEMS = 64
SCRAPE_CACHE: dict[str, tuple[float, Dict[str, Any]]] = {}


def _cache_get(url: str) -> Dict[str, Any] | None:
    item = SCRAPE_CACHE.get(url)
    if not item:
        return None
    ts, data = item
    if time.time() - ts > CACHE_TTL_SECONDS:
        SCRAPE_CACHE.pop(url, None)
        return None
    return copy.deepcopy(data)


def _cache_set(url: str, data: Dict[str, Any]) -> None:
    if len(SCRAPE_CACHE) >= CACHE_MAX_ITEMS:
        oldest_key = min(SCRAPE_CACHE, key=lambda k: SCRAPE_CACHE[k][0])
        SCRAPE_CACHE.pop(oldest_key, None)
    SCRAPE_CACHE[url] = (time.time(), copy.deepcopy(data))




# ---------------------------------------------------------
# Initialize OCR engine
# ---------------------------------------------------------
OCR_ENGINE_MODE = os.getenv("OCR_ENGINE", "auto").strip().lower()
ocr_engine = None

if OCR_ENGINE_MODE == "tesseract":
    logger.info("OCR engine: tesseract-only mode")
else:
    import paddle
    logger.info("Loading PaddleOCR model...")
    try:
        paddle.set_flags({
            "FLAGS_use_mkldnn": False,
            "FLAGS_enable_pir_api": False,
            "FLAGS_enable_pir_in_executor": False,
        })
    except Exception:
        pass

    ocr_engine = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,
        cpu_threads=2,
        lang="en"
    )
    logger.info("PaddleOCR loaded successfully!")


# ---------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------
app = FastAPI(title="WorkProof OCR Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Serve Frontend (CORRECT CONFIG)
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Serve CSS + JS from /static/*
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# ---------------------------------------------------------
# Request Model
# ---------------------------------------------------------
class ScrapeRequest(BaseModel):
    url: str


# ---------------------------------------------------------
# Download Image
# ---------------------------------------------------------
def download_image(image_url: str) -> Image.Image:
    try:
        response = requests.get(
            image_url,
            timeout=20,
            headers={"User-Agent": "WorkProofOCR/1.0"},
        )
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGB")
    except Exception as e:
        logger.error(f"Failed to download image: {e}")
        raise HTTPException(status_code=400, detail="Invalid image URL")


def load_image_from_bytes(content: bytes) -> Image.Image:
    try:
        return Image.open(io.BytesIO(content)).convert("RGB")
    except Exception as e:
        logger.error(f"Failed to parse uploaded image: {e}")
        raise HTTPException(status_code=400, detail="Invalid uploaded image")


# ---------------------------------------------------------
# OCR Extraction
# ---------------------------------------------------------
def _normalize_text_key(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", text.lower())).strip()


def _normalize_label(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _field_key(field_name: str) -> str:
    return field_name.lower().replace(' ', '_').replace('/', '_').replace('-', '_')

KEY_TO_FIELD_NAME: Dict[str, str] = {_field_key(name): name for name in FIELD_DEFINITIONS.keys()}


def _build_label_catalog() -> Dict[str, str]:
    return {_normalize_label(field_name): field_name for field_name in FIELD_DEFINITIONS.keys()}


LABEL_CATALOG = _build_label_catalog()
LABEL_ALIASES = {
    "manufacturer": "Manufacture",
    "acnumber": "A/c Number",
    "beneficiary": "Beneficiary Identifier ID",
    "identifierid": "Beneficiary Identifier ID",
    "insno": "INS No",
    "sklldescription": "Skill Description",
}

SECTION_HEADERS = [
    "personal information",
    "account information",
    "investment information",
    "assets & last purchase information",
    "last purchase detail",
    "vehicle detail",
    "insurance detail",
    "legal advisors",
]

ADVISOR_SECTIONS = {
    "account advisor": "Account Advisor",
    "assets manager": "Assets Manager",
    "investment advisor": "Investment Advisor",
    "insurance manager": "Insurance Manager",
}

ADVISOR_SUBFIELDS = {
    "advisorid": "Advisor ID",
    "managerid": "Manager ID",
    "name": "Name",
    "contact": "Contact",
    "address": "Address",
}


def _find_best_label(line: str, current_section: str | None) -> str | None:
    raw = line.strip()
    if not raw:
        return None

    normalized = _normalize_label(raw)
    if not normalized:
        return None

    if normalized in LABEL_CATALOG:
        return LABEL_CATALOG[normalized]
    if normalized in LABEL_ALIASES:
        return LABEL_ALIASES[normalized]

    best_label = None
    best_ratio = 0.0

    # Full-field fuzzy matching.
    for norm_label, original in LABEL_CATALOG.items():
        if len(normalized) < 3 or len(norm_label) < 3:
            continue
        length_ratio = len(normalized) / max(len(norm_label), 1)
        if length_ratio < 0.60 or length_ratio > 1.40:
            continue
        ratio = difflib.SequenceMatcher(a=normalized, b=norm_label).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_label = original

    if best_ratio >= 0.88:
        return best_label

    # Section-scoped subfield matching for advisor blocks.
    if current_section:
        best_sub = None
        best_sub_ratio = 0.0
        for sub_norm, sub_name in ADVISOR_SUBFIELDS.items():
            ratio = difflib.SequenceMatcher(a=normalized, b=sub_norm).ratio()
            if ratio > best_sub_ratio:
                best_sub_ratio = ratio
                best_sub = sub_name

        if best_sub and best_sub_ratio >= 0.84:
            full = f"{current_section} - {best_sub}"
            if full in FIELD_DEFINITIONS:
                return full

    return None


def _looks_like_header_or_label(text: str, current_section: str | None) -> bool:
    cleaned = text.strip().lower()
    if not cleaned:
        return True

    for header in SECTION_HEADERS:
        if difflib.SequenceMatcher(a=cleaned, b=header).ratio() >= 0.86:
            return True

    for section in ADVISOR_SECTIONS.keys():
        if difflib.SequenceMatcher(a=cleaned, b=section).ratio() >= 0.86:
            return True

    return _find_best_label(text, current_section) is not None


def _is_date_like(value: str) -> bool:
    value_clean = value.strip().replace("+", "-").replace("#", "")
    if re.search(r"\b\d{1,2}[-/ ](?:[A-Za-z]{3,9}|\d{1,2})[-/ ]\d{2,4}\b", value_clean):
        return True
    if re.search(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b", value_clean.lower()) and re.search(r"\d", value_clean):
        return True
    return False


def _score_value(field_name: str, value: str) -> float:
    value = value.strip()
    if not value:
        return -1.0

    field_def = FIELD_DEFINITIONS.get(field_name, {})
    field_type = field_def.get("type", "text")
    score = 0.0

    # Penalize values that look like another label/header.
    if _normalize_label(value) in LABEL_CATALOG:
        score -= 4.0
    if any(difflib.SequenceMatcher(a=value.lower(), b=h).ratio() >= 0.88 for h in SECTION_HEADERS):
        score -= 4.0

    has_digits = bool(re.search(r"\d", value))
    has_letters = bool(re.search(r"[A-Za-z]", value))
    normalized_label = _normalize_label(field_name)
    normalized_value = _normalize_label(value)
    label_similarity = difflib.SequenceMatcher(a=normalized_value, b=normalized_label).ratio()
    if label_similarity >= 0.70:
        score -= 3.0

    if field_type == "email":
        if re.fullmatch(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", value):
            score += 8.0
        elif "@" in value:
            score += 4.0
        else:
            score -= 4.0
    elif field_type == "phone":
        digits = re.sub(r"\D", "", value)
        if len(digits) >= 7:
            score += 6.0
        else:
            score -= 3.0
    elif field_type == "currency":
        if re.fullmatch(r"[$€£]?\s*\d+(?:[.,]\d{1,2})?", value):
            score += 6.0
        elif has_digits:
            score += 2.0
        else:
            score -= 2.0
        if has_letters:
            score -= 3.0
    elif field_type == "number":
        if has_digits and not has_letters:
            score += 5.0
        elif has_digits:
            score += 2.0
        else:
            score -= 2.0
        if has_letters:
            score -= 3.0
    elif field_type == "date":
        if _is_date_like(value):
            score += 6.0
        else:
            score -= 3.0
    else:
        if len(value) >= 3:
            score += 1.5
        if has_letters:
            score += 1.0

    # Mild bonus for cleaner-looking values.
    if not re.search(r"[#*]{2,}", value):
        score += 0.3
    if len(value) > 64:
        score -= 1.0

    # Field-specific rules.
    compact = re.sub(r"[^A-Za-z0-9*]", "", value)

    if field_name == "Full Name" or field_name.endswith(" - Name"):
        words = re.findall(r"[A-Za-z]{2,}", value)
        if len(words) >= 2:
            score += 2.5
        else:
            score -= 4.0
        if "information" in value.lower():
            score -= 4.0
        if "," in value:
            score -= 2.0

    if field_name == "Customer ID":
        if re.fullmatch(r"\d{6,}", compact):
            score += 7.0
        elif has_digits:
            score += 2.0
        else:
            score -= 4.0

    if field_name == "SSN":
        digits = re.sub(r"\D", "", value)
        if re.fullmatch(r"\d{9}", digits):
            score += 7.0
        elif len(digits) >= 7:
            score += 3.0
        else:
            score -= 3.0

    if field_name == "A/c Number":
        if re.search(r"\*{2,}\d{2,}", value):
            score += 6.0
        elif has_digits:
            score += 2.0
        else:
            score -= 2.0

    if field_name == "Beneficiary Identifier ID":
        lower = value.lower().strip()
        if lower in {"insurance", "identifier", "identifier id", "beneficiary"}:
            score -= 6.0
        compact_b = re.sub(r"[^A-Za-z0-9]", "", value)
        if re.fullmatch(r"[A-Za-z0-9]{8,20}", compact_b):
            score += 4.5
        elif len(compact_b) < 6:
            score -= 2.0

    if field_name.endswith(" - Advisor ID") or field_name.endswith(" - Manager ID"):
        compact_id = re.sub(r"\s+", "", value)
        if _is_id_like(compact_id):
            score += 6.0
        elif re.fullmatch(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}", value):
            score -= 5.0
        else:
            score -= 2.0

    if field_name.endswith(" - Contact"):
        if _is_phone_like(value):
            score += 5.0
        else:
            score -= 3.0

    if field_name.endswith(" - Address"):
        if "," in value:
            score += 4.0
        elif _is_phone_like(value):
            score -= 4.0
        elif _is_id_like(value):
            score -= 3.0

    if field_name == "IBAN":
        iban = re.sub(r"[^A-Za-z0-9]", "", value).upper()
        if re.fullmatch(r"[A-Z]{2}[0-9A-Z]{10,34}", iban):
            score += 8.0
        elif re.fullmatch(r"[A-Z]{2}[0-9A-Z*]{10,34}", re.sub(r"[^A-Za-z0-9*]", "", value).upper()):
            score += 5.0
        else:
            score -= 4.0

    if field_name == "BIC":
        bic = re.sub(r"[^A-Za-z0-9]", "", value).upper()
        if re.fullmatch(r"[A-Z0-9]{8}([A-Z0-9]{3})?", bic):
            score += 6.0
        else:
            score -= 2.0

    if field_name in {"BTC Address", "ETH Address", "LTC Address"}:
        addr = re.sub(r"\s+", "", value)
        if len(addr) >= 16 and re.search(r"[A-Za-z0-9]", addr):
            score += 4.5
        else:
            score -= 3.0

    if field_name == "VIN":
        vin = re.sub(r"[^A-Za-z0-9]", "", value).upper()
        if re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin):
            score += 7.0
        elif len(vin) >= 12 and has_digits and has_letters:
            score += 2.0
        else:
            score -= 3.0

    if field_name == "Postal":
        if re.fullmatch(r"[A-Za-z0-9\- ]{3,10}", value) and has_digits:
            score += 4.0
        elif has_digits:
            score += 1.0
        else:
            score -= 2.5

    if field_name in {"Last Txn Amount", "Unit Price", "Coupon", "Invested Amount"} and has_letters:
        score -= 4.0

    return score


def _extract_ocr_lines(image: Image.Image) -> list[Dict[str, Any]]:
    if ocr_engine is None:
        return _extract_ocr_lines_tesseract(image)

    try:
        img_np = np.array(image.convert("RGB"))
        results = ocr_engine.predict(img_np)
        if not results:
            return []

        lines: list[Dict[str, Any]] = []
        for res in results:
            texts = res.get("rec_texts", [])
            scores = res.get("rec_scores", [])
            polys = res.get("dt_polys", [])
            for i, text in enumerate(texts):
                cleaned = str(text).strip()
                if not cleaned:
                    continue
                score = float(scores[i]) if i < len(scores) else 0.0
                if score < 0.20:
                    continue

                x_left = 0.0
                y_top = 0.0
                if i < len(polys):
                    poly = np.array(polys[i], dtype=np.float32)
                    if poly.size:
                        x_left = float(np.min(poly[:, 0]))
                        y_top = float(np.min(poly[:, 1]))

                lines.append({
                    "text": cleaned,
                    "score": score,
                    "x": x_left,
                    "y": y_top,
                })

        lines.sort(key=lambda d: (d["y"], d["x"]))
        return lines

    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        # Paddle can fail in some container runtimes; use Tesseract as fallback.
        fallback_lines = _extract_ocr_lines_tesseract(image)
        logger.info(f"Tesseract fallback lines: {len(fallback_lines)}")
        return fallback_lines


def _extract_ocr_lines_tesseract(image: Image.Image) -> list[Dict[str, Any]]:
    def _to_lines(img: Image.Image, psm: int) -> list[Dict[str, Any]]:
        data = pytesseract.image_to_data(
            img,
            output_type=pytesseract.Output.DICT,
            config=f"--oem 3 --psm {psm}",
        )
        count = len(data.get("text", []))
        grouped: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
        for i in range(count):
            text = str(data["text"][i]).strip()
            if not text:
                continue
            conf_raw = str(data.get("conf", ["-1"])[i]).strip()
            try:
                conf_val = float(conf_raw)
            except Exception:
                conf_val = -1.0
            if conf_val < 10:
                continue
            block = int(data.get("block_num", [0])[i])
            par = int(data.get("par_num", [0])[i])
            line = int(data.get("line_num", [0])[i])
            key = (block, par, line)
            grouped.setdefault(key, []).append({
                "text": text,
                "conf": conf_val,
                "x": float(data.get("left", [0])[i]),
                "y": float(data.get("top", [0])[i]),
            })

        out: list[Dict[str, Any]] = []
        for words in grouped.values():
            words = sorted(words, key=lambda w: w["x"])
            line_text = " ".join(w["text"] for w in words).strip()
            if not line_text:
                continue
            out.append({
                "text": line_text,
                "score": sum(w["conf"] for w in words) / (100.0 * len(words)),
                "x": min(w["x"] for w in words),
                "y": min(w["y"] for w in words),
            })
        return out

    try:
        rgb = image.convert("RGB")
        gray = rgb.convert("L")
        enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
        upscaled = enhanced.resize((rgb.width * 2, rgb.height * 2), Image.Resampling.BICUBIC)
        binarized = upscaled.point(lambda p: 255 if p > 165 else 0, mode="1").convert("L")

        merged: list[Dict[str, Any]] = []
        for img in (rgb, upscaled, binarized):
            merged.extend(_to_lines(img, psm=6))
            merged.extend(_to_lines(img, psm=11))

        # De-duplicate near-identical lines from multi-pass OCR.
        dedup: list[Dict[str, Any]] = []
        seen: set[tuple[str, int]] = set()
        for item in sorted(merged, key=lambda d: (-d["score"], d["y"], d["x"])):
            key = (re.sub(r"\s+", " ", item["text"].lower()).strip(), int(item["y"] // 4))
            if key in seen:
                continue
            seen.add(key)
            dedup.append(item)

        dedup.sort(key=lambda d: (d["y"], d["x"]))
        return dedup
    except Exception as fallback_error:
        logger.error(f"Tesseract fallback failed: {fallback_error}")
        return []


def _extract_ocr_lines_from_image(image: Image.Image, min_score: float = 0.20) -> list[Dict[str, Any]]:
    lines = _extract_ocr_lines(image)
    return [ln for ln in lines if ln.get("score", 0.0) >= min_score]


def _backfill_legal_advisors_from_image(image: Image.Image, fields: Dict[str, str]) -> None:
    missing_keys = [
        "account_advisor___contact",
        "account_advisor___address",
        "assets_manager___contact",
        "assets_manager___address",
        "investment_advisor___manager_id",
        "investment_advisor___name",
        "investment_advisor___contact",
        "investment_advisor___address",
        "insurance_manager___manager_id",
        "insurance_manager___name",
        "insurance_manager___contact",
        "insurance_manager___address",
    ]
    if all(fields.get(k, "").strip() for k in missing_keys):
        return

    w, h = image.size
    y0 = int(h * 0.66)
    legal_crop = image.crop((0, y0, w, h))

    # Fast fallback: single enhanced pass to avoid multiple OCR re-runs.
    enhanced = ImageEnhance.Contrast(legal_crop).enhance(1.6)
    upscaled = enhanced.resize((w * 2, max(2, (h - y0) * 2)), Image.Resampling.BICUBIC)
    lines = _extract_ocr_lines_from_image(upscaled, min_score=0.18)
    best_lines = [item["text"].strip() for item in lines if item["text"].strip()]

    if not best_lines:
        return

    temp_fields: Dict[str, str] = {}
    temp_scores: Dict[str, float] = {}
    _extract_advisor_fields_from_lines(best_lines, temp_fields, temp_scores)

    for key in missing_keys:
        if fields.get(key, "").strip():
            continue
        candidate = temp_fields.get(key, "").strip()
        if candidate:
            fields[key] = candidate


def extract_text_with_paddle(image: Image.Image) -> str:
    lines = _extract_ocr_lines(image)
    return "\n".join(line["text"] for line in lines)


def _rows_from_ocr_lines(ocr_lines: list[Dict[str, Any]], image_width: int) -> list[Dict[str, Any]]:
    if not ocr_lines:
        return []

    rows: list[list[Dict[str, Any]]] = []
    for line in sorted(ocr_lines, key=lambda d: (d["y"], d["x"])):
        if not rows:
            rows.append([line])
            continue
        prev_y = rows[-1][-1]["y"]
        if abs(line["y"] - prev_y) <= 12:
            rows[-1].append(line)
        else:
            rows.append([line])

    # Template has a narrow left label column; keep cutoff conservative.
    split_x = image_width * 0.28
    table_rows: list[Dict[str, Any]] = []
    for row in rows:
        row = sorted(row, key=lambda d: d["x"])
        left_parts = [r["text"] for r in row if r["x"] <= split_x]
        right_parts = [r["text"] for r in row if r["x"] > split_x]
        table_rows.append({
            "left": " ".join(left_parts).strip(),
            "right": " ".join(right_parts).strip(),
        })
    return table_rows


def _find_nearby_value(lines: list[str], label: str, max_lookahead: int = 3, max_lookbehind: int = 2) -> str:
    target = _normalize_label(label)
    for i, line in enumerate(lines):
        if _normalize_label(line) != target:
            continue
        candidates = []
        for j in range(max(0, i - max_lookbehind), min(len(lines), i + max_lookahead + 1)):
            if j == i:
                continue
            candidate = lines[j].strip()
            if not candidate:
                continue
            if _looks_like_header_or_label(candidate, None):
                continue
            candidates.append(candidate)
        if candidates:
            best = max(candidates, key=lambda c: _score_value(label, c))
            if _score_value(label, best) >= 0.5:
                return best
    return ""


def _find_value_after_label(lines: list[str], label: str, max_lookahead: int = 4) -> str:
    target = _normalize_label(label)
    for i, line in enumerate(lines):
        if _normalize_label(line) != target:
            continue
        for j in range(i + 1, min(len(lines), i + max_lookahead + 1)):
            candidate = lines[j].strip()
            if not candidate:
                continue
            if _looks_like_header_or_label(candidate, None):
                break
            return candidate
    return ""


def _find_personal_contact(lines: list[str]) -> str:
    upper = len(lines)
    for i, line in enumerate(lines):
        if _normalize_label(line) == "accountinformation":
            upper = i
            break
    for i in range(upper):
        if _normalize_label(lines[i]) == "contact" and i + 1 < upper:
            cand = lines[i + 1].strip()
            if cand and _is_phone_like(cand):
                return cand
    return ""


def _apply_template_fixes(fields: Dict[str, str], lines: list[str]) -> None:
    bond_name_after = _find_value_after_label(lines, "Bond Name")
    bond_class_after = _find_value_after_label(lines, "Bond Class")
    coupon_after = _find_value_after_label(lines, "Coupon")
    invested_after = _find_value_after_label(lines, "Invested Amount")
    if bond_name_after:
        fields["bond_name"] = bond_name_after
    if bond_class_after:
        fields["bond_class"] = bond_class_after
    if coupon_after and re.search(r"\d", coupon_after):
        fields["coupon"] = coupon_after
    if invested_after and re.search(r"\d", invested_after):
        fields["invested_amount"] = invested_after

    account_info_idx = -1
    for i, line in enumerate(lines):
        if _normalize_label(line) == "accountinformation":
            account_info_idx = i
            break

    essential_after_label = {
        "gender": "Gender",
        "dob": "DOB",
        "ssn": "SSN",
        "address_1": "Address 1",
        "email": "Email",
        "a_c_type": "A/c Type",
        "iban": "IBAN",
        "cc_no": "cC_No",
        "last_txn_amount": "Last Txn Amount",
        "maturity_date": "Maturity Date",
        "bond_name": "Bond Name",
        "bond_class": "Bond Class",
        "department": "Department",
        "ean13": "Ean13",
        "product_name": "Product Name",
        "buying_ipv4": "Buying IPv4",
        "buying_ipv6": "Buying IPv6",
        "type": "Type",
        "model": "Model",
        "manufacture": "Manufacturer",
        "vin": "VIN",
        "ins_no": "INS No.",
    }
    for k, label in essential_after_label.items():
        if not fields.get(k):
            v = _find_value_after_label(lines, label)
            if v:
                fields[k] = v

    # Values that often appear immediately before their labels.
    for i, line in enumerate(lines):
        norm = _normalize_label(line)
        if norm == "ein" and i - 1 >= 0 and not fields.get("ein"):
            prev = lines[i - 1].strip()
            if prev and not _looks_like_header_or_label(prev, None):
                fields["ein"] = prev
        if norm == "ean13" and i - 1 >= 0 and not fields.get("ean13"):
            prev = lines[i - 1].strip()
            if re.fullmatch(r"\d{8,14}", re.sub(r"\D", "", prev)):
                fields["ean13"] = prev
        if norm == "buyingipv4" and i - 1 >= 0 and not fields.get("buying_ipv4"):
            prev = lines[i - 1].strip()
            if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", prev):
                fields["buying_ipv4"] = prev
        if norm == "ethaddress" and not fields.get("eth_address"):
            for j in range(max(0, i - 2), i):
                prev = lines[j].strip()
                if prev and not _looks_like_header_or_label(prev, None):
                    if prev.startswith("0x") or prev.startswith("@x"):
                        fields["eth_address"] = prev.replace("@", "0")
                        break
        if norm == "bs" and not fields.get("bs"):
            v = _find_value_after_label(lines, "BS")
            if v and not _looks_like_header_or_label(v, None):
                fields["bs"] = v

    # Split-label pattern: Last Txn + Amount, with numeric value just above.
    for i, line in enumerate(lines):
        if _normalize_label(line) == "lasttxn" and i + 1 < len(lines) and _normalize_label(lines[i + 1]) == "amount":
            if i - 1 >= 0 and re.search(r"\d", lines[i - 1]):
                fields["last_txn_amount"] = lines[i - 1].strip()
                break
    if fields.get("last_txn_amount", "").lower().find("date") != -1:
        fields["last_txn_amount"] = ""

    # Split-label pattern: Invested + <value> + Amount.
    for i, line in enumerate(lines):
        if _normalize_label(line) == "invested":
            if i + 1 < len(lines) and re.search(r"\d", lines[i + 1]):
                fields["invested_amount"] = lines[i + 1].strip()
                break
        if _normalize_label(line) == "investedamount":
            v = _find_value_after_label(lines, line)
            if v and re.search(r"\d", v):
                fields["invested_amount"] = v
                break

    # Inline patterns in OCR text.
    for line in lines:
        m = re.match(r"(?i)^\s*last\s*txn\s*date\s+(.+)$", line.strip())
        if m and not fields.get("last_txn_date"):
            fields["last_txn_date"] = m.group(1).strip()
        m2 = re.match(r"(?i)^\s*maturity\s*date\s+(.+)$", line.strip())
        if m2 and not fields.get("maturity_date"):
            fields["maturity_date"] = m2.group(1).strip()

    if not fields.get("a_c_name"):
        v = _find_value_after_label(lines, "A/c Name")
        if v and not re.search(r"\*{2,}\d{2,}", v) and not _looks_like_header_or_label(v, None):
            fields["a_c_name"] = v

    if not fields.get("beneficiary_identifier_id"):
        v = _find_value_after_label(lines, "Beneficiary")
        if v and not _looks_like_header_or_label(v, None):
            fields["beneficiary_identifier_id"] = v

    if not re.search(r"\b[A-Za-z]{2,}\s+[A-Za-z]{2,}\b", fields.get("full_name", "")) or "information" in fields.get("full_name", "").lower():
        v = _find_nearby_value(lines, "Full Name")
        if v:
            fields["full_name"] = v

    # Prefer contact found before Account Information (Personal Info section).
    personal_contact = _find_personal_contact(lines)
    if personal_contact:
        fields["contact"] = personal_contact

    v_contact = _find_nearby_value(lines, "Contact")
    if not fields.get("contact") and v_contact and _is_phone_like(v_contact):
        fields["contact"] = v_contact

    if not re.fullmatch(r"\d{6,}", re.sub(r"\D", "", fields.get("customer_id", ""))):
        v = _find_nearby_value(lines, "Customer ID")
        if re.fullmatch(r"\d{6,}", re.sub(r"\D", "", v)):
            fields["customer_id"] = v

    if (not fields.get("address_2")) or fields.get("address_2", "").lower() == fields.get("address_1", "").lower():
        v = _find_value_after_label(lines, "Address 2")
        if v:
            fields["address_2"] = v

    if (not fields.get("city")) or re.search(r"\bapt\b|\bsuite\b", fields.get("city", ""), re.IGNORECASE):
        v = _find_value_after_label(lines, "city")
        if v:
            fields["city"] = v

    if not re.fullmatch(r"\d{9}", re.sub(r"\D", "", fields.get("ssn", ""))):
        v = _find_nearby_value(lines, "SSN")
        if re.fullmatch(r"\d{9}", re.sub(r"\D", "", v)):
            fields["ssn"] = v

    if not fields.get("a_c_number"):
        v = _find_nearby_value(lines, "A/c Number")
        if v:
            fields["a_c_number"] = v

    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", fields.get("coupon", "")):
        v = _find_nearby_value(lines, "Coupon")
        if re.fullmatch(r"\d+(?:\.\d{1,2})?", v):
            fields["coupon"] = v

    if not re.fullmatch(r"\d+(?:\.\d{1,2})?", fields.get("invested_amount", "")):
        v = _find_nearby_value(lines, "Invested Amount")
        if re.fullmatch(r"\d+(?:\.\d{1,2})?", v):
            fields["invested_amount"] = v

    if not fields.get("purchase_token"):
        v = _find_value_after_label(lines, "Purchase Token")
        if v:
            fields["purchase_token"] = v

    btc_v = _find_value_after_label(lines, "BTC Address")
    eth_v = _find_value_after_label(lines, "ETH Address")
    ltc_v = _find_value_after_label(lines, "LTC Address")
    if btc_v:
        fields["btc_address"] = btc_v
    if eth_v:
        fields["eth_address"] = eth_v
    if ltc_v:
        fields["ltc_address"] = ltc_v

    # Avoid misplacing BTC into ETH and IPv6 into purchase token.
    if fields.get("eth_address") and fields.get("btc_address") and fields["eth_address"] == fields["btc_address"]:
        fields["eth_address"] = ""
    if fields.get("purchase_token") and re.fullmatch(r"[0-9a-fA-F:.*]{8,}", fields["purchase_token"]):
        fields["purchase_token"] = ""

    # If Department looks like Ean13 and Ean13 is empty, move it.
    dep_digits = re.sub(r"\D", "", fields.get("department", ""))
    if len(dep_digits) in {12, 13, 14} and not fields.get("ean13"):
        fields["ean13"] = fields.get("department", "")
        fields["department"] = ""
    if fields.get("ean13") and fields.get("department"):
        ean_digits = re.sub(r"\D", "", fields.get("ean13", ""))
        dep_digits = re.sub(r"\D", "", fields.get("department", ""))
        if ean_digits and ean_digits == dep_digits:
            fields["department"] = ""

    # Prevent Bond Name from incorrectly taking Bond Class value.
    if fields.get("bond_name") and fields.get("bond_class"):
        if fields["bond_name"].strip() == fields["bond_class"].strip() and not bond_name_after:
            fields["bond_name"] = ""
    if _normalize_label(fields.get("bond_name", "")) in {"bondclass", "bondname"}:
        fields["bond_name"] = ""

    # Prevent Coupon from incorrectly taking Invested Amount value.
    if fields.get("coupon") and fields.get("invested_amount"):
        if fields["coupon"].strip() == fields["invested_amount"].strip() and not coupon_after:
            fields["coupon"] = ""

    # BS/EIN correction when BS accidentally picks EIN-like token.
    if fields.get("bs") and _is_id_like(fields["bs"]):
        for i, line in enumerate(lines):
            if _normalize_label(line) == "bs" and i - 1 >= 0:
                prev = lines[i - 1].strip()
                if prev and not _looks_like_header_or_label(prev, None):
                    fields["bs"] = prev
                    break
    if fields.get("bs") and fields.get("ein") and fields["bs"] == fields["ein"]:
        for i, line in enumerate(lines):
            if _normalize_label(line) == "bs" and i - 1 >= 0:
                prev = lines[i - 1].strip()
                if prev and not _looks_like_header_or_label(prev, None) and not _is_id_like(prev):
                    fields["bs"] = prev
                    break

    # Avoid section-title bleed into IPv6.
    if _normalize_label(fields.get("buying_ipv6", "")) in {"vehicle", "vehicledetail", "detail"}:
        fields["buying_ipv6"] = ""

    # VIN often appears just before Insurance label.
    if not fields.get("vin"):
        for i, line in enumerate(lines):
            if _normalize_label(line) == "insurance" and i - 1 >= 0:
                prev = re.sub(r"[^A-Za-z0-9]", "", lines[i - 1]).upper()
                if len(prev) == 17 and re.search(r"[A-Z]", prev) and re.search(r"\d", prev):
                    fields["vin"] = prev
                    break

    # Support OCR where label and value are in the same line.
    for line in lines:
        m = re.match(r"(?i)^\s*skll\s+description\s+(.+)$", line.strip())
        if m and m.group(1).strip():
            fields["skill_description"] = m.group(1).strip()
            break

    # Support OCR split pattern: "skll" + value lines + "Description".
    if not fields.get("skill_description"):
        for i, line in enumerate(lines):
            norm = _normalize_label(line)
            if norm not in {"skll", "skill", "sklldescription", "skilldescription"}:
                continue
            chunks = []
            for j in range(i + 1, min(len(lines), i + 6)):
                cand = lines[j].strip()
                cand_norm = _normalize_label(cand)
                if not cand:
                    continue
                if cand_norm == "description":
                    break
                if _looks_like_header_or_label(cand, None):
                    break
                chunks.append(cand)
            if chunks:
                fields["skill_description"] = " ".join(chunks).strip()
                break

    if not re.fullmatch(r"[A-Za-z0-9$]{8,}", re.sub(r"\s+", "", fields.get("account_advisor___advisor_id", ""))):
        v = _find_nearby_value(lines, "Advisor ID")
        if re.fullmatch(r"[A-Za-z0-9$]{8,}", re.sub(r"\s+", "", v)):
            fields["account_advisor___advisor_id"] = v

    if not fields.get("beneficiary_identifier_id"):
        v = _find_nearby_value(lines, "Beneficiary")
        if v and not _looks_like_header_or_label(v, None):
            fields["beneficiary_identifier_id"] = v

    # Remove placeholder label bleed-through in advisor sections.
    cleanup_keys = [
        "assets_manager___name",
        "assets_manager___contact",
        "investment_advisor___name",
        "investment_advisor___manager_id",
        "investment_advisor___contact",
        "insurance_manager___name",
    ]
    for key in cleanup_keys:
        val = fields.get(key, "")
        if val and _looks_like_header_or_label(val, None):
            fields[key] = ""


def _is_phone_like(value: str) -> bool:
    v = value.strip()
    if not v:
        return False
    # Allow digits, separators and extension markers only.
    if re.search(r"[^0-9\+\-\(\)\.\sxX]", v):
        return False
    digits = re.sub(r"\D", "", v)
    # Support masked phone patterns like +1 (xxx) xxx 3853.
    if len(digits) < 7:
        if "x" in v.lower() and len(digits) >= 4:
            return True
        return False
    # Must look like an actual phone format.
    return any(ch in v for ch in "+-(). xX")


def _is_id_like(value: str) -> bool:
    raw = value.strip()
    if not raw:
        return False
    if any(ch in raw for ch in [",", ".", ":", ";", "/"]):
        return False
    if " " in raw:
        return False
    if not re.fullmatch(r"[A-Za-z0-9$]{8,24}", raw):
        return False
    return bool(re.search(r"[A-Za-z]", raw) and re.search(r"\d", raw))


def _is_address_like(value: str) -> bool:
    v = value.strip()
    if not v:
        return False
    if "," in v:
        return True
    if _is_phone_like(v) or _is_id_like(v):
        return False
    words = re.findall(r"[A-Za-z]{2,}", v)
    return len(words) >= 2


def _extract_advisor_fields_from_lines(lines: list[str], fields: Dict[str, str], best_scores: Dict[str, float]) -> None:
    section_order = [
        ("Account Advisor", "Advisor ID"),
        ("Assets Manager", "Advisor ID"),
        ("Investment Advisor", "Manager ID"),
        ("Insurance Manager", "Manager ID"),
    ]
    section_indices: list[tuple[int, str, str]] = []
    for i, line in enumerate(lines):
        for section_name, id_label in section_order:
            if _normalize_label(line) == _normalize_label(section_name):
                section_indices.append((i, section_name, id_label))

    for idx, (start, section_name, id_label) in enumerate(section_indices):
        end = len(lines)
        if idx + 1 < len(section_indices):
            end = section_indices[idx + 1][0]
        block = [ln.strip() for ln in lines[start + 1:end] if ln.strip()]
        if not block:
            continue

        labels = {"advisorid", "managerid", "name", "contact", "address"}
        explicit: Dict[str, str] = {}

        i = 0
        while i < len(block):
            token = block[i]
            norm = _normalize_label(token)
            if norm in labels:
                vals: list[str] = []
                j = i + 1
                while j < len(block):
                    nxt = block[j].strip()
                    nxt_norm = _normalize_label(nxt)
                    if nxt_norm in labels:
                        break
                    if _normalize_label(nxt) in {_normalize_label(s[0]) for s in section_order}:
                        break
                    vals.append(nxt)
                    j += 1
                if vals:
                    clean_vals = [v for v in vals if not _looks_like_header_or_label(v, None)]
                    if norm == "address":
                        if clean_vals:
                            addr_val = " ".join(clean_vals).strip()
                            if i - 1 >= 0:
                                prev_addr = block[i - 1].strip()
                                if prev_addr and not _looks_like_header_or_label(prev_addr, None) and "," in prev_addr:
                                    if prev_addr not in addr_val:
                                        addr_val = f"{prev_addr} {addr_val}".strip()
                            explicit[norm] = addr_val
                        elif i - 1 >= 0:
                            prev_addr = block[i - 1].strip()
                            if prev_addr and not _looks_like_header_or_label(prev_addr, None):
                                explicit[norm] = prev_addr
                    elif norm in {"advisorid", "managerid"}:
                        if not clean_vals:
                            i = j
                            continue
                        v0 = clean_vals[0]
                        if _is_id_like(v0):
                            explicit[norm] = v0
                        elif "name" not in explicit and re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}", v0):
                            # OCR may place name under Manager/Advisor ID when ID is absent.
                            explicit["name"] = v0
                    else:
                        if not clean_vals:
                            i = j
                            continue
                        v0 = clean_vals[0]
                        if norm == "name" and _is_phone_like(v0):
                            explicit["contact"] = v0
                        else:
                            explicit[norm] = v0
                i = j
                continue
            i += 1

        # Heuristic fills for OCR rows where label/value order gets swapped.
        if "advisorid" not in explicit and "managerid" not in explicit and section_name != "Insurance Manager":
            for token in block:
                if _is_id_like(token):
                    explicit["advisorid" if id_label == "Advisor ID" else "managerid"] = token
                    break
        if section_name == "Insurance Manager" and "managerid" not in explicit:
            for token in block:
                if _is_id_like(token):
                    explicit["managerid"] = token
                    break
        if "name" not in explicit:
            for token in block:
                if _looks_like_header_or_label(token, None):
                    continue
                if _is_phone_like(token) or _is_id_like(token):
                    continue
                if "," in token:
                    continue
                if re.search(r"[A-Za-z]{2,}\s+[A-Za-z]{2,}", token):
                    explicit["name"] = token
                    break
        if "contact" not in explicit:
            for token in block:
                if _looks_like_header_or_label(token, None):
                    continue
                if _is_phone_like(token):
                    explicit["contact"] = token
                    break
        if "address" not in explicit:
            address_parts = [t for t in block if "," in t]
            if address_parts:
                explicit["address"] = " ".join(address_parts).strip()

        # OCR fallback: phone often appears right before "Contact" label.
        contact_idx = -1
        for ii, token in enumerate(block):
            if _normalize_label(token) == "contact":
                contact_idx = ii
                break
        if contact_idx > 0:
            prev_token = block[contact_idx - 1].strip()
            if (("contact" not in explicit) or (not _is_phone_like(explicit.get("contact", "")))) and _is_phone_like(prev_token):
                explicit["contact"] = prev_token

        # OCR fallback: Insurance Manager address may appear as trailing lines without label.
        if section_name == "Insurance Manager" and "address" not in explicit and contact_idx != -1:
            tail = [t.strip() for t in block[contact_idx + 1:] if t.strip()]
            tail = [t for t in tail if not _looks_like_header_or_label(t, None)]
            tail = [t for t in tail if t != explicit.get("name", "")]
            tail = [t for t in tail if not _is_phone_like(t)]
            if tail:
                if len(tail) > 1:
                    explicit["address"] = " ".join(tail).strip()
                elif _is_address_like(tail[0]):
                    explicit["address"] = tail[0]

        if section_name == "Insurance Manager" and "address" not in explicit:
            # Last-resort: keep trailing non-label token with mixed letters/digits
            # (e.g., OCR like "00943 ol1io") as address.
            rem = [t.strip() for t in block if t.strip() and not _looks_like_header_or_label(t, None)]
            rem = [t for t in rem if t not in {explicit.get("name", ""), explicit.get("contact", ""), explicit.get("managerid", "")}]
            rem = [t for t in rem if not _is_phone_like(t)]
            for cand in reversed(rem):
                if re.search(r"[A-Za-z]", cand) and (re.search(r"\d", cand) or "," in cand):
                    explicit["address"] = cand
                    break

        candidates = {
            f"{section_name} - {id_label}": explicit.get("advisorid" if id_label == "Advisor ID" else "managerid", ""),
            f"{section_name} - Name": explicit.get("name", ""),
            f"{section_name} - Contact": explicit.get("contact", ""),
            f"{section_name} - Address": explicit.get("address", ""),
        }
        for field_name, value in candidates.items():
            if not value:
                continue
            key = _field_key(field_name)
            score = _score_value(field_name, value)
            if score > best_scores.get(key, float("-inf")):
                fields[key] = value
                best_scores[key] = score

    # Final sanitation for advisor fields.
    for key, value in list(fields.items()):
        if key.endswith("___advisor_id") or key.endswith("___manager_id"):
            if value and (value.strip().lower() in {"advisor id", "manager id"} or not _is_id_like(value)):
                fields[key] = ""
        if key.endswith("___contact"):
            if value and not _is_phone_like(value):
                fields[key] = ""


def _final_field_cleanup(fields: Dict[str, str]) -> None:
    def _strip_prefix(value: str, label_patterns: list[str]) -> str:
        out = value.strip()
        for pat in label_patterns:
            out = re.sub(pat, "", out, flags=re.IGNORECASE).strip()
        return out

    full_name = fields.get("full_name", "").strip()
    if full_name and not re.fullmatch(r"[A-Za-z]{2,}(?:[ '-][A-Za-z]{2,})+", full_name):
        fields["full_name"] = ""

    b = fields.get("beneficiary_identifier_id", "").strip().lower()
    if b in {"insurance", "identifier", "identifier id", "beneficiary"}:
        fields["beneficiary_identifier_id"] = ""

    normalize_at_keys = {
        "iban", "bic", "isin", "vin", "customer_id",
        "account_advisor___advisor_id", "assets_manager___advisor_id",
        "investment_advisor___manager_id", "insurance_manager___manager_id",
    }
    for key in normalize_at_keys:
        val = fields.get(key, "")
        if val:
            fields[key] = val.replace("@", "0")

    # Personal contact must be phone-like.
    if fields.get("contact") and not _is_phone_like(fields["contact"]):
        fields["contact"] = ""

    if fields.get("customer_id"):
        cid = fields["customer_id"].strip()
        cid = re.sub(r"[^0-9]", "", cid)
        fields["customer_id"] = cid if len(cid) >= 8 else ""

    if fields.get("a_c_type"):
        clean_type = _strip_prefix(fields["a_c_type"], [r"^a\s*\/?\s*c\s*type[:\-]?\s*"])
        if _looks_like_header_or_label(clean_type, None):
            clean_type = ""
        fields["a_c_type"] = clean_type

    if fields.get("a_c_name"):
        clean_name = _strip_prefix(fields["a_c_name"], [r"^a\s*\/?\s*c\s*name[:\-]?\s*"])
        if _looks_like_header_or_label(clean_name, None):
            clean_name = ""
        if _normalize_label(clean_name) in {"invested", "amount", "investedamount"}:
            clean_name = ""
        fields["a_c_name"] = clean_name

    if fields.get("skill_description"):
        sk = fields["skill_description"]
        sk = re.sub(r"(?i)\b(name|contact|address|advisor id|manager id)\b.*$", "", sk).strip()
        if _looks_like_header_or_label(sk, None):
            sk = ""
        fields["skill_description"] = sk

    # Advisor names must look like names, not labels/IDs/phones.
    advisor_name_keys = [
        "account_advisor___name",
        "assets_manager___name",
        "investment_advisor___name",
        "insurance_manager___name",
    ]
    for k in advisor_name_keys:
        v = fields.get(k, "").strip()
        if not v:
            continue
        if v.lower() in {"advisor id", "manager id", "name", "contact", "address", "vame"}:
            fields[k] = ""
            continue
        if _looks_like_header_or_label(v, None) or _is_id_like(v) or _is_phone_like(v):
            fields[k] = ""

    # Manufacturer should not take short/placeholder tokens like "IN".
    mfg = fields.get("manufacture", "").strip()
    if mfg:
        if mfg.lower() in {"in", "manufacturer", "model", "type"}:
            fields["manufacture"] = ""
        elif re.fullmatch(r"[A-Za-z]{1,2}", mfg):
            fields["manufacture"] = ""

    # Model should not mirror manufacture or be placeholder garbage.
    model = fields.get("model", "").strip()
    if model:
        if model.lower() in {"model", "manufacturer", "type", "in"}:
            fields["model"] = ""
        elif fields.get("manufacture", "").strip() and model.lower() == fields["manufacture"].strip().lower():
            fields["model"] = ""
        elif re.fullmatch(r"[A-Za-z]{1,2}", model):
            fields["model"] = ""
        elif re.fullmatch(r"\d{1,2}", model):
            fields["model"] = ""

    # Ean13 must be mostly numeric barcode length.
    ean = fields.get("ean13", "").strip()
    if ean:
        digits = re.sub(r"\D", "", ean)
        if len(digits) not in {12, 13, 14}:
            fields["ean13"] = ""


# ---------------------------------------------------------
# Structured Field Extraction
# ---------------------------------------------------------
def extract_structured_fields(text: str, ocr_lines: list[Dict[str, Any]] | None = None, image_width: int | None = None) -> Dict[str, Any]:
    fields: Dict[str, str] = {}
    best_scores: Dict[str, float] = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    current_advisor_section: str | None = None
    label_occurrences: list[tuple[int, str, str | None]] = []

    # Fast path for fixed-form table layout (higher accuracy + faster than regex walk).
    if ocr_lines is not None and image_width is not None:
        rows = _rows_from_ocr_lines(ocr_lines, image_width)
        i = 0
        while i < len(rows):
            left = rows[i]["left"].strip()
            right = rows[i]["right"].strip()
            left_lower = left.lower()

            for section_norm, section_original in ADVISOR_SECTIONS.items():
                if difflib.SequenceMatcher(a=left_lower, b=section_norm).ratio() >= 0.86:
                    current_advisor_section = section_original
                    break

            field_name = _find_best_label(left, current_advisor_section) if left else None
            if field_name:
                candidates = []
                if right:
                    candidates.append(right)
                if i > 0:
                    prev_left = rows[i - 1]["left"].strip()
                    prev_right = rows[i - 1]["right"].strip()
                    if prev_right and not _find_best_label(prev_left, current_advisor_section):
                        candidates.append(prev_right)

                # Multi-line value continuation (mostly addresses).
                j = i + 1
                continuation_parts = []
                while j < len(rows):
                    next_left = rows[j]["left"].strip()
                    next_right = rows[j]["right"].strip()
                    if _find_best_label(next_left, current_advisor_section):
                        break
                    if next_left:
                        break
                    if next_right:
                        continuation_parts.append(next_right)
                        j += 1
                        continue
                    break

                if continuation_parts:
                    candidates.append(" ".join(continuation_parts).strip())
                    if right:
                        candidates.append((right + " " + " ".join(continuation_parts)).strip())

                key = _field_key(field_name)
                for candidate in candidates:
                    if not candidate:
                        continue
                    score = _score_value(field_name, candidate)
                    if score >= 0.5 and score > best_scores.get(key, float("-inf")):
                        fields[key] = candidate
                        best_scores[key] = score
            i += 1

        _apply_template_fixes(fields, lines)
        _extract_advisor_fields_from_lines(lines, fields, best_scores)
        placeholder_vals = {"advisor id", "manager id", "name", "contact", "address"}
        for bad_key in ["assets_manager___name", "investment_advisor___name"]:
            bad_val = fields.get(bad_key, "")
            if bad_val and (bad_val.strip().lower() in placeholder_vals or _looks_like_header_or_label(bad_val, None)):
                fields[bad_key] = ""
        for field_name in FIELD_DEFINITIONS.keys():
            key = _field_key(field_name)
            fields.setdefault(key, "")
        _final_field_cleanup(fields)
        fields["raw_text"] = text
        return fields

    # Fallback parser for non-template images.
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()

        # Keep advisor section context for short labels like "Advisor ID".
        for section_norm, section_original in ADVISOR_SECTIONS.items():
            if difflib.SequenceMatcher(a=line_lower, b=section_norm).ratio() >= 0.86:
                current_advisor_section = section_original
                break

        field_name = _find_best_label(line, current_advisor_section)
        if not field_name:
            # Handle "Label: Value" style lines.
            inline_match = re.match(r"^\s*([^:]+?)\s*[:\-]\s*(.+)\s*$", line)
            if inline_match:
                maybe_label = inline_match.group(1).strip()
                maybe_field = _find_best_label(maybe_label, current_advisor_section)
                if maybe_field:
                    candidate = inline_match.group(2).strip()
                    key = _field_key(maybe_field)
                    score = _score_value(maybe_field, candidate)
                    if score > best_scores.get(key, float("-inf")):
                        fields[key] = candidate
                        best_scores[key] = score
            continue
        label_occurrences.append((i, field_name, current_advisor_section))

    # Extract values from the region between one label and the next label.
    for idx, (line_idx, field_name, section_ctx) in enumerate(label_occurrences):
        next_line_idx = len(lines)
        if idx + 1 < len(label_occurrences):
            next_line_idx = label_occurrences[idx + 1][0]

        for j in range(line_idx + 1, next_line_idx):
            candidate = lines[j].strip()
            if not candidate:
                continue
            if _looks_like_header_or_label(candidate, section_ctx):
                continue

            key = _field_key(field_name)
            score = _score_value(field_name, candidate)
            if score < 0.5:
                continue
            if score > best_scores.get(key, float("-inf")):
                fields[key] = candidate
                best_scores[key] = score

        # Special fallback: some IDs appear immediately above label due OCR ordering.
        key = _field_key(field_name)
        if key not in fields and line_idx - 1 >= 0:
            prev_candidate = lines[line_idx - 1].strip()
            if prev_candidate and not _looks_like_header_or_label(prev_candidate, section_ctx):
                prev_score = _score_value(field_name, prev_candidate)
                if prev_score >= 3.5:
                    fields[key] = prev_candidate
                    best_scores[key] = prev_score

    # Regex fallback for any still-missing field.
    for field_name in FIELD_DEFINITIONS.keys():
        key = _field_key(field_name)
        if key in fields and fields[key]:
            continue
        pattern = rf"{re.escape(field_name)}\s*[:\-]?\s*(.+)"
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            candidate = match.group(1).strip()
            if not _looks_like_header_or_label(candidate, current_advisor_section) and _score_value(field_name, candidate) >= 0.5:
                fields[key] = candidate

    for field_name in FIELD_DEFINITIONS.keys():
        key = _field_key(field_name)
        fields.setdefault(key, "")

    _extract_advisor_fields_from_lines(lines, fields, best_scores)
    _final_field_cleanup(fields)
    fields["raw_text"] = text
    return fields


def _merge_structured_fields(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(primary)
    for key, secondary_val in secondary.items():
        if key == "raw_text":
            continue
        sec = str(secondary_val or "").strip()
        pri = str(merged.get(key, "") or "").strip()
        if not sec:
            continue
        if not pri:
            merged[key] = sec
            continue
        field_name = KEY_TO_FIELD_NAME.get(key)
        if not field_name:
            continue
        if _score_value(field_name, sec) > _score_value(field_name, pri):
            merged[key] = sec
    return merged


# ---------------------------------------------------------
# MAIN API
# ---------------------------------------------------------
async def process_image_url(url: str) -> Dict[str, Any]:
    if not url.strip():
        raise ValueError("URL is required")

    try:
        cached = _cache_get(url)
        if cached is not None:
            return cached

        image = download_image(url)
        result = process_image(image)
        _cache_set(url, result)
        return result

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise


def process_image(image: Image.Image) -> Dict[str, Any]:
    try:
        ocr_lines = _extract_ocr_lines(image)
        extracted_text = "\n".join(line["text"] for line in ocr_lines)

        if not extracted_text.strip():
            raise ValueError("No text detected")

        structured_data = extract_structured_fields(extracted_text, ocr_lines=ocr_lines, image_width=image.width)
        if OCR_ENGINE_MODE == "tesseract":
            text_only_data = extract_structured_fields(extracted_text, ocr_lines=None, image_width=None)
            structured_data = _merge_structured_fields(structured_data, text_only_data)
        _backfill_legal_advisors_from_image(image, structured_data)
        _final_field_cleanup(structured_data)

        return structured_data

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise


@app.post("/api/scrape")
def scrape(request: ScrapeRequest):

    if not request.url.strip():
        return {"status": "error", "detail": "URL is required"}

    try:
        image = download_image(request.url)
        structured_data = process_image(image)

        return {
            "status": "success",
            "method": "ocr",
            "data": structured_data,
            "metadata": {"unique_links": 0}
        }

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return {"status": "error", "detail": str(e)}



# ---------------------------------------------------------
# Run Server
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    print("Starting WorkProof Server at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
