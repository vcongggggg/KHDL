import os
import sys
import pandas as pd
from datasets import load_dataset
from sklearn.model_selection import train_test_split

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Xoa cac file cu neu ton tai
for f in ['raw_data_train.csv', 'raw_data_test.csv']:
    if os.path.exists(f):
        os.remove(f)
        print(f"Da xoa: {f}")

# Cau hinh so dong phu hop may 16GB RAM
TRAIN_SIZE   = 30000
TEST_SIZE    = 7500
TOTAL_NEEDED = TRAIN_SIZE + TEST_SIZE  # 37.500 dong
RANDOM_STATE = 42

print(f"Dang tai {TOTAL_NEEDED} dong tu HuggingFace...")
dataset = load_dataset(
    "tinixai/vietnamese-job-descriptions",
    split=f"train[:{TOTAL_NEEDED}]"
)

df = pd.DataFrame(dataset)
print(f"Da tai ve {len(df)} dong")

# Chia train / test
train_df, test_df = train_test_split(df, test_size=TEST_SIZE, random_state=RANDOM_STATE)

# Luu file moi nho gon
train_df.to_csv('raw_data_train.csv', index=False)
test_df.to_csv('raw_data_test.csv',  index=False)

print(f"Luu xong!")
print(f"  raw_data_train.csv : {len(train_df)} dong")
print(f"  raw_data_test.csv  : {len(test_df)} dong")
