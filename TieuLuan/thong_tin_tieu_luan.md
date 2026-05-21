# Thông tin Tiểu luận Cuối kỳ - Khoa học Dữ liệu (2026)

Tài liệu này tổng hợp các ý chính, yêu cầu bắt buộc và các mốc thời gian quan trọng đối với tiểu luận cuối kỳ môn Khoa học Dữ liệu.

---

## 📅 Các mốc thời gian quan trọng (Timelines)

| Thời gian | Sự kiện | Chi tiết |
| :--- | :--- | :--- |
| **Chủ nhật, 24/05/2026** | **Hạn cuối đăng ký đề tài** | Điền tên đề tài đầy đủ vào [Link đăng ký Google Sheets](https://docs.google.com/spreadsheets/d/1po81rNaCsuXPpCajnbBtc5H6lLDQIvbo?rtpof=true&usp=drive_fs) |
| **21:00, Thứ hai, 25/05/2026** | **Mở link nộp bài** | Giảng viên gửi link nộp qua MS Teams |
| **21:15, Thứ hai, 25/05/2026** | **Đóng link nộp bài (Hạn cuối)** | **Chỉ có 15 phút để nộp bài**. Tuyệt đối không trễ hạn. |
| **Đầu buổi thi** | **Nộp bản in quyển báo cáo** | Nộp bản cứng (quyển báo cáo) trực tiếp cho giảng viên |

---

## 🎯 3 Hướng đề tài lựa chọn (SV chọn 1 trong 3)

### Hướng 1: Dự đoán giá Bất động sản (Regression)
* **Đề tài**: Dự đoán giá $X$ dựa trên các đặc điểm vật lý và vị trí địa lý.
  * *Trong đó $X$*: Nhà, đất, căn hộ chung cư, nhà mặt phố,... (Nhóm tự chọn loại hình cụ thể).
* **Target (Output)**: `Price` (Giá).
* **Features (Input)**: Tất cả các trường còn lại trong dataset. **Không giới hạn phạm vi địa lý** (ví dụ: không được chỉ lọc lấy dữ liệu ở TP.HCM).
* **Dataset bắt buộc**: [Tinix Vietnam Real Estate Listings (2025-2026) trên HuggingFace](https://huggingface.co/datasets/tinixai/vietnam-real-estates?fbclid=IwY2xjawQ_Rt1leHRuA2FlbQIxMABicmlkETFQM3A3S2ZoSld6TDdoNHRwc3J0YwZhcHBfaWQQMjIyMDM5MTc4ODIwMDg5MgABHpsb1OrTX64TXjJiz3SHc300NfFUqAc6ZAdxWmIoKbeWSXVVmJq1ec3pB63F_aem_-5RtUiAUfGY69ohhc8cC9A).

### Hướng 2: Dự đoán mức lương kỳ vọng (Regression)
* **Đề tài**: Dự đoán mức lương kỳ vọng dựa trên bản mô tả công việc (Job Description).
* **Target (Output)**: Lương kỳ vọng = Lương trung bình.
  * *Công thức*: $\text{Salary Expected} = \frac{\text{Salary Min} + \text{Salary Max}}{2}$. *(Ví dụ: Khoảng lương 23 - 28 triệu → Lương kỳ vọng = 25.5 triệu).*
* **Features (Input)**: Tất cả các trường còn lại trong dataset.
* **Dataset bắt buộc**: [Tinix Vietnam Job Description trên HuggingFace](https://huggingface.co/datasets/tinixai/vietnamese-job-descriptions?fbclid=IwY2xjawReSItleHRuA2FlbQIxMABicmlkETFMdnV6cWRZZWxPQnRDWldDc3J0YwZhcHBfaWQQMjIyMDM5MTc4ODIwMDg5MgABHjHX7IzdvIDJuhvemwHSWzyZu8c314CdPSjWRI8u8BkxS5_OVKSg3b2OhKCP_aem_rk-hwsxKBue3L8w_dzoJ7A).

### Hướng 3: Dự báo chuỗi thời gian (Time Series)
* **Đề tài**: Dự báo một biến mục tiêu sử dụng mô hình chuỗi thời gian liên quan đến kinh tế / xã hội / môi trường tại Việt Nam giai đoạn 2021-2024.
* **Yêu cầu bắt buộc**: Phải sử dụng **biến ngoại sinh (exogenous variables)** trong mô hình dự báo.
* **Dataset**: Nhóm tự thu thập từ các nguồn tin cậy.

---

## 📁 Quy định cấu trúc thư mục nộp bài
Tên thư mục nộp bài: **`STTnhom - Tên đề tài`** *(Ví dụ: `15 - Dự đoán giá biệt thự`)*

Thư mục nộp bài phải chứa đầy đủ các file sau:
```text
📂 STTnhom - Tên đề tài/
├── 📄 Quyển báo cáo (Định dạng PDF)
├── 📄 Slide báo cáo (Định dạng PDF)
├── 📄 README.md (Hướng dẫn chi tiết trình tự chạy chương trình)
├── 📓 [Một hoặc nhiều] Jupyter Notebook (.ipynb) thực thi code
├── 📂 raw_data/ (Hoặc file raw_data_train.csv & raw_data_test.csv)
│   ├── 📄 raw_data_train.csv
│   └── 📄 raw_data_test.csv
└── 📂 clean_data/ (Hoặc clean_data_train.csv & clean_data_test.csv - Dữ liệu sau khi làm sạch, trước khi Feature Engineering)
    ├── 📄 clean_data_train.csv
    └── 📄 clean_data_test.csv
```

---

## 📝 Yêu cầu đối với Quyển báo cáo & Slide

### Quyển báo cáo:
* **Mẫu trình bày**: Theo [Mau tieu luan KHDL_2026 (Google Docs)](https://docs.google.com/document/d/1BBLzM0sKX3IMyUTrcv2tk3pVWItQgqbI/edit?usp=sharing&ouid=114017105272758041500&rtpof=true&sd=true).
* **Độ dài**: 15 - 20 trang (Không tính Mục lục và Tài liệu tham khảo).
* **Văn phong**: Ngắn gọn, cô đọng, khoa học.
* ⚠️ **Tuyệt đối không đưa mã nguồn vào báo cáo.**
* **Bản in & Bản PDF**: Bản PDF upload lên hệ thống phải **trùng khớp 100%** với bản in nộp trực tiếp.

### Slide báo cáo & Thuyết trình:
* **Nội dung**: Trình bày theo thứ tự của quyển báo cáo, phân chia rõ nhiệm vụ các thành viên.
* **Thời gian báo cáo**: Tối đa **15 phút**.
* **Trọng tâm**: Tập trung phân tích các đặc tính dữ liệu (kèm đồ thị/bảng biểu), các nhận xét, lý giải và so sánh đối chiếu kết quả giữa các kỹ thuật/mô hình.
* **Chuẩn bị**: Mỗi nhóm chuẩn bị sẵn **2-3 máy tính** tại phòng thi để đề phòng sự cố kỹ thuật.

---

## ⚠️ Quy tắc phạt (Nhận 0 điểm nếu vi phạm)

1. ❌ **Không khớp nội dung**: File báo cáo PDF upload không giống 100% với bản in nộp tại lớp. (Lưu ý kiểm tra kỹ lỗi Bookmark trên Mục lục và lỗi định dạng).
2. ❌ **Thiếu file**: Thư mục nộp bài bị thiếu bất kỳ thành phần nào theo yêu cầu của giảng viên.
3. ❌ **Trễ hạn nộp**: Không hoàn thành nộp bài trước 21h15 ngày 25/5/2026 hoặc tự ý sửa đổi bài nộp sau thời gian này.
4. ❌ **Không khớp thông tin**: Thông tin đăng ký đề tài (trên Google Sheets), nội dung quyển báo cáo và chương trình thực thi không đồng nhất với nhau.
