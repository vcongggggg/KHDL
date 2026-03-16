# -*- coding: utf-8 -*-
"""
Crawl tai nghe/headphone tu CellphoneS (cellphones.com.vn).
- Danh muc: requests + BeautifulSoup.
- Trang tim kiem: dung Selenium click nut "Xem thêm" de load het san pham (site khong phan trang URL).
"""

import os
import re
import time
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse, quote

# Selenium (bat buoc cho phan search "Xem thêm"). Cai: pip install selenium webdriver-manager
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

BASE_URL = "https://cellphones.com.vn"
# Cac trang danh sach tai nghe (danh muc)
LISTING_URLS = [
    # Trang tong hop tai nghe
    "https://cellphones.com.vn/thiet-bi-am-thanh/tai-nghe.html",
    # Mot so danh muc con va khu vuc lien quan
    "https://cellphones.com.vn/thiet-bi-am-thanh/tai-nghe/headphones.html",
    "https://cellphones.com.vn/thiet-bi-am-thanh/tai-nghe/co-day.html",
    "https://cellphones.com.vn/thiet-bi-am-thanh/tai-nghe/kiem-am.html",
    "https://cellphones.com.vn/thiet-bi-am-thanh/tai-nghe/the-thao.html",
    "https://cellphones.com.vn/phu-kien/headphones.html",
    "https://cellphones.com.vn/phu-kien/xa-hang/tai-nghe.html",
    "https://cellphones.com.vn/san-pham-moi/tai-nghe.html",
]
# Tim kiem theo tu khoa (trang search co the co nhieu san pham, thu phan trang &p=)
# Co y dung nhieu tu khoa gan nhau de tang kha nang bao phu
SEARCH_QUERIES = [
    "tai nghe chup tai",
    "tai nghe bluetooth",
    "tai nghe gaming",
    "tai nghe",
    "tai nghe true wireless",
    "tai nghe in ear",
    "tai nghe co day",
    "headphone",
    "earbuds",
]
MAX_PAGES_PER_LISTING = int(os.environ.get("CELLPHONES_MAX_PAGES", "25"))
# So lan nhan "Xem thêm" toi da (cu click cho den khi het nut hoac dat gioi han nay)
MAX_LOAD_MORE_CLICKS = int(os.environ.get("CELLPHONES_LOAD_MORE_CLICKS", "600"))

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


def _url_for_page(base: str, page: int) -> str:
    """Tra ve URL trang danh sach (page=1, 2, ...)."""
    if page == 1:
        return base
    parsed = urlparse(base)
    qs = parse_qs(parsed.query)
    qs["page"] = [str(page)]
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def _search_url(query: str) -> str:
    """URL trang tim kiem (1 trang, load them bang nut Xem thêm)."""
    return f"{BASE_URL}/catalogsearch/result?q={quote(query)}"


def _crawl_search_with_load_more(query: str) -> str:
    """
    Mo trang tim kiem bang Selenium, nhan nut "Xem thêm" nhieu lan de load het san pham,
    tra ve HTML cuoi cung de parse.
    """
    if not SELENIUM_AVAILABLE:
        print("  (Can selenium + webdriver-manager. Dung requests lay 1 trang.)")
        return fetch_html(_search_url(query))

    url = _search_url(query)
    print("  Mo Chrome, load trang tim kiem...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        click_count = 0
        # Click den khi khong con nut "Xem thêm" hoac dat gioi han MAX_LOAD_MORE_CLICKS
        for _ in range(MAX_LOAD_MORE_CLICKS):
            try:
                btn = wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//*[contains(text(), 'Xem thêm') or contains(text(), 'xem thêm')]"
                )))
            except Exception:
                break
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", btn)
                click_count += 1
                if click_count % 20 == 0:
                    print("    Nhan Xem thêm:", click_count, "lan")
                time.sleep(1.2)
            except Exception:
                break
        print("  Tong nhan Xem thêm:", click_count, "lan. Lay HTML...")
        return driver.page_source
    finally:
        if driver:
            driver.quit()


def crawl_all(fetch_detail_for_price: bool = True) -> list:
    all_rows = []
    seen_urls = set()

    for base in LISTING_URLS:
        # Thu page 1, 2, ... dung lai khi trang khong them san pham moi (tranh request trung noi dung)
        for page in range(1, MAX_PAGES_PER_LISTING + 1):
            url = _url_for_page(base, page)
            print("Crawling:", url)
            try:
                html = fetch_html(url)
            except Exception as e:
                print("  -> Loi:", e)
                break
            rows = parse_listing(html, url)
            new_count = 0
            for r in rows:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_rows.append(r)
                    new_count += 1
            print("  -> Trang nay:", len(rows), "san pham, moi:", new_count, "| Tong:", len(all_rows))
            time.sleep(DELAY)
            # Dung phan trang khi khong con san pham moi (site co the khong dung ?page= hoac chi 1 trang)
            if new_count == 0:
                print("  -> Khong them mau moi, chuyen danh muc khac.")
                break

    # Crawl trang TIM KIEM: mo bang Selenium, nhan "Xem thêm" nhieu lan de load het, roi parse
    print("\n--- Crawl trang tim kiem (nut Xem thêm) ---")
    for query in SEARCH_QUERIES:
        url = _search_url(query)
        print("Search:", url)
        try:
            html = _crawl_search_with_load_more(query)
        except Exception as e:
            print("  -> Loi:", e)
            continue
        rows = parse_listing(html, url)
        new_count = 0
        for r in rows:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_rows.append(r)
                new_count += 1
        print("  -> Lay duoc:", len(rows), "san pham, moi:", new_count, "| Tong:", len(all_rows))
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
    return rows


if __name__ == "__main__":
    main()
