# -*- coding: utf-8 -*-
"""
Tiện ích dùng chung cho crawler và xử lý dữ liệu laptop.
"""

import re
import os
from datetime import datetime


def extract_number(text):
    """Lấy số đầu tiên (int hoặc float) từ chuỗi. Ví dụ: '16 GB' -> 16, '15.6 inch' -> 15.6."""
    if not text or not isinstance(text, str):
        return None
    text = text.replace(",", ".")
    match = re.search(r"[\d]+\.?[\d]*", text)
    return float(match.group()) if match else None


def parse_price_vnd(text):
    """Chuyển chuỗi giá VND sang số. Ví dụ: '15.990.000' -> 15990000."""
    if not text:
        return None
    s = re.sub(r"[^\d]", "", str(text))
    return int(s) if s else None


def parse_ram_gb(text):
    """Từ chuỗi mô tả RAM (vd: '8 GB', '16 GB DDR4') trả về số GB."""
    if not text:
        return None
    n = extract_number(text)
    if n is None:
        return None
    text_lower = text.lower()
    if "tb" in text_lower or "tb" in text_lower:
        return int(n * 1024) if n < 100 else int(n)  # Terabyte
    return int(n) if n < 1000 else int(n / 1024)


def parse_storage_gb(text):
    """Từ chuỗi dung lượng ổ cứng (vd: '256 GB SSD', '1 TB') trả về tổng GB (số)."""
    if not text:
        return None
    n = extract_number(text)
    if n is None:
        return None
    text_lower = text.lower()
    if "tb" in text_lower:
        return int(n * 1024) if n < 100 else int(n)
    return int(n) if n < 10000 else None


def parse_screen_inch(text):
    """Từ chuỗi kích thước màn hình (vd: '15.6 inch') trả về số inch."""
    return extract_number(text) if text else None


def safe_str(val, max_len=500):
    """Chuẩn hóa giá trị để ghi CSV: None -> '', str cắt max_len."""
    if val is None:
        return ""
    s = str(val).strip()
    s = s.replace("\r", " ").replace("\n", " ")
    return s[:max_len] if len(s) > max_len else s


def ensure_dir(path):
    """Tạo thư mục nếu chưa tồn tại."""
    os.makedirs(path, exist_ok=True)


def output_csv_path(output_dir, prefix="laptop", suffix=".csv"):
    """Tạo đường dẫn file CSV với timestamp. Ví dụ: raw_data/laptop_tgdd_20260306_143022.csv"""
    ensure_dir(output_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(output_dir, f"{prefix}_{ts}{suffix}")
