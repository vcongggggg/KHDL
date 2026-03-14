# Đề tài 1 — Phân tích và dự đoán giá laptop từ cấu hình phần cứng

Bài thi giữa kỳ môn Khai thác dữ liệu (KHDL). Nhóm 2 người.

---

## Cấu trúc thư mục

```
de_tai_1_laptop/
├── README.md                 # File này
├── requirements.txt          # Thư viện Python cần cài
├── raw_data/                 # Dữ liệu thô sau khi crawl (chưa làm sạch)
├── clean_data/               # Dữ liệu đã làm sạch (dùng trong notebook)
├── scripts/                  # Code crawl và tiện ích
│   ├── crawl_tgdd.py         # Crawler Thế Giới Di Động
│   ├── crawl_fpt.py         # Crawler FPT Shop (mẫu)
│   └── utils.py             # Hàm chung: parse số, lưu CSV
└── notebooks/
    └── 01-Phan-tich-va-du-doan-gia-laptop.ipynb   # Notebook chính
```

---

## Cách chạy

### 1. Cài đặt thư viện

```bash
cd GK/de_tai_1_laptop
pip install -r requirements.txt
```

### 2. Thu thập dữ liệu (crawl)

Chạy crawler và lưu vào `raw_data/`:

```bash
python scripts/crawl_tgdd.py
```

Kết quả: `raw_data/laptop_tgdd_YYYYMMDD_HHMMSS.csv` (hoặc tên tương tự).

**Lưu ý:** Trang web có thể thay đổi cấu trúc HTML; nếu lỗi, mở file `scripts/crawl_tgdd.py` và chỉnh lại bộ chọn (selector) theo trang hiện tại.

### 3. Phân tích trong notebook

1. Mở Jupyter: `jupyter notebook` hoặc mở bằng VS Code / Cursor.
2. Mở file `notebooks/01-Phan-tich-va-du-doan-gia-laptop.ipynb`.
3. Ở phần "Đọc dữ liệu", đổi đường dẫn file CSV cho đúng file trong `raw_data/` (hoặc `clean_data/` nếu đã có bước làm sạch riêng).
4. Chạy lần lượt các cell theo thứ tự.

### 4. Nộp bài

- Đổi tên folder thành: **`STTnhom - Phân tích và dự đoán giá laptop từ cấu hình phần cứng`** (STT nhóm do GV cung cấp).
- Nộp đủ: folder raw data, folder clean data, notebook (và slide nếu dùng slide).
- Kích thước dữ liệu tối đa theo yêu cầu GV (ví dụ 20 MB).

---

## Nguồn dữ liệu

- **Thế Giới Di Động:** https://www.thegioididong.com/laptop  
- **FPT Shop:** https://fptshop.com.vn/may-tinh-xach-tay  
- **Phong Vũ:** https://phongvu.vn/c/laptop  

Dữ liệu **tự thu thập bằng crawler**, không sử dụng dataset có sẵn.
