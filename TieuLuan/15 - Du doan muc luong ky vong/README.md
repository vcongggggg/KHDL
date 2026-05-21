# Nhóm 15 - Tiểu luận môn Khoa học Dữ liệu

## Đề tài 2: Dự đoán mức lương kỳ vọng của các vị trí tuyển dụng tại Việt Nam dựa trên mô tả công việc bằng Machine Learning

### Thành viên nhóm:
- Ngô Văn Công
- Võ Minh Hiếu
- Nguyễn Phan Tuấn

### Cấu trúc dự án:
- `raw_data_train.csv` / `raw_data_test.csv`: Dữ liệu thô tải từ HuggingFace (Tinix Vietnam Job Description), đã chia tỷ lệ 80/20.
- `clean_data_train.csv` / `clean_data_test.csv`: Dữ liệu sạch sau khi đã được trích xuất lương (Regex) và lọc outlier.
- `TieuLuan_Nhom15.ipynb`: Jupyter Notebook chính thức tích hợp toàn bộ quy trình từ Giới thiệu đề tài, EDA trực quan hóa, Tiền xử lý dữ liệu, Huấn luyện RandomForest + LightGBM + XGBoost, Đánh giá bằng RMSE, MAE, R2 và RAM (%).
- `best_model.pkl`: File lưu trữ Pipeline mô hình tốt nhất (được tự động sinh ra khi chạy notebook).
- `download_data.py`: Script dùng để tải lại dữ liệu thô.

### Hướng dẫn chạy chương trình:
1. Cài đặt các thư viện cần thiết:
   ```bash
   pip install pandas numpy scikit-learn xgboost lightgbm matplotlib seaborn datasets jupyter
   ```
2. Mở Jupyter Notebook:
   ```bash
   jupyter notebook TieuLuan_Nhom15.ipynb
   ```
3. Chọn **Kernel -> Restart & Run All** để thực thi toàn bộ luồng xử lý và xem kết quả biểu đồ so sánh mô hình trực quan.
