# BT2: Phân Loại Văn Bản Theo Chủ Đề
## Hướng Dẫn Sử Dụng Notebook

---

## 📁 File đã tạo

| File | Mô tả |
|------|-------|
| `BT2_TextClassification_PCA.ipynb` | Notebook chính - chạy từ đầu đến cuối |
| `test_pipeline.py` | Script test nhanh để kiểm tra pipeline |

---

## 🔷 Pipeline Tổng Quan

```
Văn bản thô
    ↓ [Preprocessing] lowercase, loại URL/email/ký tự đặc biệt
    ↓ [TF-IDF]        chuyển text → vector số (10,000 features)
    ↓ [PCA/SVD]       giảm chiều 10,000 → 200 (TruncatedSVD)
    ↓ [Scaler]        chuẩn hóa dữ liệu
    ↓ [ML Model]      Logistic Regression / LinearSVM / Random Forest
    ↓ [Evaluation]    F1-score + Confusion Matrix
```

---

## 🔷 Các Bước Thực Hiện

### **1. Import thư viện** (Cell 1)
- sklearn, numpy, pandas, matplotlib, seaborn

### **2. Load dữ liệu** (Cell 2)
> ⚠️ **Khi GV cung cấp dataset thực tế**, thay Option A bằng Option B:
> ```python
> df_train = pd.read_csv('train_data.csv')   # ← thay tên file thực
> df_test  = pd.read_csv('test_data.csv')
> X_train_raw = df_train['text'].values      # ← thay tên cột thực
> y_train     = df_train['label'].values
> ```

### **3. EDA** (Cell 3)
- Phân bố nhãn, phân bố độ dài văn bản

### **4. Tiền xử lý** (Cell 4)
- Lowercase, loại URL, email, ký tự đặc biệt

### **5. TF-IDF** (Cell 5)
- `max_features=10000`, `ngram_range=(1,2)`, `sublinear_tf=True`
- Với tiếng Việt: đổi `stop_words=None` + tự định nghĩa list stop words

### **6. PCA/TruncatedSVD** (Cell 6-7)
- Phân tích explained variance → chọn `n_components=200`
- **Tại sao TruncatedSVD thay PCA?** TF-IDF là sparse matrix, TruncatedSVD hiệu quả hơn

### **7. Cross-Validation** (Cell 8-9)
- **Stratified 5-Fold CV** – so sánh 3 mô hình
- Metric: **F1-macro** (phù hợp đa lớp, quan tâm đồng đều các lớp)

### **8. GridSearchCV** (Cell 10)
- Tối ưu hyperparameter của mô hình tốt nhất

### **9. Đánh giá** (Cell 11-12)
- Accuracy, F1-macro, F1-micro, F1-weighted
- Classification Report + Confusion Matrix (số lượng + tỷ lệ %)

### **10. Trực quan PCA 2D** (Cell 13)

### **11. Hàm dự đoán nhanh** (Cell 14)
> ⚡ **Dùng khi GV share tập test tại lớp (5 phút):**
> ```python
> df_result = predict_on_test_set("test_data.csv",
>                                  text_col="text",
>                                  label_col="label")
> ```

---

## 📊 Kết Quả Thực Nghiệm (dataset mẫu 20newsgroups, 5 chủ đề)

| Mô hình | CV F1-macro |
|---------|-------------|
| Logistic Regression | 0.8276 ± 0.0175 |
| Linear SVM | ~0.82 |  
| Random Forest | ~0.77 |

**Test F1-macro ~ 0.81** (Accuracy 81%)

---

## ⚙️ Lưu Ý Kỹ Thuật

1. **Tiếng Việt:** Đổi `stop_words='english'` → `stop_words=None`, thêm list stop words tiếng Việt
2. **Nhiều lớp imbalanced:** Thêm `class_weight='balanced'` vào LR/SVM
3. **Tốc độ tại lớp:** Pipeline đã fit sẵn (tfidf, svd_final, scaler, best_model) → chỉ cần transform tập test mới

---

## 📚 Tham Khảo

- Slide: *Đánh giá và lựa chọn mô hình học máy* (TQKhoat)
- Bài giảng: IT3190 ML&DM BKHN (section 3.5)
- scikit-learn Cross-Validation: https://scikit-learn.org/stable/modules/cross_validation.html
