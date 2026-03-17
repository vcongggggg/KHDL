from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from typing import Any
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
from threading import Lock
import os
import json
import random
from tqdm import tqdm
import csv

url = "https://mobilecity.vn/dien-thoai"
product_links = []
link_lock = Lock()


def format_duration(total_seconds: float) -> str:
    total_seconds = max(0, int(total_seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_chrome_options():
    chrome_options = Options()

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-web-security")
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.page_load_strategy = "eager"
    return chrome_options


def click_show_more_btn(driver: WebDriver, button_id: str, max_attempts=20):
    attempts = 0
    while attempts < max_attempts:
        try:
            # Tìm button
            buttons = driver.find_elements(By.ID, button_id)
            if not buttons:
                print("No more 'Show More' buttons found")
                break

            # Lướt đến button
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", buttons[0]
            )
            time.sleep(1)

            driver.execute_script("arguments[0].click();", buttons[0])

            print(f"Clicked button: {attempts+1} times")
            attempts += 1

            # Đợi nội dung load xong
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            break


def extract_product_link(product):
    try:
        # Tìm link sản phẩm
        link_element = product.find_element(
            By.CSS_SELECTOR, ".product-item-left p.name a"
        )
        link = link_element.get_attribute("href")

        with link_lock:
            product_links.append(link)

        return link
    except Exception as e:
        print(f"Error: {e} in product {product.text} - skipping")
        return None


def save_product_links_to_file(links: list[str], file_path: str):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Product Link"])
            writer.writerows([[link] for link in links])

        print(f"Saved {len(links)} product links to {file_path}")
    except Exception as e:
        print(f"Error saving product links to file: {e}")


def extract_product_common_info(driver: WebDriver, product_link: str) -> dict[str, Any]:
    product_data = {"url": product_link, "name": "", "price": "", "specifications": []}

    print(f"Extracting data from: {product_link}")

    # Lấy tên sản phẩm
    try:
        name_element = driver.find_element(By.CSS_SELECTOR, "p.product-summary-title")
        name = name_element.text.strip()
        if name:
            product_data["name"] = name
            print(f"Found product name: {name}")
    except Exception as e:
        print(f"Error getting product name: {e}")

    time.sleep(1)

    # Lấy giá sản phẩm
    try:
        price_element = driver.find_element(By.CSS_SELECTOR, "p.product-summary-price")
        price = price_element.text.strip()
        if price:
            product_data["price"] = price
            print(f"Found product price: {price}")
    except Exception as e:
        print(f"Error getting product price: {e}")

    # Trích xuất thông số kỹ thuật
    specifications = []

    try:
        driver.execute_script("document.querySelector('.show-lightbox-btn')?.click();")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".product-lightbox-content table")
            )
        )
        time.sleep(1)

        rows = driver.find_elements(
            By.CSS_SELECTOR, ".product-lightbox-content table tbody tr"
        )

        current_category = "Thông tin chung"  # Tên mặc định nếu lỡ hàng đầu tiên không phải là category
        current_details = {}

        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")

            # TRƯỜNG HỢP 1: Đây là hàng tiêu đề Danh mục (Chỉ có 1 td, có colspan="2")
            if len(tds) == 1:
                # Lưu category trước đó vào mảng (nếu đã có dữ liệu)
                if current_details:
                    specifications.append(
                        {"category": current_category, "details": current_details}
                    )
                    # Reset dictionary để chuẩn bị hứng dữ liệu cho category mới
                    current_details = {}

                # Cập nhật tên category mới
                current_category = tds[0].text.strip()

            # TRƯỜNG HỢP 2: Đây là hàng chứa Thông số (Có 2 td)
            elif len(tds) >= 2:
                # Lấy key và xóa luôn dấu hai chấm ":" ở cuối nếu có (VD: "Hệ điều hành:" -> "Hệ điều hành")
                key = tds[0].text.strip().rstrip(":")
                raw_value = tds[1].text.strip()

                # Xử lý giá trị: Nếu có nhiều dòng (do thẻ <br>), tách thành List
                if "\n" in raw_value:
                    value_list = [
                        item.strip() for item in raw_value.split("\n") if item.strip()
                    ]
                    current_details[key] = value_list
                else:
                    current_details[key] = raw_value

        if current_details:
            specifications.append(
                {"category": current_category, "details": current_details}
            )

    except Exception as e:
        print(f"Error during specification extraction: {e}")

    driver.execute_script("document.querySelector('.close-lightbox-btn')?.click();")

    if specifications:
        product_data["specifications"] = specifications

    print(f"product name common data: {product_data}")
    return product_data


def getProductInfo(driver: WebDriver, product_link: str) -> dict[str, Any]:
    """
    Lấy thông tin sản phẩm từ trang product_link bằng cách cào thông tin common và variant, sau đó merge lại thành 1 dict.

    Returns:
    - Dictionary chứa thông tin sản phẩm, bao gồm:
         - url, specifications, variant_prices
    """
    driver.get(product_link)
    time.sleep(2)

    product_common_data = extract_product_common_info(driver, product_link)
    if product_common_data is None:
        product_common_data = {"url": product_link, "specifications": {}}

    return product_common_data


def crawl_products_multithreaded(
    product_links: list[str],
    max_workers: int = 5,
    batch_size: int = 10,
    delay_between_batches: int = 3,
) -> list[dict[str, Any]]:
    """
    Cào dữ liệu sản phẩm đa luồng từ danh sách các liên kết sản phẩm.

    Nếu một liên kết gặp lỗi, sẽ được thêm vào cuối danh sách để xử lý lại tuần tự sau.

    Args:
        product_links: Danh sách các URL sản phẩm cần cào
        max_workers: Số lượng luồng tối đa chạy đồng thời
        batch_size: Kích thước mỗi batch để tránh quá tải
        delay_between_batches: Thời gian chờ giữa các batch (giây)

    Returns:
        Danh sách các dictionary chứa thông tin sản phẩm
    """
    # Đảm bảo thư mục json tồn tại
    os.makedirs("../data/json", exist_ok=True)

    results = []
    retry_links = []  # Danh sách các liên kết cần thử lại

    # Chia danh sách sản phẩm thành các batch nhỏ hơn
    batches = [
        product_links[i : i + batch_size]
        for i in range(0, len(product_links), batch_size)
    ]

    print(f"Chia thành {len(batches)} batch, mỗi batch {batch_size} sản phẩm")

    def worker(link):
        try:
            # Khởi tạo driver riêng cho mỗi thread
            options = get_chrome_options()
            options.add_argument("--headless")

            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), options=options
            )

            try:
                # Random Sleep trước mỗi request để tránh bị chặn
                time.sleep(random.uniform(1, 3))
                # Gọi hàm getProductInfo để cào dữ liệu
                result = getProductInfo(driver, link)
                return result
            finally:
                # Đảm bảo đóng driver sau khi sử dụng
                driver.quit()

        except Exception as e:
            error_msg = f"Lỗi khi xử lý link {link}: {str(e)}"
            print(error_msg)
            return {
                "url": link,
                "error": str(e),
                "specifications": {},
                "variant_prices": [],
            }

    # Xử lý theo từng batch với đa luồng
    for batch_idx, batch in enumerate(batches):
        print(f"Đang xử lý batch {batch_idx+1}/{len(batches)}")
        batch_results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(worker, link): link for link in batch}
            for future in tqdm(
                as_completed(futures), total=len(batch), desc=f"Batch {batch_idx+1}"
            ):
                link = futures[future]
                try:
                    result = future.result()
                    batch_results.append(result)
                except Exception as e:
                    # Nếu có lỗi ngoài dự tính, báo lỗi và tiếp tục
                    print(f"Lỗi khi lấy kết quả cho {link}: {str(e)}")
                    batch_results.append(
                        {
                            "url": link,
                            "error": str(e),
                            "specifications": {},
                            "variant_prices": [],
                        }
                    )

        results.extend(batch_results)
        print(
            f"Đã cào {len(batch_results)}/{len(batch)} sản phẩm từ batch {batch_idx+1}"
        )
        print(f"Tổng số sản phẩm đã cào: {len(results)}/{len(product_links)}")

        if batch_idx < len(batches) - 1:
            print(
                f"Chờ {delay_between_batches} giây trước khi xử lý batch tiếp theo..."
            )
            time.sleep(delay_between_batches)

    # Xử lý các liên kết lỗi sau khi đa luồng bằng cách tuần tự
    # Nếu một liên kết lỗi, thêm nó vào cuối danh sách retry_links để thử lại sau
    retry_links = [result["url"] for result in results if result.get("error")]
    attempt = 1
    while retry_links:
        print(
            f"\nBắt đầu xử lý lại {len(retry_links)} liên kết lỗi (Lần thử: {attempt})"
        )
        current_retry = retry_links.copy()
        retry_links = []  # reset danh sách lỗi

        for link in tqdm(current_retry, desc=f"Retry attempt {attempt}"):
            try:
                options = get_chrome_options()
                options.add_argument("--headless")

                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()), options=options
                )
                try:
                    # Cho phép load chậm hơn, không thêm độ trễ ngẫu nhiên
                    time.sleep(2)
                    result = getProductInfo(driver, link)
                    # Cập nhật kết quả mới vào danh sách results:
                    # Tìm vị trí của kết quả cũ và thay thế
                    for idx, r in enumerate(results):
                        if r["url"] == link:
                            results[idx] = result
                            break
                finally:
                    driver.quit()
            except Exception as e:
                print(f"Lỗi khi xử lý lại link {link}: {str(e)}")
                # Nếu lỗi vẫn xảy ra, thêm link vào cuối danh sách để thử lại sau
                retry_links.append(link)
        if retry_links:
            print(
                f"Vẫn còn {len(retry_links)} liên kết lỗi, chờ 10 giây trước khi thử lại..."
            )
            time.sleep(10)
        attempt += 1

    # Lưu tất cả kết quả vào một file JSON
    try:
        os.makedirs("../data/raw", exist_ok=True)
        with open("../data/raw/mobilecity_data.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        print(
            f"Đã lưu tất cả {len(results)} kết quả vào ../data/raw/mobilecity_data.json"
        )
    except Exception as e:
        print(f"Lỗi khi lưu ../data/raw/mobilecity_data.json: {str(e)}")

    return results


if __name__ == "__main__":
    options = get_chrome_options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    driver.get(url)
    time.sleep(2)
    driver_wait = WebDriverWait(driver, 10)
    button = driver_wait.until(EC.element_to_be_clickable((By.ID, "product_view_more")))

    start_time = time.perf_counter()
    click_show_more_btn(driver, "product_view_more", max_attempts=45)
    product_elements = driver.find_elements(By.CSS_SELECTOR, ".product-item-left")
    num_threads = 12

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(extract_product_link, product)
            for product in product_elements
        ]

        wait(futures)

    print(f"Tìm thấy {len(product_links)} liên kết sản phẩm")
    print(product_links[:10])
    driver.quit()
    save_product_links_to_file(product_links, "../link/product_links_mobilecity.csv")

    results = crawl_products_multithreaded(
        product_links=product_links,
        max_workers=3,
        batch_size=10,
        delay_between_batches=5,
    )

    print(f"Hoàn thành cào dữ liệu cho {len(results)} sản phẩm")
    elapsed_seconds = time.perf_counter() - start_time
    avg_seconds_per_product = elapsed_seconds / len(results) if results else 0
    print(
        f"Tổng thời gian cào: {format_duration(elapsed_seconds)} ({elapsed_seconds:.2f} giây)"
    )
