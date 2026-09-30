from __future__ import annotations

import hashlib
import re

PII_PATTERNS: dict[str, str] = {
    # Email: hỗ trợ tên miền phụ, dấu +, dấu chấm
    "email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+",
    # Thẻ tín dụng/ghi nợ: 16 số (4-4-4-4) hoặc 15 số (Amex 4-6-5), có hoặc không có dấu gạch/khoảng trắng
    "credit_card": r"(?<!\d)(?:\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}|\d{4}[- ]?\d{6}[- ]?\d{5})(?!\d)",
    # CCCD: 12 chữ số viết liền hoặc chia cụm 3-3-3-3 hoặc 4-4-4
    "cccd": r"(?<!\d)(?:\d{12}|\d{3}[- ]\d{3}[- ]\d{3}[- ]\d{3}|\d{4}[- ]\d{4}[- ]\d{4})(?!\d)",
    # SĐT Việt Nam: đầu 0 hoặc +84 hoặc (+84) kèm 9 chữ số di động
    "phone_vn": r"(?<!\d)(?:\+84|0|\(\+84\))(?:[ .-]?\d){9}(?!\d)",
    # Bổ sung Hộ chiếu VN (Passport): 1 chữ cái in hoa (B, C, G, K, P,...) theo sau là 7-8 chữ số
    "passport": r"(?<![A-Za-z0-9])[A-Z]\d{7,8}(?![A-Za-z0-9])",
}


def scrub_text(text: str) -> str:
    safe = text
    for name, pattern in PII_PATTERNS.items():
        safe = re.sub(pattern, f"[REDACTED_{name.upper()}]", safe)
    return safe


def summarize_text(text: str, max_len: int = 80) -> str:
    safe = scrub_text(text).strip().replace("\n", " ")
    return safe[:max_len] + ("..." if len(safe) > max_len else "")


def hash_user_id(user_id: str) -> str:
    return hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:12]
