# -*- coding: utf-8 -*-
"""
Crawl tai nghe/headphone tu CellphoneS (cellphones.com.vn).
Trang danh sach co HTML server-side, dung requests + BeautifulSoup la du.
"""

import os
import re
import time
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://cellphones.com.vn"
# Cac trang danh sach tai nghe (co the them trang khac)
LISTING_URLS = [
    "https://cellphones.com.vn/thiet-bi-am-thanh/tai-nghe/headphones.html",
    "https://cellphones.com.vn/thiet-bi-am-thanh/tai-nghe/co-day.html",
    "https://cellphones.com.vn/phu-kien/headphones.html",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}

DELAY = 1.0  # giay giua cac request
DELAY_DETAIL = 0.8  # giay giua moi trang chi tiet (tranh bi chan)


def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def clean_price_text(price_text: str) -> int:
    """Chuyen text gia '9.985.000d' -> int VND."""
    if not price_text:
        return 0
    digits = (
        price_text.replace(".", "")
        .replace(",", "")
        .replace("₫", "")
        .replace("đ", "")
        .replace(" ", "")
        .strip()
    )
    # Chi lay so dau tien (gia hien tai)
    match = re.search(r"\d+", digits)
    if match:
        return int(match.group(0))
    try:
        return int(digits)
    except ValueError:
        return 0


def _is_product_url(full_url: str) -> bool:
    """True neu la link trang chi tiet san pham, False neu la trang danh muc."""
    if "cellphones.com.vn" not in full_url or ".html" not in full_url:
        return False
    path = full_url.split("cellphones.com.vn")[-1].strip("/")
    # Danh muc: thiet-bi-am-thanh/tai-nghe/headphones.html hoac tai-nghe/jbl.html (slug ngan)
    if "/thiet-bi-am-thanh/tai-nghe/" in path and path.count("/") >= 2:
        return False
    if path.startswith("tai-nghe/") and len(path) < 25:
        return False
    # San pham: tai-nghe-chup-tai-sony-wh-1000xm6.html (slug dai, co dau -)
    if "tai-nghe-chup-tai" in path or "tai-nghe-bluetooth" in path or "tai-nghe-gaming" in path:
        return True
    if path.startswith("tai-nghe-") and path.endswith(".html") and len(path) > 25:
        return True
    return False


def parse_listing(html: str, page_url: str) -> list:
    """Tu HTML trang danh sach, trich link san pham + ten + gia (neu co)."""
    soup = BeautifulSoup(html, "lxml")
    rows = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        full_url = urljoin(BASE_URL, href)
        if full_url in seen or not _is_product_url(full_url):
            continue
        seen.add(full_url)

        # Ten: tu the h3 trong cung khoi hoac text cua link
        name = ""
        parent = a.parent
        for _ in range(6):
            if not parent:
                break
            h3 = parent.find("h3") or parent.find("h2")
            if h3:
                name = (h3.get_text() or "").strip()
                break
            parent = getattr(parent, "parent", None)
        if not name:
            name = (a.get_text() or "").strip()

        # Gia: trong khoi hoac trong text link (vd "9.985.000d")
        price_raw = ""
        if parent:
            for el in parent.find_all(class_=re.compile(r"price|gia|amount", re.I)):
                price_raw = (el.get_text() or "").strip()
                if re.search(r"\d", price_raw):
                    break
        if not price_raw:
            price_raw = (a.get_text() or "").strip()
        if price_raw:
            m = re.search(r"[\d.,]+\s*[đ₫]?", price_raw)
            if m:
                price_raw = m.group(0).strip()

        rows.append({
            "source": "cellphones",
            "url": full_url,
            "name": name[:300] if name else "",
            "price_raw": price_raw,
            "price_vnd": clean_price_text(price_raw),
        })
    return rows


def _extract_specs_from_text(text: str) -> dict:
    """
    Heuristic: tu toan bo text trang chi tiet, tim cac dong thong so chinh.
    Lay gia tri ngay dong sau label.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    specs = {
        "brand": "",
        "weight_gram": None,
        "connection": "",
        "battery_life_hours": None,
    }

    def get_after(label: str):
        for i, ln in enumerate(lines):
            if label.lower() in ln.lower():
                # lay dong tiep theo khac rong
                for j in range(i + 1, min(i + 5, len(lines))):
                    if lines[j]:
                        return lines[j]
        return ""

    # Hãng sản xuất
    brand = get_after("Hãng sản xuất")
    if not brand:
        # fallback: tim tu khoa thuong xuyen (Sony, JBL, ...)
        m = re.search(r"(Sony|JBL|Sennheiser|Bose|Hyperx|Anker|Baseus|Havit|Samsung|Xiaomi)",
                      text, flags=re.I)
        if m:
            brand = m.group(1)
    specs["brand"] = brand.strip()

    # Trọng lượng -> gram
    weight_txt = get_after("Trọng lượng")
    if weight_txt:
        m = re.search(r"([\d.,]+)\s*g", weight_txt.replace(",", "."), flags=re.I)
        if m:
            try:
                specs["weight_gram"] = float(m.group(1))
            except ValueError:
                pass

    # Cổng kết nối
    conn = get_after("Cổng kết nối")
    if conn:
        specs["connection"] = conn

    # Thời lượng pin (lay so lon nhat trong dong)
    batt_txt = get_after("Thời lượng sử dụng Pin")
    if batt_txt:
        nums = re.findall(r"\d+", batt_txt)
        if nums:
            try:
                specs["battery_life_hours"] = int(max(nums, key=int))
            except ValueError:
                pass

    return specs


def _infer_type_and_flags_from_name(name: str) -> dict:
    """Suy luan loai tai nghe va 1 so flag tu ten san pham."""
    s = (name or "").lower()
    info = {
        "type": "",
        "is_gaming": 0,
        "is_wireless": 0,
        "has_mic": 0,
    }
    if "gaming" in s or "game" in s:
        info["is_gaming"] = 1
    if "chụp tai" in s or "chup tai" in s or "over-ear" in s:
        info["type"] = "over-ear"
    elif "nhét tai" in s or "nhet tai" in s or "earbuds" in s:
        info["type"] = "in-ear"
    if "bluetooth" in s or "true wireless" in s or "wireless" in s:
        info["is_wireless"] = 1
    if "mic" in s or "micro" in s:
        info["has_mic"] = 1
    return info


def parse_detail_page(html: str, base_row: dict) -> dict:
    """
    Tu HTML trang chi tiet: lay gia + mot so thong so ky thuat.
    Tra ve dict da duoc cap nhat (khong tao row moi).
    """
    soup = BeautifulSoup(html, "lxml")
    price_vnd = base_row.get("price_vnd") or 0
    price_raw = base_row.get("price_raw") or ""

    # 1) Gia
    if not price_vnd:
        for sel in [
            ".product-info [class*='price']",
            ".product-detail [class*='price']",
            ".p-price",
            ".product-price",
            "[class*='price']",
            "span.price",
            "div.price",
        ]:
            els = soup.select(sel)
            for el in els:
                txt = (el.get_text() or "").strip()
                if re.search(r"\d{2,}[\d.,]*\s*[đ₫]?", txt):
                    m = re.search(r"([\d.,]+)\s*[đ₫]?", txt)
                    if m:
                        price_raw = m.group(0).strip()
                        price_vnd = clean_price_text(price_raw)
                        if price_vnd > 10000:
                            break
            if price_vnd > 0:
                break

        # Fallback to any currency-like pattern
        if price_vnd <= 0:
            text_all = soup.get_text(" ", strip=True)
            for m in re.finditer(r"([\d]{1,3}(?:\.[\d]{3}){2,})\s*[đ₫]?", text_all):
                raw = m.group(0).strip()
                p = clean_price_text(raw)
                if 100000 <= p <= 50000000:
                    price_vnd = p
                    price_raw = raw
                    break

    base_row["price_vnd"] = price_vnd
    base_row["price_raw"] = price_raw

    # 2) Thong so ky thuat tu text
    specs = _extract_specs_from_text(soup.get_text("\n", strip=True))
    for k, v in specs.items():
        base_row[k] = v

    # 3) Suy luan tu ten
    inferred = _infer_type_and_flags_from_name(base_row.get("name", ""))
    for k, v in inferred.items():
        base_row[k] = v

    return base_row


def crawl_all(fetch_detail_for_price: bool = True) -> list:
    all_rows = []
    seen_urls = set()

    for url in LISTING_URLS:
        print("Crawling listing:", url)
        try:
            html = fetch_html(url)
        except Exception as e:
            print("  -> Loi:", e)
            continue
        rows = parse_listing(html, url)
        for r in rows:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_rows.append(r)
        print("  -> Lay duoc", len(rows), "san pham, tong:", len(all_rows))
        time.sleep(DELAY)

    # Vao tung trang chi tiet de lay gia (neu tren listing khong co)
    if fetch_detail_for_price and all_rows:
        need_price = [r for r in all_rows if not r.get("price_vnd")]
        if need_price:
            print("Vao", len(need_price), "trang chi tiet de lay gia...")
        for i, row in enumerate(all_rows):
            if row.get("price_vnd"):
                continue
            try:
                html = fetch_html(row["url"])
                row = parse_detail_page(html, row)
                all_rows[i] = row
                if (i + 1) % 5 == 0:
                    print("  ", i + 1, "/", len(all_rows))
            except Exception:
                # bo qua neu co loi tren 1 trang chi tiet
                pass
            time.sleep(DELAY_DETAIL)

    return all_rows


def save_csv(rows: list, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"headphone_cellphones_{ts}.csv")
    if not rows:
        print("Khong co du lieu de luu.")
        return path
    # Sap xep truong de de xem trong CSV
    keys = [
        "source",
        "url",
        "name",
        "price_raw",
        "price_vnd",
        "brand",
        "type",
        "is_gaming",
        "is_wireless",
        "has_mic",
        "connection",
        "battery_life_hours",
        "weight_gram",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print("Da luu", len(rows), "dong vao", path)
    return path


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(os.path.dirname(script_dir), "raw_data")
    rows = crawl_all()
    save_csv(rows, raw_dir)


if __name__ == "__main__":
    main()
