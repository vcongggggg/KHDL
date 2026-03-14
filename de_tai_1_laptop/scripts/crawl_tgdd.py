# -*- coding: utf-8 -*-
"""
Crawler laptop từ Thế Giới Di Động (thegioididong.com).

Cách dùng:
  python crawl_tgdd.py

Kết quả: file CSV trong thư mục raw_data/ (đường dẫn tương đối so với thư mục project).

Lưu ý:
- Trang web có thể thay đổi HTML. Nếu lỗi hoặc thiếu dữ liệu, mở DevTools (F12)
  trên trang sản phẩm/laptop để xem lại class/selector và cập nhật trong code.
- Nên đặt DELAY giữa các request để tránh bị chặn (mặc định 2 giây).
"""

import os
import re
import sys
import time
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Đảm bảo import utils khi chạy từ thư mục project: python scripts/crawl_tgdd.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (
    parse_price_vnd,
    parse_ram_gb,
    parse_storage_gb,
    parse_screen_inch,
    safe_str,
    output_csv_path,
)

# --- Cấu hình ---
BASE_URL = "https://www.thegioididong.com"
LIST_URL = "https://www.thegioididong.com/laptop"
DELAY = 2  # giây giữa mỗi request
MAX_PAGES = 50  # giới hạn số trang danh sách (tăng để lấy >1000 sản phẩm)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}

# Thư mục project: cùng cấp với thư mục scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(PROJECT_DIR, "raw_data")


def get_soup(url):
    """GET URL và trả về BeautifulSoup. Trả về None nếu lỗi."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"[Lỗi] {url}: {e}")
        return None


def get_product_links_from_list(soup):
    """
    Lấy danh sách link sản phẩm từ 1 trang danh sách laptop.
    TGDĐ: sản phẩm nằm trong thẻ a có href dạng /laptop/ten-san-pham-xxxxx
    """
    links = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "/laptop/" in href and href.count("/") >= 3:
            full = urljoin(BASE_URL, href)
            if "thegioididong.com/laptop/" in full:
                links.add(full)
    return list(links)


def get_spec_row(spec_list, label_pattern):
    """Tìm dòng thông số có nhãn chứa label_pattern (không phân biệt hoa thường)."""
    if not spec_list:
        return None
    label_pattern = label_pattern.lower()
    for item in spec_list:
        text = (item.get_text() or "").lower()
        if label_pattern in text:
            return item.get_text().strip()
    return None


def parse_product_page(url):
    """
    Vào 1 trang chi tiết sản phẩm, trích xuất: tên, giá, và các thông số kỹ thuật.
    Trả về dict; nếu không lấy được giá hoặc tên thì vẫn trả về dict (để sau làm sạch).
    """
    soup = get_soup(url)
    if not soup:
        return None
    time.sleep(DELAY)

    row = {
        "url": url,
        "source": "thegioididong",
        "name": "",
        "price_vnd": None,
        "brand": "",
        "cpu_name": "",
        "ram_gb": None,
        "storage_gb": None,
        "storage_type": "",
        "screen_size_inch": None,
        "resolution": "",
        "gpu_name": "",
        "weight_kg": None,
        "os": "",
    }

    # --- Tên sản phẩm ---
    title_el = soup.find("h1") or soup.find("title")
    if title_el:
        row["name"] = safe_str(title_el.get_text(), 300)

    # --- Giá ---
    # TGDĐ thường có class chứa "price" hoặc "box-price"
    price_el = (
        soup.find("div", class_=re.compile(r"price|box-price", re.I))
        or soup.find("p", class_=re.compile(r"price", re.I))
    )
    if price_el:
        price_text = price_el.get_text()
        row["price_vnd"] = parse_price_vnd(price_text)

    # Nếu không tìm thấy theo class, thử tìm theo pattern số tiền VND
    if row["price_vnd"] is None:
        for elem in soup.find_all(string=re.compile(r"[\d.]+\s* triệu|[\d.,]+\s*₫")):
            p = parse_price_vnd(elem)
            if p and 1_000_000 <= p <= 500_000_000:
                row["price_vnd"] = p
                break

    # --- Bảng thông số (parameter list) ---
    # TGDĐ thường dùng ul.listparameter hoặc div chứa cặp nhãn - giá trị
    spec_container = (
        soup.find("ul", class_=re.compile(r"parameter|listparameter|spec", re.I))
        or soup.find("div", class_=re.compile(r"parameter|spec", re.I))
    )
    if spec_container:
        spec_text = spec_container.get_text()
        specs_lower = spec_text.lower()

        # RAM
        ram_match = re.search(r"(\d+)\s*gb\s*(?:ram|ddr)", specs_lower)
        if ram_match:
            row["ram_gb"] = int(ram_match.group(1))
        else:
            ram_val = get_spec_row(spec_container.find_all(["li", "div", "p"]), "ram")
            if ram_val:
                row["ram_gb"] = parse_ram_gb(ram_val)

        # Ổ cứng
        if "ssd" in specs_lower or "hdd" in specs_lower:
            row["storage_type"] = "SSD" if "ssd" in specs_lower else "HDD"
        storage_match = re.search(r"(\d+)\s*(?:gb|tb)", specs_lower)
        if storage_match:
            num = int(storage_match.group(1))
            row["storage_gb"] = num * 1024 if "tb" in specs_lower else num

        # Màn hình
        screen_match = re.search(r"(\d+\.?\d*)\s*[\"']?\s*inch", specs_lower)
        if screen_match:
            row["screen_size_inch"] = float(screen_match.group(1))

        # CPU - lấy dòng chứa "cpu" hoặc "bộ xử lý"
        for tag in spec_container.find_all(["li", "div", "p"]):
            t = (tag.get_text() or "").lower()
            if "cpu" in t or "bộ xử lý" in t or "chip" in t:
                row["cpu_name"] = safe_str(tag.get_text(), 200)
                break

        # Card đồ họa
        for tag in spec_container.find_all(["li", "div", "p"]):
            t = (tag.get_text() or "").lower()
            if "card màn hình" in t or "đồ họa" in t or "vga" in t or "gpu" in t:
                row["gpu_name"] = safe_str(tag.get_text(), 200)
                break

        # Cân nặng
        weight_match = re.search(r"(\d+\.?\d*)\s*kg", specs_lower)
        if weight_match:
            row["weight_kg"] = float(weight_match.group(1))

        # HĐH
        if "windows" in specs_lower:
            row["os"] = "Windows"
        elif "macos" in specs_lower or "mac os" in specs_lower:
            row["os"] = "macOS"

    # Brand: thường có trong breadcrumb hoặc tên sản phẩm (từ đầu)
    if not row["brand"] and row["name"]:
        brands = ["Asus", "Acer", "Dell", "HP", "Lenovo", "MSI", "LG", "Apple", "Microsoft", "Gigabyte", "Huawei"]
        for b in brands:
            if b.lower() in row["name"].lower():
                row["brand"] = b
                break

    return row


def crawl_list_page(page=1):
    """Lấy link sản phẩm từ trang danh sách (có phân trang)."""
    if page <= 1:
        url = LIST_URL
    else:
        url = f"{LIST_URL}?page={page}"
    soup = get_soup(url)
    if not soup:
        return []
    time.sleep(DELAY)
    return get_product_links_from_list(soup)


def main():
    print("Bắt đầu crawl laptop từ Thế Giới Di Động...")
    print(f"Thư mục lưu raw: {RAW_DIR}")

    all_links = []
    for page in range(1, MAX_PAGES + 1):
        links = crawl_list_page(page)
        if not links:
            print(f"Trang {page}: không lấy được link. Dừng phân trang.")
            break
        new_links = [l for l in links if l not in all_links]
        all_links.extend(new_links)
        print(f"Trang {page}: +{len(new_links)} link (tổng {len(all_links)})")
        if len(new_links) == 0:
            break

    print(f"\nTổng số link sản phẩm: {len(all_links)}")
    if len(all_links) == 0:
        print("Không có link nào. Kiểm tra lại selector trong get_product_links_from_list().")
        return

    # Trích xuất từng sản phẩm
    fieldnames = [
        "url", "source", "name", "price_vnd", "brand", "cpu_name", "ram_gb",
        "storage_gb", "storage_type", "screen_size_inch", "resolution",
        "gpu_name", "weight_kg", "os",
    ]
    out_path = output_csv_path(RAW_DIR, prefix="laptop_tgdd")
    count_ok = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for i, link in enumerate(all_links, 1):
            print(f"[{i}/{len(all_links)}] {link[:60]}...")
            row = parse_product_page(link)
            if row:
                out_row = {k: row.get(k) for k in fieldnames}
                for k in out_row:
                    if out_row[k] is None:
                        out_row[k] = ""
                    elif isinstance(out_row[k], str) and len(out_row[k]) > 500:
                        out_row[k] = safe_str(out_row[k], 500)
                writer.writerow(out_row)
                if row.get("price_vnd"):
                    count_ok += 1
            time.sleep(DELAY)

    print(f"\nHoàn thành. Đã lưu: {out_path}")
    print(f"Số dòng có giá: {count_ok} / {len(all_links)}")


if __name__ == "__main__":
    main()
