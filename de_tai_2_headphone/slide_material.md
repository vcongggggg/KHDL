# Slide material: Dữ liệu & pipeline (de_tai_2_headphone)

## Slide A (Tổng quan)
**Mục tiêu**
- Xây dựng mô hình dự đoán giá tai nghe/headphone: `Y = price_vnd`
- Khảo sát tính khả thi: liệu có mối liên hệ giữa thông số kỹ thuật + tính năng với giá bán hay không

**Nguồn dữ liệu (tự crawl)**
- `cellphones.com.vn` (CellphoneS)
- `gearvn.com` (GearVN)
- `phongvu.vn` (Phong Vũ)
- `hoanghamobile.com` (Hoàng Hà Mobile)

**Quy mô dữ liệu**
- Ước tính raw: ~`1191` dòng (mỗi sản phẩm ~1 dòng)
- Sau clean/encoding (theo notebook): ~`1173` dòng, `17` cột (clean) và ~`31` cột (encoded)

---

## Slide B (Thư viện dùng)
**Web crawling & parsing**
- `selenium` (+ `webdriver-manager`): cần khi trang dùng modal/popup/JS để hiện spec
- `requests`: lấy HTML/endpoint khi có sẵn dữ liệu (tránh phụ thuộc render JS)
- `beautifulsoup4` + `lxml`: parse HTML và trích xuất bảng/thẻ spec
- `re` (regex): trích số (pin/weight/giá), parse label/value

**Dữ liệu & trực quan hóa**
- `pandas`, `numpy`: xử lý dữ liệu + chuẩn hóa + lưu CSV
- `matplotlib`, `seaborn`: biểu đồ EDA (missing, phân bố giá/pin/weight, …)

**ML (tùy chọn cho EDA nâng cao)**
- `scikit-learn`: encoding (one-hot), StandardScaler, `t-SNE` (không giám sát)

**File output chính**
- `raw_data/raw_data.csv` (gộp raw)
- `clean_data/headphone_clean.csv` (clean chuẩn hóa)
- `clean_data/headphone_encoded_for_ml.csv` (encoded cho ML, tùy chọn)

---

## Slide C (Quy trình thực hiện - tổng thể)
1. **Crawl từng website** (tạo raw CSV theo từng nguồn)
   - `scripts/crawl_cellphones_headphone.py`
   - `scripts/crawl_gearvn_headphone.py`
   - `scripts/crawl_phongvu_headphone.py`
   - `scripts/crawl_hoanghamobile_headphone.py`
2. **Gộp raw**: `scripts/merge_raw_to_raw_data.py`
   - `concat` các file raw
   - `drop_duplicates(subset=["url"])`
   - xuất `raw_data/raw_data.csv`
3. **Cleaning & chuẩn hóa**: `notebooks/02-cleaning_data.ipynb`
   - EDA trước clean (missing + phân bố)
   - chuẩn hóa text/categorical
   - parse numeric quan trọng (`battery_life_hours`, `weight_gram`, `price_vnd`)
   - giảm missing theo quy tắc có điều kiện (median/mode theo nhóm)
   - xuất `clean_data/headphone_clean.csv`
4. **Encoding + EDA nâng cao** (tùy chọn): `notebooks/03-data_encoding.ipynb`
   - one-hot encode (`brand_grouped`, `type`)
   - StandardScaler + Clustermap/t-SNE
   - xuất `clean_data/headphone_encoded_for_ml.csv`

---

## Slide D (1 slide duy nhất: Quy trình crawl chung - nêu rõ dùng gì để làm gì)
**Quy trình thực hiện (dùng X để làm Y)**
- Dùng `requests` để gửi HTTP request lấy HTML trang danh mục/tìm kiếm và trang chi tiết (khi site cho dữ liệu tĩnh).
- Dùng `selenium` để mở web như người dùng thật, click/scroll và lấy HTML động (đặc biệt khi spec nằm trong modal/popup).
- Dùng `WebDriverWait` để chờ phần tử/nút/ bảng thông số load xong trước khi parse, tránh lấy thiếu dữ liệu.
- Dùng `BeautifulSoup (bs4) + lxml` để parse HTML và đọc các cặp `label -> value` trong bảng/spec block.
- Dùng `regex (re)` để trích xuất thông tin từ text: giá số, giờ pin, trọng lượng, keyword kết nối.
- Dùng logic chuẩn hóa để map dữ liệu về format chung: `type`, `connection`, `is_wireless`, `has_mic`, `is_gaming`.
- Dùng `urllib.parse` (`urljoin`, xử lý URL) để ghép và chuẩn hóa link sản phẩm đầy đủ.
- Dùng `time.sleep` (delay ngắn) để giảm tần suất request/automation, hạn chế bị chặn.
- Dùng `csv/pandas` để lưu file theo từng nguồn: `raw_data/headphone_<web>_<timestamp>.csv`.
- Dùng `os.makedirs` để tự tạo thư mục output nếu chưa tồn tại.
- Dùng script merge (`merge_raw_to_raw_data.py`) để nối các file raw và `drop_duplicates` theo `url`.

**Lưu ý đặc biệt theo website (ghi ngoài slide)**
- **CellphoneS**: nhiều thông số nằm trong modal "Xem tất cả" -> cần Selenium mở modal rồi mới parse.
- **GearVN**: spec nằm trong modal mở bằng nút `gvn-specs-core-btn`.
- **Phong Vũ**: trang detail render JS mạnh -> ưu tiên Selenium, fallback requests khi cần.
- **Hoàng Hà Mobile**: có endpoint AJAX `/Ajax/fullspecs2/<id>` -> gọi thẳng bằng requests (nhanh và ổn định).

---

## Slide E (Tổng số mẫu / phân bố theo nguồn - raw)
Tổng mẫu raw (theo thống kê notebook crawl):
- CellphoneS: ~`724`
- Hoàng Hà Mobile: ~`279`
- Phong Vũ: ~`125`
- GearVN: ~`63`

Ghi chú:
- Sau khi merge & drop trùng theo `url`, file chuẩn là `raw_data/raw_data.csv`

---

## Slide F (Cleaning & chuẩn hóa - các bước chính)
### Mục tiêu clean
- Giảm `missing` nhưng hạn chế điền sai
- Chuẩn hóa các feature quan trọng để phục vụ phân tích/ML, đặc biệt mục tiêu `price_vnd`

### Bước lọc dữ liệu (quality gate)
- Drop bản ghi có `price_vnd` bị thiếu hoặc `price_vnd <= 0`
- Drop trường hợp thiếu đồng thời các thông tin mô tả quan trọng (đặc biệt `brand` & `type`)
- `drop_duplicates(subset=["url"])`

### Chuẩn hóa feature
- Nhị phân:
  - ép `is_gaming`, `is_wireless`, `has_mic` về 0/1
  - cải thiện `is_wireless` bằng suy luận từ `name/url/connection`
- `normalize_connection`:
  - chuẩn hóa format kết nối (bluetooth/wireless/jack/usb-c/type-c, …)
- Numeric + outlier handling:
  - `battery_life_hours`: parse theo keyword pin/giờ/h/hour; chặn outlier theo range (rule)
  - `weight_gram`: parse từ `kg/g`; chặn outlier theo range (rule)

### Xử lý missing (theo nguyên tắc có điều kiện)
- Impute numeric:
  - điền bằng `median` theo nhóm khi đủ mẫu và median nằm trong range hợp lý
- Impute categorical/text:
  - `type`: ưu tiên `mode` theo nhóm (khi share đủ cao)
  - `brand/connection`: fill theo mode nhóm (fallback `Unknown/Other`)
  - đảm bảo các cột feature chính không còn NaN để encode/model không lỗi

### Output
- `clean_data/headphone_clean.csv`

---

## Slide G (Encoding & EDA - tùy chọn cho bài toán regression)
**Bài toán**
- Hồi quy: dự đoán `price_vnd` từ các đặc trưng kỹ thuật + tính năng

**Features đề xuất**
- Numeric: `battery_life_hours`, `weight_gram`
- Boolean: `is_wireless`, `is_gaming`, `has_mic`
- Categorical (one-hot):
  - `brand` (nhóm top hãng + `Other`)
  - `type`

**Phân tích không giám sát**
- `Clustermap` (tương quan + cụm)
- `t-SNE` (giảm chiều để quan sát gom cụm)

**Output encoding**
- `clean_data/headphone_encoded_for_ml.csv`

---

## Slide H (Kết luận độ khả thi - 2 ý chốt)
1. **Bài toán dự đoán giá là khả thi**
- Dữ liệu đủ lớn, đa dạng
- Correlation/Clustermap cho thấy liên kết giữa `price_vnd` và các đặc trưng như `is_wireless`, pin, thương hiệu
2. **Dữ liệu có cấu trúc phân cụm**
- t-SNE cho thấy các sản phẩm theo phân khúc giá có xu hướng tụ lại thành cụm rõ ràng
- hỗ trợ các thuật toán ML học/tách phân khúc tốt hơn

