"""
Transaction Preprocessing & One-Hot Encoding Pipeline.
Transforms raw grocery transaction records into clean baskets and boolean incidence matrices.
"""

from pathlib import Path
from typing import List, Tuple, Union
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder


class TransactionPreprocessor:
    """Loads, cleans, and encodes grocery basket transactions."""

    def __init__(self):
        self.encoder = TransactionEncoder()
        self.unique_products: List[str] = []

    def load_transactions(self, file_path: Union[str, Path]) -> List[List[str]]:
        """
        Reads CSV and produces a clean, trimmed, non-empty list of unique items per basket.
        Supports both the wide CSV ('Item 1' ... 'Item 32') and line-by-line comma-separated format.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Transaction file not found at: {file_path}")

        # Check if first line contains wide headers
        with open(file_path, "r", encoding="utf-8") as f:
            first_line = f.readline()

        transactions: List[List[str]] = []

        if "Item 1" in first_line or "Item(s)" in first_line:
            df = pd.read_csv(file_path)
            item_cols = [c for c in df.columns if c.startswith("Item ")]
            for row in df[item_cols].values:
                # Strip spaces, lowercase, drop empty/NaN items
                basket = [str(item).strip().lower() for item in row if pd.notna(item) and str(item).strip()]
                if basket:
                    # Deduplicate items within the same basket using set()
                    transactions.append(sorted(list(set(basket))))
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    basket = [item.strip().lower() for item in line.split(",") if item.strip()]
                    if basket:
                        transactions.append(sorted(list(set(basket))))

        return transactions

    def encode_transactions(self, transactions: List[List[str]]) -> Tuple[pd.DataFrame, List[str]]:
        """
        Converts lists of item transactions into a one-hot boolean DataFrame (binary incidence matrix).
        Returns:
            df_encoded (pd.DataFrame): Boolean DataFrame of shape (N, M)
            unique_products (List[str]): Alphabetically sorted list of all unique products
        """
        if not transactions:
            raise ValueError("Transactions list cannot be empty.")

        encoded_array = self.encoder.fit_transform(transactions)
        df_encoded = pd.DataFrame(encoded_array, columns=self.encoder.columns_)
        self.unique_products = sorted(list(self.encoder.columns_))
        return df_encoded, self.unique_products
