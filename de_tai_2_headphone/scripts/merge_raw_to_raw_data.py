import os
import pandas as pd

"""
Gộp 3 file raw (Cellphones, GearVN, Phong Vũ) thành một file:
- Đọc các file mới nhất trong raw_data/ theo pattern
- Nối lại, drop trùng theo url
- Lưu thành raw_data/raw_data.csv
"""

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_DIR, "raw_data")

SOURCES = [
    "headphone_cellphones",
    "headphone_gearvn",
    "headphone_phongvu",
]


def latest_file(prefix: str) -> str | None:
    files = [f for f in os.listdir(RAW_DIR) if f.startswith(prefix) and f.endswith(".csv")]
    if not files:
        return None
    files.sort()  # tên có timestamp nên file cuối cùng là mới nhất
    return os.path.join(RAW_DIR, files[-1])


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    paths = []
    for prefix in SOURCES:
        p = latest_file(prefix)
        if p and os.path.isfile(p):
            paths.append(p)
            print(f"Found raw file for {prefix}: {p}")
        else:
            print(f"WARNING: Không tìm thấy file cho prefix {prefix}")

    if not paths:
        print("Không có file raw nào để gộp.")
        return

    dfs = [pd.read_csv(p) for p in paths]
    df_all = pd.concat(dfs, ignore_index=True)
    print("Số dòng trước khi drop trùng:", len(df_all))

    df_all = df_all.drop_duplicates(subset=["url"])
    print("Số dòng sau khi drop trùng url:", len(df_all))

    out_path = os.path.join(RAW_DIR, "raw_data.csv")
    df_all.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("Đã lưu file gộp:", out_path)


if __name__ == "__main__":
    main()

