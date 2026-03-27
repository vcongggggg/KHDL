# Tom tat thay doi (Data Cleaning / Encoding)

Tai lieu nay tong hop cac thay doi da duoc cap nhat de dong bo logic xu ly du lieu cho de tai headphone.

## 1) Xu ly `battery_life_hours` dung logic wireless

- Trong `notebooks/02-cleaning_data.ipynb`:
  - Khong con ep tat ca dong wired thanh `battery_life_hours = 0`.
  - Voi dong `is_wireless = 0`, gia tri pin duoc giu `NaN` (khong ap dung).
  - Bo sung co `battery_applicable` de phan biet dong co y nghia pin (wireless) va dong khong ap dung.
- Cap nhat `price_per_battery_hour`:
  - Chi giu gia tri cho dong `battery_applicable == 1`.
  - Dong wired de `NaN` de tranh lam meo thong ke.

## 2) Chuan hoa `connection` ho tro nhieu kieu ket noi

- Trong `notebooks/02-cleaning_data.ipynb`:
  - Ham `normalize_connection()` da duoc doi tu "1 nhan duy nhat" sang "gom nhieu nhan".
  - Vi du:
    - Truoc: `Bluetooth`
    - Sau: `3.5mm+Bluetooth` (neu co ca day va khong day)
- Muc tieu:
  - Phan anh dung san pham hybrid (vua co day vua bluetooth).
  - Van giu logic `is_wireless = 1` neu co bluetooth.

## 3) Sua mismatch `is_wireless = 0` nhung `connection = Bluetooth`

- Nguyen nhan cu: impute categorical theo `brand` thuong gay wired bi dien bluetooth.
- Da sua trong `notebooks/02-cleaning_data.ipynb`:
  - `connection` duoc impute theo nhom `("brand", "is_wireless")`.
  - Fallback theo tung nhom `is_wireless`.
- Ket qua mong doi: giam/loai mismatch wired-bluetooth do impute.

## 4) Outlier theo style slide tham khao (Laptop)

- Da them cell "7.x) Xu ly ngoai le (Outliers)" trong `notebooks/02-cleaning_data.ipynb`:
  - Numeric:
    - Tinh nguong IQR cho `price_vnd`.
    - Tao `price_vnd_capped` va ve truoc/sau (histogram + boxplot).
  - Categorical:
    - Gom nhom Top-N thanh `Other`.
    - Tao `brand_grouped`, `connection_grouped`.
- Quan trong:
  - Da bo sung `price_vnd_original`.
  - Da gan `df["price_vnd"] = df["price_vnd_capped"]` de cac buoc sau dung gia da cap outlier.

## 5) Loai bo hau to "Chinh hang" trong `brand`

- Trong `notebooks/02-cleaning_data.ipynb` (cell 6.1):
  - Bo sung `normalize_brand()`.
  - Loai bo cac token marketing:
    - `chinh hang`, `chinh hang`, `hang chinh hang`, `official`, `authentic`, `genuine`, ...
  - Vi du:
    - `Apple Chinh hang` -> `Apple`
    - `Samsung Chinh hang` -> `Samsung`

## 6) Cap nhat `03-data_encoding.ipynb` de chay an toan voi clean-data moi

- Cell ve "Pin vs Gia" da duoc bo sung:
  - Loc `battery_applicable == 1` (neu co cot nay).
  - Fallback voi file cu: loc `battery_life_hours > 0`.
  - Them filter rule range khi ve:
    - `battery_life_hours` trong `[1, 200]`
    - `weight_gram` trong `[1, 2000]`
- Cell One-Hot Encoding da duoc cap nhat:
  - Neu chua co `brand_grouped` / `connection_grouped` thi tu tao fallback.
  - Mo rong encode cho `connection_grouped`.

## 7) File/hinh da duoc tao them (tieu bieu)

- Figures trong `figures/cleaning_data/`:
  - `outlier_price_hist_before_after.png`
  - `outlier_price_box_before_after.png`
  - `grouped_brand_grouped_bar.png`
  - `grouped_connection_grouped_bar.png`

## 8) Cach chay lai de dong bo ket qua

1. Dong file CSV dang mo (neu co), dac biet:
   - `clean_data/headphone_clean.csv`
2. Chay lai `notebooks/02-cleaning_data.ipynb` tu dau den cuoi.
3. Chay lai `notebooks/03-data_encoding.ipynb`.
4. Kiem tra:
   - `brand` khong con chuoi "Chinh hang".
   - Plot pin/gia khong con diem ngoai range.
   - `price_vnd` da la gia tri sau capping.

---

Neu can, co the doi ten file nay thanh `SUMMARY_CHANGES.md` hoac tach thanh 2 file:
- `SUMMARY_CLEANING.md`
- `SUMMARY_ENCODING.md`
