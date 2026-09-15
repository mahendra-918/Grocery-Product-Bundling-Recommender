"""
Unit tests for TransactionPreprocessor.
Validates loading, deduplication, and One-Hot encoding dimensions.
"""

import unittest
from pathlib import Path
import pandas as pd
from ml.preprocess import TransactionPreprocessor


class TestTransactionPreprocessor(unittest.TestCase):
    def setUp(self):
        self.preprocessor = TransactionPreprocessor()
        self.sample_baskets = [
            ["citrus fruit", "margarine", "ready soups", "semi-finished bread"],
            ["coffee", "tropical fruit", "yogurt"],
            ["whole milk"],
            ["pip fruit", "yogurt", "cream cheese", "meat spreads"],
            ["other vegetables", "whole milk", "condensed milk", "long life bakery product"],
        ]

    def test_encode_transactions_shape_and_types(self):
        df_encoded, products = self.preprocessor.encode_transactions(self.sample_baskets)
        self.assertIsInstance(df_encoded, pd.DataFrame)
        self.assertEqual(df_encoded.shape[0], 5)
        self.assertEqual(df_encoded.shape[1], len(products))
        self.assertEqual(df_encoded.dtypes.iloc[0], bool)
        self.assertIn("whole milk", products)
        self.assertIn("yogurt", products)

    def test_encode_empty_transactions_raises_error(self):
        with self.assertRaises(ValueError):
            self.preprocessor.encode_transactions([])

    def test_load_real_dataset_integrity(self):
        data_path = Path("data/groceries - groceries.csv")
        if not data_path.exists():
            data_path = Path("data/groceries.csv")

        if data_path.exists():
            transactions = self.preprocessor.load_transactions(data_path)
            self.assertEqual(len(transactions), 9835)

            df_encoded, products = self.preprocessor.encode_transactions(transactions)
            # Verify exact matrix shape (9835, 169)
            self.assertEqual(df_encoded.shape, (9835, 169))
            self.assertIn("whole milk", products)
            self.assertIn("other vegetables", products)
            self.assertIn("rolls/buns", products)


if __name__ == "__main__":
    unittest.main()
