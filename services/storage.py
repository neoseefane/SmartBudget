import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from models.budget import Budget
from models.transaction import Transaction


class StorageService:
    """Handles all SQLite persistence for SmartBudget"""

    def __init__(self, db_path):
        self.database_path = str(db_path)
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self.create_tables()
        self._seed_demo_data()

    @contextmanager
    def _connect(self):
        """Open a database connection and always close the connection."""
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row

        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def create_tables(self):
        with self._connect() as connection:
            connection.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                kind TEXT NOT NULL CHECK(kind IN ('Income', 'Expense')),
                category TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                note TEXT DEFUALT ''
            )
            """)
            connection.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL UNIQUE COLLATE NOCASE,
                monthly_limit REAL NOT NULL CHECK(monthly_limit > 0)
            )
            """)

    def _seed_demo_data(self):
        """Add clearly labelled sample records only when the database is empty."""
        with self._connect() as connection:
            count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
            if count == 0:
                samples = [
                    ("Monthly salary (sample)", 12500.00, "Income", "Salary", date.today().replace(day=1).isoformat(),
                     "Demo record - edit or delete"),
                    ("Grocery shopping (sample)", 1250.00, "Expense", "Groceries", date.today().isoformat(),
                     "Demo record"),
                    ("Transport (sample)", 650.00, "Expense", "Transport", date.today().isoformat(), "Demo record"),
                    ("Freelance payment (sample)", 1800.00, "Income", "Freelance", date.today().isoformat(),
                     "Demo record"),
                    ("Internet bill (sample)", 599.00, "Expense", "Utilities", date.today().isoformat(), "Demo record"),
                ]
                connection.executemany("""
                    INSERT INTO transactions (title, amount, kind, category, transaction_date, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, samples)

            budget_count = connection.execute("SELECT COUNT(*) FROM budgets").fetchone()[0]
            if budget_count == 0:
                connection.executemany(
                    "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?)",
                    [("Groceries", 2500), ("Transport", 1200), ("Utilities", 1000)],
                )

    def save_transaction(self, transaction: Transaction):
        values = (
            transaction.title,
            transaction.amount,
            transaction.kind,
            transaction.category,
            transaction.transaction_date,
            transaction.note
        )

        with self._connect() as connection:
            if transaction.id is None:
                cursor = connection.execute("""
                    INSERT INTO transactions 
                    (title, amount, kind, category, transaction_date, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, values)
                return cursor.lastrowid
            connection.execute("""
            UPDATE transactions 
            SET title=?, amount=?, kind=?, category=?, transaction_date=?, note=?
            WHERE id=?
            """, values + (transaction.id,))
            return transaction.id

    def list_transactions(self):
        with self._connect() as connection:
            rows = connection.execute(
            "SELECT * FROM transactions ORDER BY transaction_date DESC, id DESC"
            ).fetchall()
        return [Transaction(
            id=row["id"], title=row["title"], amount=row["amount"], kind=row["kind"], category=row["category"], transaction_date=row["transaction_date"], note=row["note"] or ""
        ) for row in rows]

    def delete_transaction(self, transaction_id: int):
        with self._connect() as connection:
            connection.execute("DELETE FROM transactions WHERE id=?", (transaction_id,))

    def save_budget(self, budget: Budget):
        with self._connect() as connection:
            connection.execute("""
                INSERT INTO budgets (category, monthly_limit) VALUES (?, ?)
                ON CONFLICT(category) DO UPDATE SET monthly_limit=excluded.monthly_limit
            """, (budget.category.strip(), budget.monthly_limit))

    def list_budgets(self):
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM budgets ORDER BY  category").fetchall()
        return [Budget(id=row["id"], category=row["category"], monthly_limit=row["monthly_limit"]) for row in rows]

    def category_expenses(self, category: str):
        """Return this month's expenses for a given category."""
        month = date.today().strftime("%Y-%m")
        with self._connect() as connection:
            row = connection.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM transactions
                WHERE kind='Expense' AND category=? COLLATE NOCASE
                    AND substr(transaction_date, 1, 7)=?
            """, (category, month)).fetchone()
        return float(row[0])

    def expenses_by_category(self):
        """Return this month's expense totals grouped by category."""
        month = date.today().strftime("%Y-%m")
        with self._connect() as connection:
            rows = connection.execute("""
                SELECT category, SUM(amount) AS total
                FROM transactions
                WHERE kind='Expense' AND substr(transaction_date, 1, 7)=?
                GROUP BY category
                ORDER BY total DESC
            """, (month, )).fetchall()
        return {row["category"]: float(row["total"]) for row in rows}
