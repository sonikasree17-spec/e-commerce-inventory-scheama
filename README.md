# E-Commerce Inventory Management System

A runnable web app based on the uploaded SQL project documents. It includes product/category/supplier/customer management, stock adjustments, low-stock alerts, inventory valuation, customer orders, automatic stock deduction, and a read-only SQL query lab.

## Run on Windows

1. Install Python 3.10 or newer.
2. Extract this ZIP to a folder.
3. Open Command Prompt or PowerShell in that folder.
4. Run:

```bash
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

5. The app opens in your browser, usually at `http://localhost:8501`.

## Run on macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

## Data and reset

The app creates `inventory.db` automatically on first run and seeds the sample products, categories, suppliers, customers, and orders from the supplied project. To reset to the original sample data, stop the app, delete `inventory.db`, and run it again.

## Notes

- This is a local academic/demo application, not a production deployment.
- SQLite is used so the app can run without a separate MySQL server.
- The SQL Query Lab accepts one read-only `SELECT` statement at a time.
