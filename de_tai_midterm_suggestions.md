## Gợi ý đề tài giữa kỳ KHDL (nhóm 2 người)

**ĐÃ CHỐT:** Đề tài 1 — **Dự đoán giá laptop từ cấu hình phần cứng** (crawl TGDĐ / FPT Shop / Phong Vũ,…). Chi tiết đề tài đã chốt: xem file `GK/de_tai_1_chot.md`.

---

Tất cả đề tài dưới đây đều:
- Cho phép **tự crawl dữ liệu từ web**
- Dễ đạt **> 1000 mẫu** và **≥ 5 biến**
- Có thể làm đầy đủ pipeline: **thu thập → làm sạch → mã hoá → feature engineering → trực quan hoá → mô hình → kết luận**
- Tránh trùng các đề tài đã thấy trong file đăng ký (USD/VND, giá vàng, BĐS, cổ phiếu, IMDb, IT jobs, khách sạn,...)

---

### Đề tài 1 — Dự đoán giá laptop từ cấu hình phần cứng

- **Mô tả ngắn**: Crawl dữ liệu laptop mới bán tại Việt Nam (ví dụ: Thế Giới Di Động, FPT Shop, Phong Vũ, GearVN, CellphoneS).  
  Mỗi dòng là một mẫu laptop với các thông tin cấu hình và **giá bán**.
- **Bài toán**: Hồi quy (regression) — dự đoán **giá laptop** từ cấu hình.
- **Biến mục tiêu (Y) gợi ý**: `price_vnd`.
- **Biến giải thích (X) gợi ý**: hãng, dòng CPU, số nhân luồng, RAM (GB), SSD/HDD (GB), loại card đồ hoạ (onboard/dedicated), kích thước màn hình (inch), độ phân giải, tần số quét, cân nặng, năm ra mắt,...
- **Nguồn crawl tham khảo**:
  - `https://www.thegioididong.com/laptop`
  - `https://fptshop.com.vn/may-tinh-xach-tay`
  - `https://phongvu.vn/c/laptop`
- **Ưu điểm**:
  - Cấu trúc HTML khá rõ ràng, dễ parse.
  - Nhiều biến kỹ thuật nên làm **feature engineering** rất phong phú (ví dụ: performance score, ppi, price per GB RAM,...).

---

### Đề tài 2 — Phân tích và dự đoán điểm đánh giá sản phẩm điện tử trên sàn TMĐT

- **Mô tả ngắn**: Crawl dữ liệu các sản phẩm điện thoại / laptop / phụ kiện trên Tiki hoặc Shopee: tên sản phẩm, danh mục, giá, số sao trung bình, số lượng đánh giá, số lượng đã bán, freeship, voucher, thương hiệu,...
- **Bài toán** (có thể chọn 1 trong 2):
  - Hồi quy: dự đoán **điểm rating trung bình** (sao) từ thông tin sản phẩm.
  - Phân lớp: dự đoán sản phẩm thuộc nhóm **rating cao / trung bình / thấp**.
- **Biến mục tiêu (Y) gợi ý**:
  - `rating` (liên tục 1–5), hoặc
  - `rating_label` (High / Medium / Low).
- **Biến giải thích (X) gợi ý**: giá, brand, danh mục, có freeship hay không, số lượng đã bán, số lượng đánh giá, có Mall/Official Store hay không, số lượng hình ảnh, độ dài mô tả,...
- **Nguồn crawl tham khảo**:
  - `https://tiki.vn` (các category điện tử)
  - `https://shopee.vn` (điện thoại & phụ kiện, laptop,...)
- **Ưu điểm**:
  - Dễ đủ **> 1000 sản phẩm**.
  - Phần **EDA** và **trực quan hoá** rất trực quan (giá vs rating, số lượng đánh giá vs rating, tác động của freeship,...).

---

### Đề tài 3 — Dự đoán điểm review quán ăn/quán cà phê từ thông tin quán

- **Mô tả ngắn**: Crawl danh sách quán ăn/cà phê từ Foody hoặc Google Maps (thông qua HTML, không cần API): tên quán, loại hình (nhà hàng, cà phê, trà sữa,...), mức giá, khu vực, số review, giờ mở cửa, tiện ích (wifi, điều hoà, chỗ đậu xe,...), điểm rating.
- **Bài toán**:
  - Hồi quy: dự đoán **điểm rating** của quán.
  - Hoặc phân lớp: quán **điểm cao / trung bình / thấp**.
- **Biến mục tiêu (Y) gợi ý**: `rating` hoặc `rating_label`.
- **Biến giải thích (X) gợi ý**: loại quán, khoảng giá, quận/huyện, số review, có giao hàng hay không, có chỗ đậu xe, có điều hoà, có không gian mở, thời gian mở cửa,...
- **Nguồn crawl tham khảo**:
  - `https://www.foody.vn`
  - Google Maps web (tìm theo từ khoá và khu vực).
- **Ưu điểm**:
  - Gần gũi với đời sống sinh viên, phần **phân tích trực quan** (bản đồ, heatmap theo khu vực) rất thú vị.

---

### Đề tài 4 — Dự đoán giá xe máy cũ từ thông tin tin đăng

- **Mô tả ngắn**: Crawl tin đăng bán **xe máy cũ** trên Chợ Tốt: hãng xe, dòng xe, năm sản xuất, dung tích (cc), số km đã chạy, tình trạng (mới/đã dùng), khu vực, mô tả ngắn, giá đăng bán,...
- **Bài toán**: Hồi quy — dự đoán **giá xe máy cũ**.
- **Biến mục tiêu (Y) gợi ý**: `price_vnd`.
- **Biến giải thích (X) gợi ý**: hãng, dòng, năm sản xuất, dung tích, số km, tỉnh/thành, số ảnh, độ dài mô tả, loại người bán (cá nhân/cửa hàng),...
- **Nguồn crawl tham khảo**:
  - `https://xe.chotot.com/mua-ban-xe-may`
- **Ưu điểm**:
  - Dữ liệu nhiều, đa dạng vùng miền.
  - Có thể thử thêm **phân tích văn bản** (text description) nếu muốn nâng độ khó.

---

### Đề tài 5 — Phân tích và dự đoán số lượt xem video YouTube từ metadata

- **Mô tả ngắn**: Thu thập dữ liệu các video thuộc một số kênh hoặc chủ đề (music, education, gaming,...) bằng cách crawl HTML trang YouTube (hoặc dùng API nếu cho phép): tiêu đề, độ dài video, ngày đăng, số like, số comment, có xuất hiện từ khoá nào trong tiêu đề, thuộc playlist nào,...
- **Bài toán**:
  - Hồi quy: dự đoán **số lượt xem** sau một khoảng thời gian (ví dụ: sau 30 ngày kể từ ngày đăng).
  - Hoặc phân lớp: video **hot / bình thường / ít view**.
- **Biến mục tiêu (Y) gợi ý**: `views_30d` hoặc `view_level`.
- **Biến giải thích (X) gợi ý**: độ dài video, chủ đề, độ dài tiêu đề, có emoji trong tiêu đề, có số/từ “official MV”, ngày trong tuần đăng, khung giờ đăng,...
- **Nguồn crawl tham khảo**:
  - Trang kênh và trang kết quả tìm kiếm trên `https://www.youtube.com`.
- **Ưu điểm**:
  - Dữ liệu dễ hiểu, trực quan; nhiều hướng **EDA** thú vị (ảnh hưởng tiêu đề, độ dài, giờ đăng,... đến view).

---

### Gợi ý chọn đề tài cho nhóm 2 người

- Nếu muốn **dễ crawling + rõ ràng về cấu trúc dữ liệu**: ưu tiên **Đề tài 1 (giá laptop)** hoặc **Đề tài 2 (rating sản phẩm TMĐT)**.  
- Nếu muốn **gần gũi đời sống, nhiều ý tưởng trực quan hoá**: cân nhắc **Đề tài 3 (quán ăn/cà phê)** hoặc **Đề tài 4 (xe máy cũ)**.  
- Nếu thích **mạng xã hội / content**: chọn **Đề tài 5 (video YouTube)**.

