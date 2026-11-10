# SmartBudget – FNB App Academy Unit 6 Capstone

SmartBudget is a personal finance management web application built with Python and Flet. It demonstrates Object-Oriented Programming (OOP), SQLite persistence, multi-view navigation, CRUD operations, reporting, and automated tests.

## Features

- Dashboard with balance, income, expenses, recent activity and budget snapshot.
- Transaction management: create, read, update, delete and search income/expenses.
- Monthly category budgets with progress indicators.
- Reports with category expense breakdown.
- CSV export of transactions.
- SQLite database persistence.
- Sample data is inserted automatically into a new/empty database so the app has something to demonstrate. Sample records are labeled "(sample)" and can be edited or deleted.

## Requirements

- Python 3.10 or later
- pip

## Setup

### macOS / Linux

```bash
cd yourname_smartbudget_app
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
cd yourname_smartbudget_app
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the web application

```bash
flet run --web --port 8550
```

Open the local URL printed in the terminal. Press `Ctrl+C` in the terminal to stop the server.

## Run automated tests

From the project root:

```bash
python -m unittest discover -s tests -v
```

## Data storage

The application creates `smartbudget.db` in the project folder on first run. SQLite stores transactions and budgets. Keep this file if you want to retain the data you entered. Do not include private financial information in a coursework submission.

## Main project structure

```text
yourname_smartbudget_app/
├── main.py
├── models/
│   ├── __init__.py
│   ├── transaction.py
│   └── budget.py
├── services/
│   ├── __init__.py
│   └── storage.py
├── tests/
│   ├── __init__.py
│   └── test_storage.py
├── assets/
├── requirements.txt
└── README.md
```

## Capstone learning outcomes demonstrated

1. Plan, build, test and refine a complete application.
2. Use OOP data models (`Transaction`, `Budget`) and a storage service.
3. Integrate persistent SQLite storage.
4. Build a multi-view Flet web interface.
5. Test persistence and CRUD operations with Python `unittest`.
6. Provide a clean, consistent interface and useful data feedback.

## Important limitations

This is an educational, single-user local application. It does not provide user accounts, cloud synchronization, bank integration, encryption, or financial advice. The SQLite database is local to the machine running the app. For a production multi-user service, a server-side database, authentication, access controls, backups and deployment security would be required.
