import os
import re
import time
import csv
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://hoanghamobile.com"

# Search keywords (Hoàng Hà Mobile search)
SEARCH_QUERIES = [
    "tai nghe",
    "headphone",
    "earbuds",
    "tws",
]

MAX_ITEMS = int(os.environ.get("HHM_MAX_ITEMS", "600"))
MAX_PAGES = int(os.environ.get("HHM_MAX_PAGES", "30"))

DELAY = float(os.environ.get("HHM_DELAY", "0.8"))
DELAY_DETAIL = float(os.environ.get("HHM_DELAY_DETAIL", "0.7"))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}


def _search_url(query: str, page: int = 1) -> str:
    # Hoàng Hà dùng param p=2 cho trang tiếp theo
    base = f"{BASE_URL}/tim-kiem?scope=&kwd={requests.utils.quote(query)}"
    if page <= 1:
        return base
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}p={page}"


def clean_price_text(price_text: str) -> int:
    if not price_text:
        return 0
    digits = (
        price_text.replace(".", "")
        .replace(",", "")
        .replace("₫", "")
        .replace("đ", "")
        .replace("�", "")
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
    stop = {"tai", "nghe", "gaming", "headphone", "earbuds", "true", "wireless", "tws", "bluetooth"}
    for m in re.finditer(r"\b([a-zA-Z]{3,})\b", name or ""):
        cand = m.group(1)
        if cand.lower() not in stop:
            info["brand"] = cand
            break
    if "gaming" in s:
        info["is_gaming"] = 1
    if any(x in s for x in ["wireless", "bluetooth", "true wireless", "tws"]):
        info["is_wireless"] = 1
    if any(x in s for x in ["mic", "micro"]):
        info["has_mic"] = 1
    if any(x in s for x in ["over-ear", "chụp tai", "chup tai", "trùm đầu", "trum dau", "on-ear"]):
        info["type"] = "over-ear"
    elif any(x in s for x in ["in-ear", "nhét tai", "nhet tai"]):
        info["type"] = "in-ear"
    return info


def _is_headphone_candidate(name: str, url: str) -> bool:
    n = (name or "").lower()
    u = (url or "").lower()
    # Loại các link danh mục/điều hướng (không phải product detail)
    if any(x in u for x in ["/kho-san-pham-cu/", "/tim-kiem", "/phu-kien/", "/dich-vu/", "/tra-gop/"]):
        return False
    if "/tai-nghe/" in u:
        # product detail thường là /tai-nghe/<slug> (1 slug, không có thêm segment)
        try:
            path = urlparse(url).path.strip("/")
            parts = path.split("/")
            # hợp lệ: ["tai-nghe", "<slug>"]
            if len(parts) == 2 and parts[0] == "tai-nghe" and parts[1]:
                return True
        except Exception:
            pass
        return True
    positive = ["tai nghe", "headphone", "earbuds", "tws", "true wireless", "in-ear", "over-ear", "airpods"]
    return any(k in n for k in positive)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def _fetch(session: requests.Session, url: str, timeout: int = 20, retries: int = 2) -> str:
    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            r = session.get(url, timeout=timeout)
            r.raise_for_status()
            r.encoding = r.apparent_encoding or "utf-8"
            return r.text
        except Exception as e:
            last_err = e
            time.sleep(0.8 * (attempt + 1))
    raise last_err  # type: ignore


def _fetch_fullspecs(session: requests.Session, fullspecs_url: str, referer: str) -> str:
    # Endpoint Ajax/fullspecs2 thường yêu cầu header ajax + referer
    headers = {
        "Referer": referer,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "text/html, */*;q=0.9",
    }
    last_err: Optional[Exception] = None
    for attempt in range(3):
        try:
            r = session.get(fullspecs_url, timeout=25, headers=headers)
            r.raise_for_status()
            r.encoding = r.apparent_encoding or "utf-8"
            return r.text
        except Exception as e:
            last_err = e
            time.sleep(0.8 * (attempt + 1))
    raise last_err  # type: ignore


def _extract_fullspecs_url(detail_html: str) -> str:
    # Link dạng: https://hoanghamobile.com/Ajax/fullspecs2/7917
    m = re.search(r"(https?://hoanghamobile\.com)?/Ajax/fullspecs2/\d+", detail_html)
    if not m:
        return ""
    href = m.group(0)
    return href if href.startswith("http") else urljoin(BASE_URL, href)


def _parse_specs_from_fullspecs_html(html: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")
    specs = {
        "brand": "",
        "connection": "",
        "battery_life_hours": None,
        "weight_gram": None,
        "type": "",
        "is_wireless": 0,
        "has_mic": 0,
        "is_gaming": 0,
    }

    # Dạng bạn đưa:
    # div.box-technical-specifications li > strong(label) + span(value)
    pairs: List[tuple[str, str]] = []
    for li in soup.select(".box-technical-specifications li"):
        k_el = li.find("strong")
        v_el = li.find("span")
        if not k_el or not v_el:
            continue
        k = (k_el.get_text(" ", strip=True) or "").strip()
        v = (v_el.get_text(" ", strip=True) or "").strip()
        if k and v:
            pairs.append((k, v))

    for label, value in pairs:
        ll = label.lower()
        vlow = value.lower()

        if ("hãng sản xuất" in ll or ll.startswith("thương hiệu") or ll.startswith("hãng")) and not specs["brand"]:
            specs["brand"] = value

        # Kết nối: ghép nhiều trường liên quan
        if any(x in ll for x in ["công nghệ kết nối", "kết nối cùng lúc", "cổng kết nối", "kết nối"]):
            # tránh các dòng "Phạm vi kết nối" (10m) vì không phải connector
            if "phạm vi" in ll or "pham vi" in ll:
                continue
            parts = [p.strip() for p in re.split(r"[;/,]+", value) if p.strip()]
            if parts:
                cur = specs["connection"]
                joined = ", ".join(parts)
                specs["connection"] = (cur + ", " + joined).strip(", ") if cur else joined

        if any(x in ll for x in ["thời gian sử dụng", "thoi gian su dung", "thời lượng", "thoi luong"]):
            # ưu tiên "Thời gian sử dụng tai nghe"
            nums = re.findall(r"\d+", value)
            if nums:
                try:
                    specs["battery_life_hours"] = max(map(int, nums))
                except ValueError:
                    pass

        if "trọng lượng" in ll or "khoi luong" in ll or "khối lượng" in ll or "weight" in ll:
            m = re.search(r"([\d.,]+)\s*g", value.replace(",", "."), flags=re.I)
            if m:
                try:
                    specs["weight_gram"] = float(m.group(1))
                except ValueError:
                    pass

        if ll.startswith("micro"):
            if any(x in vlow for x in ["có", "có", "yes", "true"]):
                specs["has_mic"] = 1

        if "gaming" in vlow:
            specs["is_gaming"] = 1

        if ll.startswith("kiểu") or ll.startswith("kiểu"):
            if any(x in vlow for x in ["in-ear", "nhét tai", "nhet tai"]):
                specs["type"] = "in-ear"
            elif any(x in vlow for x in ["over-ear", "chụp tai", "chup tai", "trùm đầu", "trum dau", "on-ear"]):
                specs["type"] = "over-ear"

    if specs.get("connection"):
        c = specs["connection"].lower()
        if any(x in c for x in ["bluetooth", "wireless", "không dây", "khong day", "tws", "true wireless"]):
            specs["is_wireless"] = 1

    return specs


def parse_search_listing(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    rows: List[Dict] = []
    seen = set()

    # Tập trung các link sản phẩm thuộc /tai-nghe/
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        if href.startswith("tel:") or href.startswith("javascript"):
            continue
        if "/tai-nghe/" not in href:
            continue
        # loại danh mục kho sản phẩm cũ (không phải trang sản phẩm)
        if "/kho-san-pham-cu/" in href:
            continue
        # loại trang trả góp (không phải product detail)
        if "/tra-gop/" in href:
            continue
        url = urljoin(BASE_URL, href)
        if url in seen:
            continue
        seen.add(url)
        # Đừng lấy name từ text link (hay ra "Danh mục"), sẽ set từ H1 ở trang chi tiết
        if not _is_headphone_candidate("", url):
            continue
        rows.append(
            {
                "source": "hoanghamobile",
                "url": url,
                "name": "",
                "price_raw": "",
                "price_vnd": 0,
                "brand": "",
                "type": "",
                "is_gaming": 0,
                "is_wireless": 0,
                "has_mic": 0,
                "connection": "",
                "battery_life_hours": "",
                "weight_gram": "",
            }
        )

    return rows


def enrich_detail(session: requests.Session, row: Dict) -> Dict:
    html = _fetch(session, row["url"], timeout=25, retries=2)
    soup = BeautifulSoup(html, "lxml")

    # Name
    h1 = soup.find(["h1", "h2"])
    if h1:
        name = (h1.get_text(" ", strip=True) or "").strip()
        if name:
            row["name"] = name[:300]

    # Price: tìm pattern "330.000 ₫"
    text_all = soup.get_text(" ", strip=True)
    m = re.search(r"([\d]{1,3}(?:\.[\d]{3})+)\s*₫", text_all)
    if m:
        row["price_raw"] = m.group(0).strip()
        row["price_vnd"] = clean_price_text(row["price_raw"])

    # Infer
    row.update(_infer_from_name(row.get("name", "")))

    # Full specs via Ajax/fullspecs2/<id>
    fullspecs_url = _extract_fullspecs_url(html)
    if fullspecs_url:
        try:
            specs_html = _fetch_fullspecs(session, fullspecs_url, referer=row["url"])
            specs = _parse_specs_from_fullspecs_html(specs_html)
            for k, v in specs.items():
                if v not in (None, "", 0):
                    row[k] = v
        except Exception:
            pass

    return row


def crawl_all() -> List[Dict]:
    session = _session()
    all_rows: List[Dict] = []
    seen_urls = set()

    for q in SEARCH_QUERIES:
        if len(all_rows) >= MAX_ITEMS:
            break
        print(f"HoangHaMobile search: '{q}'")
        for page in range(1, MAX_PAGES + 1):
            if len(all_rows) >= MAX_ITEMS:
                break
            url = _search_url(q, page=page)
            try:
                html = _fetch(session, url, timeout=25, retries=2)
            except Exception:
                break
            rows = parse_search_listing(html)
            new_count = 0
            for r in rows:
                u = r["url"]
                if u not in seen_urls:
                    seen_urls.add(u)
                    all_rows.append(r)
                    new_count += 1
                    if len(all_rows) >= MAX_ITEMS:
                        break
            print(f"  - page {page}: found={len(rows)} new={new_count} total={len(all_rows)}")
            time.sleep(DELAY)
            # nếu trang này không thêm được url mới thì dừng sớm
            if new_count == 0 and page >= 2:
                break

    # Enrich details
    if all_rows:
        print("\nVao trang chi tiet HoangHaMobile de lay gia + thong so...")
        for i, row in enumerate(all_rows):
            try:
                all_rows[i] = enrich_detail(session, row)
            except Exception:
                pass
            if (i + 1) % 20 == 0:
                print(" ", i + 1, "/", len(all_rows))
            time.sleep(DELAY_DETAIL)

    return all_rows


def save_csv(rows: List[Dict], out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"headphone_hoanghamobile_{ts}.csv")
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

