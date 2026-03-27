# Phân tích và dự đoán giá tai nghe/headphone từ thông số kỹ thuật

## 1. Tổng quan

Mục tiêu của đề tài là **khảo sát tính khả thi** xây dựng mô hình **dự đoán giá tai nghe (Y = `price_vnd`)** dựa trên các **thuộc tính & thông số** (X) như: hãng, loại tai nghe, có gaming/không, wireless/không, có mic/không, cổng kết nối, thời lượng pin, trọng lượng...

## 2. Nguồn dữ liệu

Dữ liệu được tự crawl từ các trang TMĐT:
- CellphoneS (`cellphones.com.vn`)
- GearVN (`gearvn.com`)
- Phong Vũ (`phongvu.vn`)
- Hoàng Hà Mobile (`hoanghamobile.com`)

## 3. Cấu trúc thư mục

```
de_tai_2_headphone/
│
├── scripts/
│   ├── crawl_cellphones_headphone.py
│   ├── crawl_gearvn_headphone.py
│   ├── crawl_phongvu_headphone.py
│   ├── crawl_hoanghamobile_headphone.py
│   └── merge_raw_to_raw_data.py        # (gộp raw -> raw_data/raw_data.csv)
│
├── raw_data/
│   ├── headphone_cellphones_*.csv      # raw từng nguồn
│   ├── headphone_gearvn_*.csv
│   ├── headphone_phongvu_*.csv
│   ├── headphone_hoanghamobile_*.csv
│   └── raw_data.csv                    # dữ liệu gộp (sau merge)
│
├── clean_data/
│   ├── headphone_clean.csv             # dữ liệu đã clean dùng cho phân tích
│   ├── headphone_encoded_for_ml.csv     # (tuỳ chọn) dữ liệu đã encoding cho ML
│
├── notebooks/
│   ├── 01-data_collection.ipynb        # mô tả cách thu thập dữ liệu từng web
│   ├── 02-cleaning_data.ipynb          # cleaning + chuẩn hoá + trực quan hoá before/after
│   ├── 03-data_encoding.ipynb          # encoding + EDA nâng cao
│
├── requirements.txt
└── README.md
```

## 4. Cài đặt môi trường

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 5. Thứ tự chạy (pipeline)

1. **Crawl từng nguồn**:
   ```bash
   python scripts/crawl_cellphones_headphone.py
   python scripts/crawl_gearvn_headphone.py
   python scripts/crawl_phongvu_headphone.py
   python scripts/crawl_hoanghamobile_headphone.py
   ```

2. **Gộp dữ liệu raw** thành một file duy nhất:
   ```bash
   python scripts/merge_raw_to_raw_data.py
   ```
   Output: `raw_data/raw_data.csv` (loại trùng theo `url`).

3. **Mô tả cách thu thập dữ liệu (phần báo cáo)**:
   - Mở `notebooks/00-data_collection.ipynb` (markdown mô tả cách crawl mỗi web).

4. **Làm sạch + chuẩn hoá dữ liệu**:
   - Mở `notebooks/02-cleaning_data.ipynb`, Run All:
     - Đọc `raw_data/raw_data.csv`
     - EDA before cleaning (missing + phân bố biến chính)
     - Cleaning theo pipeline (chuẩn hoá text/connection/battery/weight/type, giảm missing)
     - Xuất `clean_data/headphone_clean.csv`

5. **Encoding + EDA nâng cao (tuỳ chọn)**:
   - Mở `notebooks/03-data_encoding.ipynb`, Run All:
     - Đọc `clean_data/headphone_clean.csv`
     - One-hot / encoding các biến phân loại
     - (Tuỳ chọn) t-SNE: có cờ `RUN_HEAVY` để tránh treo kernel khi không cần


