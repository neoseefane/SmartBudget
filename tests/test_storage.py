import tempfile
import unittest
from datetime import date
from pathlib import Path

from models.transaction import Transaction
from models.budget import Budget
from services.storage import StorageService

class StorageServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Path(self.temp_dir.name) / "test.db"
        self.store = StorageService(self.db)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_demo_data_is_seeded_once(self):
        self.assertGreaterEqual(len(self.store.list_transactions()), 5)
        first_count = len(self.store.list_transactions())
        StorageService(self.db)
        self.assertEqual(len(self.store.list_transactions()), first_count)

    def test_create_update_delete_transaction(self):
        tx = Transaction(
            id=None,
            title="Test salary",
            amount=5000,
            kind="Income",
            category="Salary",
            transaction_date="2026-11-09"
        )
        tx_id = self.store.save_transaction(tx)
        self.assertTrue(any(item.id == tx_id for item in self.store.list_transactions()))

        updated = Transaction(
            id=tx_id,
            title="Updated salary",
            amount=5500,
            kind="Income",
            category="Salary",
            transaction_date="2026-11-09"
        )
        self.store.save_transaction(updated)
        saved = next(item for item in self.store.list_transactions() if item.id == tx_id)
        self.assertEqual(saved.amount, 5500)

        self.store.delete_transaction(tx_id)
        self.assertFalse(any(item.id == tx_id for item in self.store.list_transactions()))

    def test_budget_upsert(self):
        self.store.save_budget(Budget(None, "Books", 400))
        self.store.save_budget(Budget(None, "Books", 600))
        books = [b for b in self.store.list_budgets() if b.category.lower() == "books"]
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0].monthly_limit, 600)

    def test_category_expense_total(self):
        tx = Transaction(
            id=None,
            title="Book",
            amount=100,
            kind="Expense",
            category="Books",
            transaction_date=date.today().isoformat()
        )

        self.store.save_transaction(tx)
        self.assertEqual(self.store.category_expenses("Books"), 100)

if __name__ == "__main__":
    unittest.main()