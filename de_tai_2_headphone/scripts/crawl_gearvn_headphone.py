import os
import time
import csv
from typing import List, Dict

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://gearvn.com"
# Dùng collection tổng cho tai nghe máy tính. Có phân trang bằng ?page=
LISTING_URL_TEMPLATE = BASE_URL + "/collections/tai-nghe-may-tinh?page={page}"


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0 Safari/537.36"
    )
}


def fetch_html(url: str) -> str:
    """Download HTML of a URL, with basic error handling."""
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_product_list(html: str) -> List[Dict]:
    """
    Parse product blocks from a listing page.

    NOTE: CSS selectors có thể thay đổi theo thời gian.
    Nếu script không lấy được dữ liệu, hãy:
      - mở trang trong trình duyệt
      - inspect (F12) phần tử tên / giá / link sản phẩm
      - chỉnh lại các selector bên dưới cho phù hợp.
    """
    soup = BeautifulSoup(html, "lxml")

    # Thử nhiều selector khác nhau vì theme có thể đổi.
    selectors = [
        "div.product-item",
        "div.productitem",
        "div.product-grid-item",
        "div.product",  # fallback (có thể hơi rộng)
    ]
    product_nodes = []
    for sel in selectors:
        product_nodes = soup.select(sel)
        if product_nodes:
            break
    rows: List[Dict] = []

    for node in product_nodes:
        # Link chi tiết sản phẩm
        a_tag = node.select_one("a")
        if not a_tag or not a_tag.get("href"):
            continue
        url = BASE_URL + a_tag["href"]

        # Tên sản phẩm
        name_tag = node.select_one(".product-name")
        if not name_tag:
            name_tag = node.select_one(".product-title")
        name = name_tag.get_text(strip=True) if name_tag else ""

        # Giá hiển thị trên listing
        price_tag = node.select_one(".product-price")
        if not price_tag:
            price_tag = node.select_one(".price")
        price_text = price_tag.get_text(strip=True) if price_tag else ""

        rows.append(
            {
                "source": "gearvn",
                "url": url,
                "name": name,
                "price_raw": price_text,
            }
        )

    return rows


def clean_price_text(price_text: str) -> int:
    """Convert text price like '1.590.000₫' to integer VND."""
    if not price_text:
        return 0
    digits = (
        price_text.replace(".", "")
        .replace(",", "")
        .replace("₫", "")
        .replace("đ", "")
        .replace(" ", "")
    )
    try:
        return int(digits)
    except ValueError:
        return 0


def crawl_listing(max_pages: int = 10, delay_sec: float = 1.0) -> List[Dict]:
    """Crawl multiple listing pages and collect basic info."""
    all_rows: List[Dict] = []
    for page in range(1, max_pages + 1):
        url = LISTING_URL_TEMPLATE.format(page=page)
        print(f"Crawling listing page {page}: {url}")
        try:
            html = fetch_html(url)
        except Exception as exc:
            print(f"  -> error fetching page {page}: {exc}")
            break

        rows = parse_product_list(html)
        if not rows:
            print("  -> no more products found, stopping.")
            break

        for r in rows:
            r["price_vnd"] = clean_price_text(r.get("price_raw", ""))
        all_rows.extend(rows)

        time.sleep(delay_sec)

    return all_rows


def save_to_csv(rows: List[Dict], output_dir: str) -> str:
    """Save collected rows to a timestamped CSV file."""
    os.makedirs(output_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    filename = f"headphone_gearvn_{ts}.csv"
    path = os.path.join(output_dir, filename)

    if not rows:
        print("Không có dữ liệu để lưu.")
        return path

    fieldnames = sorted(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Đã lưu {len(rows)} dòng vào {path}")
    return path


def main():
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(project_dir, "raw_data")

    rows = crawl_listing(max_pages=8, delay_sec=1.0)
    save_to_csv(rows, raw_dir)


if __name__ == "__main__":
    main()

