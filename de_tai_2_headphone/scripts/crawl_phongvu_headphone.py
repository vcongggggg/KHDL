import os
import re
import time
import csv
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
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
    "https://phongvu.vn/c/tai-nghe-gaming",
    "https://phongvu.vn/c/tai-nghe-wireless",
    "https://phongvu.vn/c/tai-nghe-có-mic",
    "https://phongvu.vn/c/tai-nghe-không-dây",
    "https://phongvu.vn/c/tai-nghe-trùm-đầu",
    "https://phongvu.vn/c/tai-nghe-nhét-tai",
    "https://phongvu.vn/c/tai-nghe-nhet-tai",
    "https://phongvu.vn/c/tai-nghe-chụp-tai",
    "https://phongvu.vn/c/tai-nghe-chup-tai",
    "https://phongvu.vn/c/tai-nghe-trum-dau",
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


def _is_headphone_candidate(name: str, url: str) -> bool:
    n = (name or "").lower()
    u = (url or "").lower()
    # URL thường chứa slug "tai-nghe" nếu đúng ngành hàng
    if "tai-nghe" in u:
        return True
    # Keyword positive
    positive = [
        "tai nghe",
        "headphone",
        "earbud",
        "earbuds",
        "tws",
        "true wireless",
        "in-ear",
        "over-ear",
        "chụp tai",
        "chup tai",
        "nhét tai",
        "nhet tai",
        "airpods",
    ]
    if any(k in n for k in positive):
        return True
    return False


def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or "utf-8"
    return r.text


def _sanitize_url(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return s
    first_http = s.find("http")
    if first_http > 0:
        s = s[first_http:]
    if s.startswith("http") and s.count("http") >= 2:
        s = s[: s.find("http", 4)]
    s = s.replace(" ", "")
    return s


def _scroll_and_try_expand(driver) -> None:
    # Scroll để trigger lazy render
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.35);")
        time.sleep(0.6)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
        time.sleep(0.6)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.9)
    except Exception:
        return

    # Best-effort: click các nút mở rộng nếu có
    for xp in [
        "//button[contains(., 'Xem thêm')]",
        "//button[contains(., 'Xem chi tiết')]",
        "//div[contains(@class,'button-text') and contains(., 'Xem thêm')]",
    ]:
        try:
            btn = driver.find_element(By.XPATH, xp)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(0.6)
        except Exception:
            pass


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


def _fetch_detail_html(url: str, driver=None) -> str:
    """
    PhongVu detail thường render JS -> dùng Selenium để lấy page_source đã render.
    Nếu Selenium không có thì fallback requests.
    """
    url = _sanitize_url(url)
    if not url:
        return ""

    if not SELENIUM_AVAILABLE or driver is None:
        return fetch_html(url)

    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(lambda d: d.execute_script("return document.readyState") == "complete")
        _scroll_and_try_expand(driver)
        return driver.page_source
    except Exception:
        # fallback requests nếu Selenium lỗi
        try:
            return fetch_html(url)
        except Exception:
            return ""


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
        if not _is_headphone_candidate(name, full_url):
            continue

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


def _extract_specs_from_html(container: Tag) -> Dict:
    """
    Trích các thông số chính từ block HTML 'Thông số kĩ thuật' của Phong Vũ.
    Dựa trên cấu trúc:
      div.css-19vrbri > div.css-1lchwqw (label) + div.css-1lchwqw (value)
    """
    specs: Dict = {
        "brand": "",
        "connection": "",
        "battery_life_hours": None,
        "weight_gram": None,
        "type": "",
        "is_wireless": 0,
        "has_mic": 0,
    }

    for row in container.select("div.css-19vrbri"):
        cells = row.select("div.css-1lchwqw")
        if len(cells) < 2:
            continue
        label = cells[0].get_text(strip=True)
        value = cells[1].get_text(strip=True)
        if not label:
            continue

        # Thương hiệu
        if label.startswith("Thương hiệu"):
            specs["brand"] = value

        # Kiểu tai nghe
        elif label.startswith("Kiểu") or label.startswith("Kiểu tai nghe") or label.startswith("Kiểu"):
            t = value.lower()
            if any(x in t for x in ["in-ear", "nhét tai", "nhet tai"]):
                specs["type"] = "in-ear"
            elif any(x in t for x in ["over-ear", "chụp tai", "chup tai", "trùm đầu", "trum dau"]):
                specs["type"] = "over-ear"

        # Kết nối (Bluetooth, 3.5mm,...)
        elif label.startswith("Kết nối") or label.startswith("Kết nối") or label.startswith("Cổng kết nối"):
            specs["connection"] = value
            vlow = value.lower()
            if "bluetooth" in vlow or "không dây" in vlow or "wireless" in vlow:
                specs["is_wireless"] = 1

        # Kiểu kết nối (tai nghe không dây / có dây)
        elif label.startswith("Kiểu kết nối"):
            vlow = value.lower()
            if "không dây" in vlow or "wireless" in vlow or "bluetooth" in vlow:
                specs["is_wireless"] = 1

        # Micro
        elif label.startswith("Micro") or label.startswith("Microphone"):
            vlow = value.lower()
            if "có" in vlow or "có" in vlow:
                specs["has_mic"] = 1

        # Thời lượng pin
        elif label.startswith("Thời lượng pin") or label.startswith("Thời gian sử dụng") or label.startswith("Thời gian nghe nhạc"):
            nums = re.findall(r"\d+", value)
            if nums:
                try:
                    specs["battery_life_hours"] = max(map(int, nums))
                except ValueError:
                    pass

        # Trọng lượng / Khối lượng
        elif label.startswith("Khối lượng") or label.startswith("Khối lượng") or label.startswith("Trọng lượng"):
            m = re.search(r"([\d.,]+)\s*g", value.replace(",", "."), flags=re.I)
            if m:
                try:
                    specs["weight_gram"] = float(m.group(1))
                except ValueError:
                    pass

        # Một số case Phong Vũ nhét cả câu mô tả dài trong value (không có label riêng cho pin),
        # ví dụ: "Tai nghe đa năng kết nối ... Thời lượng sử dụng pin 3 - 4 giờ; ..."
        # Khi đó ta vẫn cố gắng bắt thời lượng pin từ chính value.
        if specs.get("battery_life_hours") is None:
            vlow_all = value.lower()
            if any(k in vlow_all for k in ["thời lượng", "thoi luong", "thời gian sử dụng", "thoi gian su dung", "thời lượng pin", "thoi luong pin", "pin "]):
                nums = re.findall(r"\d+", value)
                if nums:
                    try:
                        specs["battery_life_hours"] = max(map(int, nums))
                    except ValueError:
                        pass

    return specs


def _find_detail_container(soup: BeautifulSoup) -> Tag:
    # Ưu tiên "Thông tin chi tiết" (đúng với debug)
    title = soup.find(["div", "h5"], string=re.compile("Thông tin chi tiết", re.I))
    if not title:
        # fallback: có thể có "Thông số kỹ thuật"
        title = soup.find(["div", "h5"], string=re.compile("Thông số k[ií] thuật|Thông số", re.I))
    if not title:
        return soup  # type: ignore

    parent = title.find_parent("div")
    if not parent:
        return title.parent or soup  # type: ignore

    # Bám theo debug: thử 1 wrapper đặc trưng, không có thì dùng luôn parent
    return parent.find_parent("div", class_=re.compile("css-1vyqkg")) or parent


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
        driver = None
        try:
            driver = _open_detail_driver()
            for i, row in enumerate(all_rows):
                try:
                    html = _fetch_detail_html(row.get("url", ""), driver=driver)
                    if not html:
                        continue
                    soup = BeautifulSoup(html, "lxml")
                    container = _find_detail_container(soup)
                    specs = _extract_specs_from_html(container)
                    # Nếu container bắt nhầm (không thấy row spec) thì fallback quét toàn trang
                    if (
                        not any(v not in (None, "", 0) for v in specs.values())
                        and len(container.select("div.css-19vrbri")) == 0
                        and len(soup.select("div.css-19vrbri")) > 0
                    ):
                        specs = _extract_specs_from_html(soup)  # type: ignore
                    for k, v in specs.items():
                        if v not in (None, "", 0):
                            row[k] = v
                    all_rows[i] = row
                    if (i + 1) % 10 == 0:
                        print("  ", i + 1, "/", len(all_rows))
                except Exception:
                    pass
                time.sleep(DELAY_DETAIL)
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

