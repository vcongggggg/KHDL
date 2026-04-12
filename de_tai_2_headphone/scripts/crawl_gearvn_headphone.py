import os
import re
import time
import csv
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

# Selenium (de nhan nut 'Xem thêm sản phẩm' tren trang search)
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

BASE_URL = "https://gearvn.com"

# Cac query search tai nghe tren GearVN (de lan luot dung Selenium)
SEARCH_QUERIES = [
    "tai nghe",
    "tai nghe gaming",
    "headphone",
    "earbuds",
]

MAX_ITEMS = int(os.environ.get("GEARVN_MAX_ITEMS", "450"))
# So lan nhan 'Xem thêm sản phẩm' toi da tren moi trang search
MAX_LOAD_MORE_CLICKS = int(os.environ.get("GEARVN_LOAD_MORE_CLICKS", "200"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}

DELAY = 1.0


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
    # brand: tránh bắt nhầm "Tai"/"Nghe"/...
    stop = {"tai", "nghe", "gaming", "headphone", "earbuds", "true", "wireless"}
    for m in re.finditer(r"\b([a-zA-Z]{3,})\b", name or ""):
        cand = m.group(1)
        if cand.lower() not in stop:
            info["brand"] = cand
            break
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


def _is_headphone_candidate(name: str, url: str) -> bool:
    n = (name or "").lower()
    u = (url or "").lower()
    # loại phụ kiện/hộp/case
    if any(x in n for x in ["phụ kiện", "phu kien", "hộp", "hop", "case", "bao đựng", "bao dung"]):
        return False
    if "/products/tai-nghe" in u or "tai-nghe" in u:
        return True
    positive = ["tai nghe", "headphone", "earbuds", "tws", "true wireless", "in-ear", "over-ear"]
    return any(k in n for k in positive)


def _clean_connection_value(v: str) -> str:
    if not v:
        return ""
    vv = " ".join(v.split())
    low = vv.lower()
    if "copyright" in low or "gearvn" in low:
        return ""
    tokens = [
        "bluetooth",
        "wireless",
        "2.4ghz",
        "lightspeed",
        "3.5",
        "jack",
        "usb",
        "type-c",
        "type c",
        "usb-c",
        "usb a",
        "usb-a",
        "lightning",
        "aux",
        "nfc",
    ]
    if any(t in low for t in tokens):
        return vv
    if low in {"có dây", "không dây"}:
        return vv
    return ""


def _open_detail_driver():
    if not SELENIUM_AVAILABLE:
        return None
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def _try_open_specs_modal(driver, wait: WebDriverWait) -> bool:
    # nút mở modal
    try:
        btn = wait.until(EC.element_to_be_clickable((By.ID, "gvn-specs-core-btn")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", btn)
    except Exception:
        return False

    # chờ modal/table xuất hiện
    try:
        wait.until(
            EC.visibility_of_element_located(
                (By.XPATH, "//h3[contains(., 'Thông số') or contains(., 'Thong so')]")
            )
        )
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
        return True
    except Exception:
        return False


def _close_specs_modal(driver) -> None:
    try:
        btn = driver.find_element(By.ID, "gvn-specs-core-modal-close")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.2)
    except Exception:
        pass


def _extract_specs_from_modal_html(html: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")
    specs: Dict = {
        "brand": "",
        "connection": "",
        "battery_life_hours": "",
        "weight_gram": "",
        "type": "",
        "is_gaming": 0,
        "is_wireless": 0,
        "has_mic": 0,
    }

    # lấy cặp label/value từ các table trong modal
    pairs = []
    for tr in soup.select("table tr"):
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue
        label = (th.get_text(" ", strip=True) or "").strip()
        value = (td.get_text(" ", strip=True) or "").strip()
        if label and value:
            pairs.append((label, value))

    for label, value in pairs:
        ll = label.lower()
        vv = value.strip()
        vlow = vv.lower()

        if (ll.startswith("thương hiệu") or ll.startswith("hãng")) and not specs["brand"]:
            # bỏ các dòng trạng thái/bảo hành
            if "bảo hành" not in ll and len(vv) <= 40:
                specs["brand"] = vv

        if "cổng kết nối" in ll or "kết nối" == ll:
            c = _clean_connection_value(vv)
            if c:
                specs["connection"] = c
                if any(x in c.lower() for x in ["bluetooth", "wireless", "không dây", "2.4ghz", "lightspeed"]):
                    specs["is_wireless"] = 1

        if "phương thức kết nối" in ll and vlow in {"không dây", "co day", "có dây"}:
            if "không dây" in vlow:
                specs["is_wireless"] = 1

        if ll.startswith("kiểu tai nghe"):
            if "in-ear" in vlow or "nhét tai" in vlow or "nhet tai" in vlow:
                specs["type"] = "in-ear"
            elif "over-ear" in vlow or "chụp tai" in vlow or "chup tai" in vlow:
                specs["type"] = "over-ear"

        if "nhu cầu sử dụng" in ll and "gaming" in vlow:
            specs["is_gaming"] = 1

        if ll.startswith("micro"):
            if any(x in vlow for x in ["có", "có", "yes", "true"]):
                specs["has_mic"] = 1

        if "thời lượng pin" in ll or "thời gian sử dụng" in ll or "pin" == ll:
            nums = re.findall(r"\d+", vv)
            if nums:
                specs["battery_life_hours"] = max(nums, key=int)

        if "trọng lượng" in ll or "khối lượng" in ll:
            m = re.search(r"([\d.,]+)\s*g", vv.replace(",", "."), flags=re.I)
            if m:
                specs["weight_gram"] = m.group(1)

    return specs


def fetch_gearvn_specs_via_modal(url: str, driver=None) -> Dict:
    if not SELENIUM_AVAILABLE or driver is None:
        return {}
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        ok = _try_open_specs_modal(driver, wait)
        if not ok:
            return {}
        html = driver.page_source
        specs = _extract_specs_from_modal_html(html)
        _close_specs_modal(driver)
        return specs
    except Exception:
        return {}


def _search_url(query: str) -> str:
    return f"{BASE_URL}/search?q={query.replace(' ', '%20')}"


def _crawl_search_with_load_more(query: str) -> str:
    """
    Mo trang search bang Selenium, cuon xuong va nhan nut
    'Xem thêm sản phẩm' (#load_more_search) nhieu lan de load
    nhieu tai nghe nhat, tra ve HTML cuoi cung.
    """
    if not SELENIUM_AVAILABLE:
        print("  (Can selenium + webdriver-manager. Dung requests lay 1 trang search.)")
        return fetch_html(_search_url(query))

    print("  Mo Chrome, load trang search GearVN...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(_search_url(query))
        wait = WebDriverWait(driver, 15)
        last_count = 0
        for i in range(MAX_LOAD_MORE_CLICKS):
            # Luon cuon xuong gan cuoi trang truoc khi tim nut
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.8)
            try:
                btn = wait.until(
                    EC.element_to_be_clickable((By.ID, "load_more_search"))
                )
            except Exception:
                # Khong con nut 'Xem thêm sản phẩm' -> da load het
                break
            try:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(0.3)
                driver.execute_script("arguments[0].click();", btn)
            except Exception:
                break
            # Cho backend load xong danh sach moi
            time.sleep(1.2)
            products = driver.find_elements(By.CSS_SELECTOR, ".proloop-block")
            count = len(products)
            if count > last_count:
                last_count = count
                if (i + 1) % 5 == 0:
                    print(f"    Nhan 'Xem them san pham' {i+1} lan, so san pham: {count}")
            else:
                # So san pham khong tang -> dung
                break
        print(f"  Tong so san pham nhin thay tren trang search cho query '{query}':", last_count)
        return driver.page_source
    finally:
        if driver:
            driver.quit()


def parse_listing(html: str, page_url: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    rows: List[Dict] = []
    # Card san pham dung class proloop-block (theo HTML ban gui)
    for product in soup.select(".proloop-block"):
        a = product.select_one(".proloop-img a[href]")
        if not a:
            continue
        href = a.get("href", "")
        full_url = urljoin(BASE_URL, href)
        # Ten san pham nam trong h3.proloop-name a
        name_el = product.select_one(".proloop-name a, .product-name, .product-title, h3, h2")
        name = (name_el.get_text() if name_el else a.get_text() or "").strip()
        if not _is_headphone_candidate(name, full_url):
            continue

        price_raw = ""
        # Gia hien thi trong .proloop-price--highlight
        price_el = product.select_one(".proloop-price--highlight, .product-price, .price, .product__price, .pro-price")
        if price_el:
            price_raw = (price_el.get_text() or "").strip()
        m = re.search(r"[\d.,]+\s*[đ₫]?", price_raw)
        if m:
            price_raw = m.group(0).strip()

        row = {
            "source": "gearvn",
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
        inferred = _infer_from_name(name)
        row.update(inferred)
        rows.append(row)
    return rows


def _extract_specs_from_text(text: str) -> Dict:
    """
    Thử trích một số thông số chính từ text trang chi tiết GearVN.

    Dựa trên bảng \"Thông số kỹ thuật\" mà bạn gửi, các label thường gặp:
    - Thương hiệu
    - Cổng kết nối / Phương thức kết nối / Tương thích (Bluetooth...)
    - Kiểu tai nghe
    - Nhu cầu sử dụng (Gaming...)
    - Micro / Microphone
    - Thời lượng pin
    - Trọng lượng
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    specs: Dict = {
        "brand": "",
        "connection": "",
        "battery_life_hours": "",
        "weight_gram": "",
        "type": "",
        "is_gaming": 0,
        "is_wireless": 0,
        "has_mic": 0,
    }

    def get_after_any(labels):
        for i, ln in enumerate(lines):
            for label in labels:
                if label.lower() in ln.lower():
                    for j in range(i + 1, min(i + 6, len(lines))):
                        if lines[j]:
                            return lines[j]
        return ""

    # Thương hiệu
    brand = get_after_any(["Hãng sản xuất", "Thương hiệu"])
    if not brand:
        m = re.search(
            r"(Sony|JBL|Sennheiser|Bose|Hyperx|HyperX|Anker|Baseus|Havit|Samsung|Xiaomi|Razer|Logitech|Steelseries)",
            text,
            flags=re.I,
        )
        if m:
            brand = m.group(1)
    specs["brand"] = brand.strip()

    # Kiểu tai nghe (in-ear / over-ear) nếu có
    type_txt = get_after_any(["Kiểu tai nghe", "Kiểu", "Kiểu"])
    if type_txt:
        t = type_txt.lower()
        if any(x in t for x in ["in-ear", "nhét tai", "nhet tai"]):
            specs["type"] = "in-ear"
        elif any(x in t for x in ["over-ear", "chụp tai", "chup tai", "trùm đầu", "trum dau"]):
            specs["type"] = "over-ear"

    # Kết nối (cổng kết nối / phương thức kết nối / tương thích)
    conn_txt = get_after_any(["Cổng kết nối", "Kết nối", "Chuẩn kết nối", "Phương thức kết nối", "Tương thích"])
    if conn_txt:
        specs["connection"] = conn_txt

    # Suy luận wireless từ kết nối
    conn_lower = (conn_txt or "").lower()
    if any(x in conn_lower for x in ["bluetooth", "không dây", "wireless"]):
        specs["is_wireless"] = 1

    # Nhu cầu sử dụng (gaming)
    use_txt = get_after_any(["Nhu cầu sử dụng", "Nhu cầu sử dụng"])
    if use_txt and "gaming" in use_txt.lower():
        specs["is_gaming"] = 1

    # Micro
    mic_txt = get_after_any(["Micro", "Microphone"])
    if mic_txt:
        if "có" in mic_txt.lower() or "có" in mic_txt.lower():
            specs["has_mic"] = 1

    # Thời lượng pin
    batt_txt = get_after_any(["Thời lượng pin", "Thời gian sử dụng", "Thời gian chơi nhạc"])
    if batt_txt:
        nums = re.findall(r"\d+", batt_txt)
        if nums:
            specs["battery_life_hours"] = max(nums, key=int)

    # Trọng lượng
    weight_txt = get_after_any(["Trọng lượng", "Khối lượng", "Khối lượng"])
    if weight_txt:
        m = re.search(r"([\d.,]+)\s*g", weight_txt.replace(",", "."), flags=re.I)
        if m:
            specs["weight_gram"] = m.group(1)

    return specs


def crawl_listing(max_pages: int = None, delay_sec: float = DELAY) -> List[Dict]:
    all_rows: List[Dict] = []
    seen_urls = set()

    # Dung Selenium cho tung query search, loai trung theo URL
    print("Crawling GearVN bang cac query search voi Selenium...")
    for q in SEARCH_QUERIES:
        if len(all_rows) >= MAX_ITEMS:
            break
        print(f"- Query: '{q}'")
        try:
            html = _crawl_search_with_load_more(q)
        except Exception as e:
            print("  -> Loi search voi query", q, ":", e)
            continue
        rows = parse_listing(html, _search_url(q))
        new_count = 0
        for r in rows:
            u = (r.get("url") or "").strip()
            if u and u not in seen_urls:
                seen_urls.add(u)
                all_rows.append(r)
                new_count += 1
                if len(all_rows) >= MAX_ITEMS:
                    break
        print(f"  -> Query '{q}': {len(rows)} san pham, moi: {new_count} | Tong: {len(all_rows)}")
        time.sleep(delay_sec)

    # Vao tung trang chi tiet de lay thong so (giong cach lam voi Cellphones)
    if all_rows:
        print("\nVao trang chi tiet GearVN de lay thong so...")
        driver = None
        try:
            driver = _open_detail_driver()
            for i, row in enumerate(all_rows):
                try:
                    specs = fetch_gearvn_specs_via_modal(row["url"], driver=driver) if driver else {}
                    # fallback sang cách cũ nếu modal không có
                    if not any(v for v in specs.values()):
                        html = fetch_html(row["url"])
                        soup = BeautifulSoup(html, "lxml")
                        text = soup.get_text("\n", strip=True)
                        specs = _extract_specs_from_text(text)
                        # làm sạch connection nếu bị rác
                        if specs.get("connection"):
                            specs["connection"] = _clean_connection_value(str(specs.get("connection") or ""))
                    for k, v in specs.items():
                        if v:
                            row[k] = v
                    all_rows[i] = row
                    if (i + 1) % 10 == 0:
                        print("  ", i + 1, "/", len(all_rows))
                except Exception:
                    pass
                time.sleep(0.8)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    return all_rows


def save_csv(rows: List[Dict], out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"headphone_gearvn_{ts}.csv")
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
    rows = crawl_listing()
    save_csv(rows, raw_dir)
    return rows


if __name__ == "__main__":
    main()

