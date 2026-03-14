# -*- coding: utf-8 -*-
"""
Crawler mẫu laptop từ FPT Shop (fptshop.com.vn).
Cấu trúc tương tự crawl_tgdd.py; cần chỉnh lại URL và selector theo trang FPT.

Cách dùng (từ thư mục scripts):
  python crawl_fpt.py
"""

import os
import sys

# Đảm bảo có thể import utils khi chạy từ thư mục scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import parse_price_vnd, safe_str, output_csv_path

BASE_URL = "https://fptshop.com.vn"
LIST_URL = "https://fptshop.com.vn/may-tinh-xach-tay"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
RAW_DIR = os.path.join(PROJECT_DIR, "raw_data")
DELAY = 2
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
}


def get_soup(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"[Lỗi] {url}: {e}")
        return None


def get_product_links(soup):
    """Lấy link sản phẩm từ trang danh sách. Cần chỉnh selector theo HTML thực tế của FPT."""
    links = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "/may-tinh-xach-tay/" in href and href != "/may-tinh-xach-tay/":
            links.add(urljoin(BASE_URL, href))
    return list(links)


def parse_product(url):
    """Trích xuất thông tin 1 sản phẩm. Cần chỉnh theo cấu trúc trang FPT."""
    soup = get_soup(url)
    if not soup:
        return None
    time.sleep(DELAY)
    row = {
        "url": url,
        "source": "fptshop",
        "name": "",
        "price_vnd": None,
        "brand": "",
        "cpu_name": "",
        "ram_gb": None,
        "storage_gb": None,
        "screen_size_inch": None,
        "gpu_name": "",
        "os": "",
    }
    h1 = soup.find("h1")
    if h1:
        row["name"] = h1.get_text().strip()[:300]
    # Giá: mở trang FPT, F12 tìm class/selector chứa giá và cập nhật ở đây
    price_el = soup.find(class_=lambda c: c and "price" in str(c).lower())
    if price_el:
        row["price_vnd"] = parse_price_vnd(price_el.get_text())
    return row


def main():
    print("Crawler FPT Shop - mẫu. Cần chỉnh selector theo trang hiện tại.")
    soup = get_soup(LIST_URL)
    if not soup:
        return
    links = get_product_links(soup)
    print(f"Số link tìm thấy: {len(links)}")
    if not links:
        return
    fieldnames = list(parse_product(links[0]).keys()) if parse_product(links[0]) else []
    out_path = output_csv_path(RAW_DIR, prefix="laptop_fpt")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for i, link in enumerate(links[:20], 1):  # Mẫu 20 sản phẩm
            row = parse_product(link)
            if row:
                writer.writerow({k: row.get(k) or "" for k in fieldnames})
    print(f"Đã lưu mẫu: {out_path}")


if __name__ == "__main__":
    main()
