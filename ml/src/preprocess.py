"""Data preprocessing and tokenization for Guard-IA ML pipeline.

Loads raw email datasets (CSV), cleans text, and produces
stratified train/val/test splits ready for fine-tuning.
"""

import re
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import (
    DATA_RAW_DIR,
    DATA_SPLITS_DIR,
    RANDOM_SEED,
    TEST_SPLIT,
    TRAIN_SPLIT,
    VAL_SPLIT,
)

# HTML tag removal
_HTML_TAG_RE = re.compile(r"<[^>]+>")
# Multiple whitespace normalization
_MULTI_WS_RE = re.compile(r"\s+")


def load_raw_data(path: str = DATA_RAW_DIR) -> pd.DataFrame:
    """Load raw email dataset from CSV files in the data directory.

    Expects CSV with at least two columns:
      - text: email body (subject + body concatenated)
      - label: 0 (legitimate) or 1 (phishing)
    """
    data_path = Path(path)
    csv_files = list(data_path.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_path}")

    frames: list[pd.DataFrame] = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)

    # Validate required columns
    required = {"text", "label"}
    missing = required - set(combined.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Drop rows with missing text
    combined = combined.dropna(subset=["text"])
    combined["label"] = combined["label"].astype(int)

    print(f"Loaded {len(combined)} samples from {len(csv_files)} file(s)")
    print(f"Label distribution:\n{combined['label'].value_counts().to_string()}")
    return combined


def preprocess_text(text: str) -> str:
    """Clean and normalize email text for model input.

    Steps:
      1. Remove HTML tags
      2. Normalize whitespace
      3. Strip leading/trailing whitespace
      4. Lowercase
    """
    if not isinstance(text, str):
        return ""
    text = _HTML_TAG_RE.sub(" ", text)
    text = _MULTI_WS_RE.sub(" ", text)
    text = text.strip().lower()
    return text


def split_dataset(
    data: pd.DataFrame,
    train_ratio: float = TRAIN_SPLIT,
    val_ratio: float = VAL_SPLIT,
    test_ratio: float = TEST_SPLIT,
    seed: int = RANDOM_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Stratified split preserving label distribution.

    Default: 80% train, 10% val, 10% test.
    """
    # First split: train vs (val + test)
    val_test_ratio = val_ratio + test_ratio
    train_df, temp_df = train_test_split(
        data,
        test_size=val_test_ratio,
        random_state=seed,
        stratify=data["label"],
    )

    # Second split: val vs test
    relative_test = test_ratio / val_test_ratio
    val_df, test_df = train_test_split(
        temp_df,
        test_size=relative_test,
        random_state=seed,
        stratify=temp_df["label"],
    )

    print(f"Split sizes: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")
    return train_df, val_df, test_df


def save_splits(
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    output_dir: str = DATA_SPLITS_DIR,
) -> None:
    """Save dataset splits to CSV files."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    train.to_csv(out / "train.csv", index=False)
    val.to_csv(out / "val.csv", index=False)
    test.to_csv(out / "test.csv", index=False)
    print(f"Splits saved to {out}")


if __name__ == "__main__":
    data = load_raw_data()
    data["text"] = data["text"].apply(preprocess_text)
    train, val, test = split_dataset(data)
    save_splits(train, val, test)
    print(f"Done: train={len(train)}, val={len(val)}, test={len(test)}")
