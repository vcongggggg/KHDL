# Phân Tích Ảnh Hưởng của Phần Cứng và Thương Hiệu đến Giá Điện Thoại Di Động

Nhóm thực hiện:

- **Đặng Đăng Khoa** _(Crawl dữ liệu và mã hoá dữ liệu)_
- **Nguyễn Thành Lập** _(Clean dữ liệu và thiết lập feature engineering)_
- **Trần Nguyễn Văn Phát** _(Phân tích đa biến)_

## 1. Tổng Quan

Phân tích mức độ ảnh hưởng của các thông số phần cứng và thương hiệu đến giá bán của điện thoại di động. Dự án này tập trung vào thu thập dữ liệu, xem sét sự ảnh hưởng của phần cứng và thương hiệu đến mức giá của điện thoại di động, tiền xử lý và phân tích để chuẩn bị cho việc xây dựng mô hình dự đoán giá.

## 2. Nguồn Dữ Liệu

Dữ liệu được thu thập từ hai trang thương mại điện tử:

- [MobileCity](https://mobilecity.vn/dien-thoai)
- [CellphoneS](https://cellphones.com.vn/mobile.html)

## 3. Mục Tiêu Phân Tích

Khảo sát tính khả thi cho việc xây dựng mô hình dự đoán biến mục tiêu "Giá - Price" dựa trên các đặc trưng về phần cứng và thương hiệu. Với biến mục tiêu là biến liên tục, bài toán được định hướng theo mô hình hồi quy (regression).

## 4. Cấu Trúc Thư Mục

```
KHDL/
│
├── notebooks/
│   ├── crawl_data_cellphones.ipynb    # Thu thập dữ liệu từ CellphoneS
│   ├── crawl_data_mobilecity.ipynb    # Thu thập dữ liệu từ MobileCity
│   ├── cleaning_data.ipynb            # Tiền xử lý - làm sạch dữ liệu
│   └── data_analysis.ipynb            # Phân tích dữ liệu và trực quan hóa
│
├── scripts/
│   ├── crawl_data_cellphones.py       # Script thu thập dữ liệu từ CellphoneS
│   ├── crawl_data_mobilecity.py       # Script thu thập dữ liệu từ MobileCity
│   └── merge_data.py                  # Script gộp dữ liệu từ hai nguồn
│
├── link/
│   ├── product_links_cellphones.csv   # Link sản phẩm từ CellphoneS
│   └── product_links_mobilecity.csv   # Link sản phẩm từ MobileCity
│
├── data/
│   ├── raw/
│   │   ├── cellphones_data.json       # Dữ liệu gốc thu thập từ CellphoneS
│   │   ├── mobilecity_data.json       # Dữ liệu gốc thu thập từ MobileCity
│   │   └── all_products.json          # Dữ liệu gộp từ cả hai nguồn
│   │
│   └── clean/
│       ├── cleaned_data.csv           # Dữ liệu đã được làm sạch
│       ├── extracted_features.csv     # Dữ liệu sau khi đã được trích xuất đặc trưng
│       ├── feature_engineering.csv    # Dữ liệu sau khi đã được feature engineering
│       └── encoded_data_for_ml.csv    # Dữ liệu đã được mã hóa cho mô hình học máy
│
└── README.md                          # Tài liệu dự án
```

## 5. Hướng dẫn cài đặt

### Khởi tạo môi trường ảo

```bash
# Linux/MacOS
python3 -m venv .venv && source .venv/bin/activate

# Windows
python -m venv .venv && .venv\Scripts\activate
```

### Cài đặt các thư viện cần thiết

```bash
pip install -r requirements.txt
```

## 6. Thứ tự thực thi file

1. `scripts/crawl_data_cellphones.py` - Thu thập dữ liệu từ CellphoneS
2. `scripts/crawl_data_mobilecity.py` - Thu thập dữ liệu từ MobileCity
3. `scripts/merge_data.py` - Gộp dữ liệu từ hai nguồn
4. `notebooks/cleaning_data.ipynb` - Tiền xử lý dữ liệu
5. `notebooks/data_analysis.ipynb` - Phân tích dữ liệu

## 7. Công Nghệ Sử Dụng

- Python: Ngôn ngữ lập trình chính
- Pandas & NumPy: Xử lý và phân tích dữ liệu
- Matplotlib & Seaborn: Trực quan hóa dữ liệu
- Selenium: Thu thập dữ liệu web
- Scikit-learn: Mã hóa dữ liệu và phân chia tập dữ liệu
