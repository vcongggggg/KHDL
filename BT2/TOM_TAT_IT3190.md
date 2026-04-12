# Tóm tắt nội dung bài giảng IT3190 - Nhập môn Học máy & Khai phá dữ liệu
## Giảng viên: Thân Quang Khoát - Đại học Bách khoa Hà Nội

---

## 📘 Chương 1: Giới thiệu chung về Học máy và Khai phá dữ liệu

### 1.1 Khái niệm cơ bản
*   **Học máy (Machine Learning):** Là lĩnh vực cung cấp phương pháp giải quyết nhiệm vụ thực tế thông qua khả năng tự cải thiện dựa trên dữ liệu hoặc kinh nghiệm (E), nhằm tối ưu hóa tiêu chí hiệu năng (P) khi thực hiện nhiệm vụ (T).
*   **Bản chất:** Tìm một hàm $y^*: x \to y$ để kết nối đầu vào (quan sát) với đầu ra (phán đoán).

### 1.2 Quy trình xây dựng hệ thống (CRISP-DM)
Bao gồm các bước: Hiểu bài toán → Tiếp cận phân tích → Yêu cầu dữ liệu → Thu thập → Hiểu dữ liệu → Tiền xử lý (Data Preparation) → Huấn luyện mô hình (Modeling) → Đánh giá (Evaluation) → Triển khai.

### 1.3 Các vấn đề quan trọng
*   **Quá khớp (Overfitting):** Mô hình quá phức tạp, học cả nhiễu, dẫn đến kết quả kém trên dữ liệu mới.
*   **Kém khớp (Underfitting):** Mô hình quá đơn giản, không học được quy luật dữ liệu.
*   **Tiền xử lý:** Chuyển đổi dữ liệu thô sang dạng vector, lọc nhiễu, chuẩn hóa.

---

## 📘 Chương 2: Hồi quy và Phân cụm

### 2.1 Hồi quy (Regression)
*   **Mục tiêu:** Dự đoán giá trị đầu ra thuộc miền liên tục (số thực).
*   **Mô hình tuyến tính:** Sử dụng hàm $f(x; w) = w_0 + w_1x_1 + ... + w_nx_n$.
*   **Hàm mất mát (Loss function):** Thường dùng **Square loss** (Lỗi bình phương). Mục tiêu là tối thiểu hóa tổng phần dư bình phương (RSS).

### 2.2 Phân cụm (Clustering)
*   Thuộc nhóm học không giám sát (Unsupervised learning).
*   Gom các mẫu dữ liệu tương tự nhau vào cùng một cụm mà không cần nhãn trước.

---

## 📘 Chương 3: Phân loại (Classification)

### 3.1 k-Láng giềng gần nhất (kNN)
*   Dựa trên ý tưởng: Các mẫu tương tự nhau thường có nhãn giống nhau.
*   Đặc điểm: Học lười (lazy learning), không tham số (non-parametric), tốn chi phí lưu trữ và tính toán khi dự đoán.

### 3.2 Cây quyết định & Rừng ngẫu nhiên (Random Forest)
*   Mô hình cấu trúc cây dựa trên các câu hỏi điều kiện. Rừng ngẫu nhiên kết hợp nhiều cây để tăng độ chính xác.

### 3.3 Máy vectơ hỗ trợ (SVM)
*   Tìm siêu phẳng tối ưu để phân tách các lớp dữ liệu với lề (margin) lớn nhất.

### 3.4 Naive Bayes
*   Dựa trên định lý Bayes và giả thiết độc lập giữa các thuộc tính. Cực kỳ hiệu quả cho **phân loại văn bản** (Multinomial Naive Bayes).

### 3.5 Đánh giá và Lựa chọn mô hình (Trọng tâm BT2)
*   **Phương pháp chia dữ liệu:** Hold-out (2/3 train, 1/3 test), Cross-validation (Đánh giá chéo), Stratified Sampling (Lấy mẫu phân tầng).
*   **Độ đo (Metrics):**
    *   **Accuracy:** Độ chính xác tổng thể.
    *   **Precision (Độ chính xác):** Khả năng dự đoán đúng của các mẫu được gán nhãn lớp đó.
    *   **Recall (Độ triệu hồi):** Khả năng tìm thấy các mẫu thực sự thuộc về lớp đó.
    *   **F1-score:** Trung bình điều hòa giữa Precision và Recall. (Macro-F1 dùng cho bài toán nhiều lớp).
*   **Ma trận nhầm lẫn (Confusion Matrix):** Bảng thống kê chi tiết các trường hợp đoán đúng/sai giữa các lớp.

---

## 📘 Chương 4: Khai phá dữ liệu (Data Mining)

### 4.1 Tổng quan
*   **Mục đích:** Trích xuất tri thức từ lượng dữ liệu khổng lồ ("Vũ trụ số").
*   **Kim tự tháp tri thức:** Dữ liệu (Thô) → Thông tin (Có ý nghĩa) → Tri thức (Hiểu biết mức cao).

### 4.2 Các tác vụ chính
*   **Tác vụ mô tả:** Phân cụm, Tổng hợp hóa, Khai phá luật kết hợp (Association Rules - tìm mối liên hệ giữa các mặt hàng/sự kiện).
*   **Tác vụ dự báo:** Phân loại, Hồi quy.

### 4.3 Hiệu chỉnh (Regularization)
*   Các kỹ thuật như L1/L2 regularization giúp kiểm soát độ phức tạp của mô hình để tránh Overfitting.
*   Các kỹ thuật khác: Dừng sớm (Early stopping), Tăng cường dữ liệu (Data augmentation).
