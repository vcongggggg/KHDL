# Phân tích và dự đoán giá tai nghe/headphone từ thông số kỹ thuật

## 1. Tổng quan

Mục tiêu của đề tài là **khảo sát tính khả thi** xây dựng mô hình **dự đoán giá tai nghe (Y = `price_vnd`)** dựa trên các **thuộc tính & thông số** (X) như: hãng, loại tai nghe, có gaming/không, wireless/không, có mic/không, cổng kết nối, thời lượng pin, trọng lượng...

## 2. Nguồn dữ liệu

Dữ liệu được tự crawl từ 3 trang TMĐT:
- CellphoneS (`cellphones.com.vn`)
- GEARVN (`gearvn.com`)
- Phong Vũ (`phongvu.vn`)

## 3. Cấu trúc thư mục

```
de_tai_2_headphone/
│
├── scripts/
│   ├── crawl_cellphones_headphone.py
│   ├── crawl_gearvn_headphone.py
│   ├── crawl_phongvu_headphone.py
│   └── merge_raw_to_raw_data.py        # (gộp 3 nguồn -> raw_data/raw_data.csv)
│
├── raw_data/
│   ├── headphone_cellphones_*.csv      # raw từng nguồn
│   ├── headphone_gearvn_*.csv
│   ├── headphone_phongvu_*.csv
│   └── raw_data.csv                    # dữ liệu gộp (sau merge)
│
├── clean_data/
│   ├── headphone_clean.csv             # dữ liệu đã clean dùng cho phân tích
│
├── notebooks/
│   └── 01-Phan-tich-va-du-doan-gia-tai-nghe.ipynb
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

1. **Crawl từng nguồn** (có thể chọn 1–3 nguồn tuỳ nhu cầu):
   ```bash
   python scripts/crawl_cellphones_headphone.py
   python scripts/crawl_gearvn_headphone.py
   python scripts/crawl_phongvu_headphone.py
   ```

2. **Gộp dữ liệu raw** thành một file duy nhất:
   ```bash
   python scripts/merge_raw_to_raw_data.py
   ```
   Output: `raw_data/raw_data.csv` (~1000 dòng từ 3 nguồn, loại trùng theo `url`).

3. **Làm sạch + phân tích** trong notebook:
   - Mở `notebooks/01-Phan-tich-va-du-doan-gia-tai-nghe.ipynb`.
   - Run All:
     - Đọc `raw_data/raw_data.csv`.
     - Clean & chuẩn hoá dữ liệu (chuẩn hoá `connection`, boolean, xử lý missing...).
     - Lưu `clean_data/headphone_clean.csv`.
     - Thực hiện EDA, trực quan hoá và đánh giá khả thi của mô hình dự đoán giá.

