# Đề tài đã chốt — Giữa kỳ KHDL (nhóm 2 người)

## Tên đề tài
**Phân tích và dự đoán giá laptop từ cấu hình phần cứng**  
*(Crawl dữ liệu laptop bán tại Việt Nam từ các trang thương mại điện tử.)*

---

## 1. Phát biểu bài toán (đặt đầu notebook/slide)

- **Mục tiêu:** Phân tích dữ liệu để đánh giá **khả thi** xây dựng mô hình **dự đoán giá laptop (Y)** từ các đặc trưng cấu hình (X₁, X₂, …).
- **Loại bài toán:** **Hồi quy (Regression)** — biến mục tiêu Y là số (giá VND).
- **Yêu cầu cần trả lời:**
  - Bài toán có khả thi với dữ liệu thu thập được không? Vì sao?
  - Nếu khả thi, tập **đặc trưng hữu ích** dùng để xây dựng mô hình là gì?

*(Lưu ý: Phần mô hình hóa chi tiết dành cho bài tập sau; bài GK tập trung thu thập, làm sạch, mã hóa, feature engineering, trực quan hóa và kết luận.)*

---

## 2. Biến mục tiêu (Y)

| Tên biến   | Mô tả           | Đơn vị |
|------------|-----------------|--------|
| `price_vnd` | Giá bán laptop  | VND    |

---

## 3. Biến giải thích (X) — gợi ý thu thập

| Nhóm        | Biến gợi ý | Ghi chú |
|-------------|------------|---------|
| **Cơ bản**  | `brand`, `name`, `sku` | Hãng, tên sản phẩm, mã |
| **CPU**     | `cpu_name`, `cpu_cores`, `cpu_threads` | Tên CPU, số nhân, số luồng |
| **RAM**     | `ram_gb`   | Dung lượng RAM (GB) |
| **Ổ cứng**  | `storage_type`, `storage_gb`, `has_hdd`, `has_ssd` | Loại ổ, dung lượng, HDD/SSD |
| **Màn hình**| `screen_size_inch`, `resolution`, `refresh_rate_hz` | Inch, độ phân giải, tần số quét |
| **Đồ họa**  | `gpu_type`, `gpu_name` | Onboard / Card rời, tên GPU |
| **Khác**    | `weight_kg`, `os`, `release_year` (nếu có) | Cân nặng, HĐH, năm ra mắt |

**Tối thiểu:** ≥ 5 biến (theo yêu cầu GV). Nên thu thập ≥ 10 biến để làm feature engineering và trực quan đa biến phong phú.

---

## 4. Nguồn dữ liệu (tự crawl)

- **Bắt buộc:** Tự thu thập (crawl), **không** dùng dataset có sẵn.
- **Số lượng:** > 1000 mẫu (sản phẩm laptop).
- **Nguồn gợi ý (chọn 1 hoặc kết hợp):**
  - `https://www.thegioididong.com/laptop`
  - `https://fptshop.com.vn/may-tinh-xach-tay`
  - `https://phongvu.vn/c/laptop`
  - `https://cellphones.com.vn/laptop.html`
  - `https://gearvn.com/laptop.html`

Trong notebook: **ghi rõ nguồn** và **mô tả cách thu thập** (công cụ, luồng crawl, cấu trúc HTML/API nếu có).

---

## 5. Cấu trúc bài làm (theo rubric GK)

1. **Thu thập dữ liệu** — Code crawl + mô tả + lưu raw data.
2. **Thống kê mô tả** — Trực quan đơn biến cho một vài biến quan trọng (minh họa).
3. **Làm sạch và chuẩn hóa** — Mô tả cách xử lý; trực quan **phân bố trước / sau** làm sạch.
4. **Mã hóa dữ liệu** — Biến danh mục (one-hot/label) hoặc text (NLP nếu có).
5. **Feature engineering** — Xây dựng và lựa chọn đặc trưng (ví dụ: `price_per_ram_gb`, nhóm CPU theo hiệu năng, …).
6. **Trực quan đa biến** — Scatter, correlation map, distribution, lmplot, clustermap; có thể thêm t-SNE nếu phù hợp.
7. **Kết luận** — Khả thi hay không, đặc trưng hữu ích là gì.
8. **Tài liệu tham khảo** — Đặt cuối notebook/slide.

---

## 6. Gợi ý chia công việc (nhóm 2 người)

| Người | Phần chính |
|-------|------------|
| **A** | Crawl (code + raw data) + Làm sạch + Mã hóa + Thống kê mô tả / EDA đơn biến |
| **B** | Feature engineering + Trực quan đa biến + Kết luận + Chuẩn bị slide/notebook trình bày |

*(Cả hai cùng nắm toàn bộ để trả lời khi thuyết trình.)*

---

## 7. Tên folder nộp bài (theo GV)

Format: **`STTnhom - Tên đề tài`**  
Ví dụ: `07 - Phân tích và dự đoán giá laptop từ cấu hình phần cứng`

---

## 8. Bước tiếp theo

- Đăng ký đề tài vào Google Sheet theo link GV gửi (trước **17h 10/3/2026**).
- Bắt đầu crawl 1 nguồn (ví dụ TGDĐ) để kiểm tra cấu trúc HTML và số lượng sản phẩm.
- Làm skeleton notebook theo style folder mẫu `10-Data-Capstone-Projects`.

Nếu cần, có thể nhờ hỗ trợ: skeleton notebook, đoạn code crawl mẫu, hoặc checklist trực quan hóa.
