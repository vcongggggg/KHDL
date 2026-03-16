import os
import re
import time
import csv
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Selenium (de nhan nut 'Xem thêm sản phẩm' tren trang danh muc)
SELENIUM_AVAILABLE = False
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_AVAILABLE = True
except ImportError:
    pass

BASE_URL = "https://phongvu.vn"

# Mot so URL danh muc / brand tai nghe tren Phong Vu
LISTING_URLS = [
    # Trang tong hop tai nghe
    "https://phongvu.vn/c/tai-nghe",
]

MAX_PAGES_PER_LISTING = int(os.environ.get("PHONGVU_MAX_PAGES", "10"))  # khong dung nua (Selenium), giu de tuong thich
MAX_ITEMS = int(os.environ.get("PHONGVU_MAX_ITEMS", "400"))
PHONGVU_LOAD_MORE_CLICKS = int(os.environ.get("PHONGVU_LOAD_MORE_CLICKS", "200"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}

DELAY = 1.0
DELAY_DETAIL = 0.8


def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def clean_price_text(price_text: str) -> int:
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
    m = re.search(r"\d+", digits)
    if m:
        try:
            return int(m.group(0))
        except ValueError:
            return 0
    try:
        return int(digits)
    except ValueError:
        return 0


def _infer_from_name(name: str) -> Dict:
    s = (name or "").lower()
    info = {
        "brand": "",
        "type": "",
        "is_gaming": 0,
        "is_wireless": 0,
        "has_mic": 0,
    }
    # brand: chuoi chu cai dau tien
    m = re.search(r"\b([a-zA-Z]{3,})\b", name or "")
    if m:
        info["brand"] = m.group(1)
    if "gaming" in s:
        info["is_gaming"] = 1
    if "wireless" in s or "bluetooth" in s or "true wireless" in s:
        info["is_wireless"] = 1
    if "mic" in s or "micro" in s:
        info["has_mic"] = 1
    if "over-ear" in s or "chụp tai" in s or "chup tai" in s:
        info["type"] = "over-ear"
    elif "in-ear" in s or "nhét tai" in s or "nhet tai" in s:
        info["type"] = "in-ear"
    return info


def _url_for_page(base: str, page: int) -> str:
    if page == 1:
        return base
    # Phong Vu su dung query ?page=
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}page={page}"


def _crawl_listing_with_load_more(listing_url: str) -> str:
    """
    Mo trang danh muc bang Selenium, cuon xuong va nhan nut
    'Xem thêm sản phẩm' (div.button-text ...) nhieu lan de load
    nhieu san pham nhat, tra ve HTML cuoi cung.
    """
    if not SELENIUM_AVAILABLE:
        print("  (Can selenium + webdriver-manager. Dung requests lay 1 trang bang requests.)")
        return fetch_html(listing_url)

    print("  Mo Chrome, load trang danh muc PhongVu...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(listing_url)
        wait = WebDriverWait(driver, 15)
        last_count = 0
        for i in range(PHONGVU_LOAD_MORE_CLICKS):
            # Cuon xuong cuoi trang truoc khi tim nut
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.8)
            try:
                btn = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//div[contains(@class,'button-text') and contains(., 'Xem thêm sản phẩm')]",
                        )
                    )
                )
            except Exception:
                # Khong con nut -> co the da load het
                break
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", btn)
            except Exception:
                break
            time.sleep(1.2)
            products = driver.find_elements(By.CSS_SELECTOR, "[data-view-id='product_container'], .css-1p8n9i2, .css-13l3l78")
            count = len(products)
            if count > last_count:
                last_count = count
                if (i + 1) % 5 == 0:
                    print(f"    Nhan 'Xem them san pham' {i+1} lan, so san pham: {count}")
            else:
                break
        print("  Tong so san pham nhin thay tren danh muc PhongVu:", last_count)
        return driver.page_source
    finally:
        if driver:
            driver.quit()


def parse_listing(html: str, page_url: str) -> List[Dict]:
    """
    Tu HTML trang danh sach Phong Vu, trich card san pham.
    Co the can tinh chinh selector neu site thay doi.
    """
    soup = BeautifulSoup(html, "lxml")
    rows: List[Dict] = []

    # Card san pham Phong Vu (theo HTML ban gui: div.product-card ...)
    product_cards = soup.select(
        ".product-card, [data-view-id='product_container'], .css-1p8n9i2, .css-13l3l78"
    )
    for card in product_cards:
        a = card.find("a", href=True)
        if not a:
            continue
        href = a.get("href", "")
        full_url = urljoin(BASE_URL, href)

        name_el = card.select_one("h3.css-1xdyrhj, h3, h4, .css-1ehqh5q")
        name = (name_el.get_text() if name_el else a.get_text() or "").strip()

        price_raw = ""
        # Gia hien tai: .att-product-detail-latest-price
        price_el = card.select_one(".att-product-detail-latest-price, .css-1u04k9e, .css-13k0vsy, .css-1b0tqk2")
        if price_el:
            price_raw = (price_el.get_text() or "").strip()
        m = re.search(r"[\d.,]+\s*[đ₫]?", price_raw)
        if m:
            price_raw = m.group(0).strip()

        row = {
            "source": "phongvu",
            "url": full_url,
            "name": name[:300] if name else "",
            "price_raw": price_raw,
            "price_vnd": clean_price_text(price_raw),
            "brand": "",
            "type": "",
            "is_gaming": 0,
            "is_wireless": 0,
            "has_mic": 0,
            "connection": "",
            "battery_life_hours": "",
            "weight_gram": "",
        }
        row.update(_infer_from_name(name))
        rows.append(row)

    return rows


def _extract_specs_from_text(text: str) -> Dict:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    specs: Dict = {
        "brand": "",
        "connection": "",
        "battery_life_hours": "",
        "weight_gram": "",
    }

    def get_after_any(labels):
        for i, ln in enumerate(lines):
            for label in labels:
                if label.lower() in ln.lower():
                    for j in range(i + 1, min(i + 6, len(lines))):
                        if lines[j]:
                            return lines[j]
        return ""

    brand = get_after_any(["Thương hiệu", "Hãng sản xuất"])
    if not brand:
        m = re.search(
            r"(Sony|JBL|Sennheiser|Bose|Hyperx|HyperX|Anker|Baseus|Havit|Samsung|Xiaomi|Razer|Logitech|Steelseries)",
            text,
            flags=re.I,
        )
        if m:
            brand = m.group(1)
    specs["brand"] = brand.strip()

    conn_txt = get_after_any(["Kết nối", "Chuẩn kết nối", "Cổng kết nối"])
    if conn_txt:
        specs["connection"] = conn_txt

    batt_txt = get_after_any(["Thời lượng pin", "Thời gian sử dụng", "Thời gian chơi nhạc"])
    if batt_txt:
        nums = re.findall(r"\d+", batt_txt)
        if nums:
            specs["battery_life_hours"] = max(nums, key=int)

    weight_txt = get_after_any(["Trọng lượng"])
    if weight_txt:
        m = re.search(r"([\d.,]+)\s*g", weight_txt.replace(",", "."), flags=re.I)
        if m:
            specs["weight_gram"] = m.group(1)

    return specs


def crawl_all() -> List[Dict]:
    all_rows: List[Dict] = []
    seen_urls = set()

    for base in LISTING_URLS:
        if len(all_rows) >= MAX_ITEMS:
            print(f"Dat {MAX_ITEMS} san pham, dung crawl PhongVu.")
            break
        print("Crawling (Selenium):", base)
        try:
            html = _crawl_listing_with_load_more(base)
        except Exception as e:
            print("  -> Loi:", e)
            continue
        rows = parse_listing(html, base)
        new_count = 0
        for r in rows:
            u = (r.get("url") or "").strip()
            if u and u not in seen_urls:
                seen_urls.add(u)
                all_rows.append(r)
                new_count += 1
                if len(all_rows) >= MAX_ITEMS:
                    break
        print(f"  -> Danh muc nay: {len(rows)} san pham, moi: {new_count} | Tong: {len(all_rows)}")
        time.sleep(DELAY)

    # Vao trang chi tiet de lay thong so
    if all_rows:
        print("\nVao trang chi tiet PhongVu de lay thong so...")
        for i, row in enumerate(all_rows):
            try:
                html = fetch_html(row["url"])
                soup = BeautifulSoup(html, "lxml")
                text = soup.get_text("\n", strip=True)
                specs = _extract_specs_from_text(text)
                for k, v in specs.items():
                    if v:
                        row[k] = v
                all_rows[i] = row
                if (i + 1) % 10 == 0:
                    print("  ", i + 1, "/", len(all_rows))
            except Exception:
                pass
            time.sleep(DELAY_DETAIL)

    return all_rows


def save_csv(rows: List[Dict], out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"headphone_phongvu_{ts}.csv")
    if not rows:
        print("Khong co du lieu de luu.")
        return path
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
    return rows


if __name__ == "__main__":
    main()

