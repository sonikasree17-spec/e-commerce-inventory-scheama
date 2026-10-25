import sqlite3
from pathlib import Path
from datetime import date
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).with_name("inventory.db")

st.set_page_config(page_title="E-Commerce Inventory", page_icon="📦", layout="wide")

def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS Categories (
            category_id INTEGER PRIMARY KEY,
            category_name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS Suppliers (
            supplier_id INTEGER PRIMARY KEY,
            supplier_name TEXT NOT NULL,
            phone TEXT
        );
        CREATE TABLE IF NOT EXISTS Products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK(stock_quantity >= 0),
            FOREIGN KEY(category_id) REFERENCES Categories(category_id),
            FOREIGN KEY(supplier_id) REFERENCES Suppliers(supplier_id)
        );
        CREATE TABLE IF NOT EXISTS Customers (
            customer_id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            email TEXT,
            phone TEXT
        );
        CREATE TABLE IF NOT EXISTS Orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            total_amount REAL NOT NULL DEFAULT 0,
            FOREIGN KEY(customer_id) REFERENCES Customers(customer_id)
        );
        CREATE TABLE IF NOT EXISTS Order_Items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            subtotal REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES Orders(order_id),
            FOREIGN KEY(product_id) REFERENCES Products(product_id)
        );
        """)
        count = conn.execute("SELECT COUNT(*) FROM Products").fetchone()[0]
        if count == 0:
            conn.executemany("INSERT OR IGNORE INTO Categories VALUES (?,?)", [
                (1, "Electronics"), (2, "Clothing"), (3, "Accessories")])
            conn.executemany("INSERT OR IGNORE INTO Suppliers VALUES (?,?,?)", [
                (1, "ABC Suppliers", "9876543210"), (2, "XYZ Traders", "9876501234")])
            conn.executemany("INSERT OR IGNORE INTO Products VALUES (?,?,?,?,?,?)", [
                (101, "Headphones", 1, 1, 1500, 20),
                (102, "T-Shirt", 2, 2, 500, 50),
                (103, "Smart Watch", 1, 1, 3000, 10),
                (104, "Handbag", 3, 2, 1200, 15)])
            conn.executemany("INSERT OR IGNORE INTO Customers VALUES (?,?,?,?)", [
                (1, "Arun", "arun@gmail.com", "9876543211"),
                (2, "Priya", "priya@gmail.com", "9876543212")])
            conn.executemany("INSERT OR IGNORE INTO Orders VALUES (?,?,?,?)", [
                (1001, 1, "2026-10-20", 3000), (1002, 2, "2026-10-21", 1000)])
            conn.executemany("INSERT OR IGNORE INTO Order_Items (item_id,order_id,product_id,quantity,subtotal) VALUES (?,?,?,?,?)", [
                (1, 1001, 101, 2, 3000), (2, 1002, 102, 2, 1000)])

def df_query(sql, params=()):
    with connect() as conn:
        return pd.read_sql_query(sql, conn, params=params)

def run_write(sql, params=()):
    with connect() as conn:
        conn.execute(sql, params)
        conn.commit()

init_db()

st.title("📦 E-Commerce Inventory Management")
st.caption("A working inventory application powered by Streamlit + SQLite, based on your SQL mini-project.")

with st.sidebar:
    st.header("Navigation")
    page = st.radio("Open section", [
        "Dashboard", "Products & Stock", "Categories", "Suppliers",
        "Customers", "Orders", "SQL Query Lab"
    ])
    st.divider()
    st.caption("Demo data is stored locally in inventory.db.")

if page == "Dashboard":
    metrics = df_query("""
        SELECT COUNT(*) products,
               COALESCE(SUM(stock_quantity),0) units,
               COALESCE(SUM(price * stock_quantity),0) inventory_value,
               COALESCE(SUM(CASE WHEN stock_quantity < 15 THEN 1 ELSE 0 END),0) low_stock
        FROM Products
    """).iloc[0]
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Products", int(metrics["products"]))
    c2.metric("Units in stock", int(metrics["units"]))
    c3.metric("Inventory value", f"₹{metrics['inventory_value']:,.2f}")
    c4.metric("Low-stock products", int(metrics["low_stock"]))
    left, right = st.columns(2)
    with left:
        st.subheader("Stock by product")
        stock = df_query("SELECT product_name, stock_quantity FROM Products ORDER BY stock_quantity DESC")
        st.bar_chart(stock.set_index("product_name"))
    with right:
        st.subheader("Inventory value by category")
        cat = df_query("""SELECT c.category_name, SUM(p.price*p.stock_quantity) value
                          FROM Products p JOIN Categories c ON c.category_id=p.category_id
                          GROUP BY c.category_name ORDER BY value DESC""")
        if not cat.empty:
            st.bar_chart(cat.set_index("category_name"))
    st.subheader("Products needing attention (stock < 15)")
    low = df_query("""SELECT product_id, product_name, stock_quantity, price
                      FROM Products WHERE stock_quantity < 15 ORDER BY stock_quantity""")
    st.dataframe(low, use_container_width=True, hide_index=True)
    st.subheader("Recent orders")
    st.dataframe(df_query("""SELECT o.order_id, c.customer_name, o.order_date, o.total_amount
                             FROM Orders o JOIN Customers c ON c.customer_id=o.customer_id
                             ORDER BY o.order_date DESC"""), use_container_width=True, hide_index=True)

elif page == "Products & Stock":
    st.subheader("Product catalogue")
    products = df_query("""SELECT p.product_id, p.product_name, c.category_name, s.supplier_name,
                                  p.price, p.stock_quantity, p.price*p.stock_quantity AS stock_value
                           FROM Products p JOIN Categories c ON p.category_id=c.category_id
                           JOIN Suppliers s ON p.supplier_id=s.supplier_id ORDER BY p.product_id""")
    st.dataframe(products, use_container_width=True, hide_index=True)
    st.divider()
    st.subheader("Add a product")
    cats = df_query("SELECT category_id, category_name FROM Categories")
    sups = df_query("SELECT supplier_id, supplier_name FROM Suppliers")
    if cats.empty or sups.empty:
        st.info("Add at least one category and supplier before adding a product.")
    else:
        with st.form("add_product", clear_on_submit=True):
            name = st.text_input("Product name")
            a,b,c = st.columns(3)
            category = a.selectbox("Category", cats["category_name"].tolist())
            supplier = b.selectbox("Supplier", sups["supplier_name"].tolist())
            price = c.number_input("Price (₹)", min_value=0.0, value=100.0, step=50.0)
            stock_qty = st.number_input("Opening stock", min_value=0, value=0, step=1)
            submitted = st.form_submit_button("Add product")
            if submitted:
                if not name.strip():
                    st.error("Enter a product name.")
                else:
                    cat_id = int(cats.loc[cats.category_name == category, "category_id"].iloc[0])
                    sup_id = int(sups.loc[sups.supplier_name == supplier, "supplier_id"].iloc[0])
                    try:
                        run_write("INSERT INTO Products(product_name,category_id,supplier_id,price,stock_quantity) VALUES (?,?,?,?,?)",
                                  (name.strip(), cat_id, sup_id, price, stock_qty))
                        st.success("Product added.")
                        st.rerun()
                    except sqlite3.IntegrityError as e:
                        st.error(f"Could not add product: {e}")
    st.divider()
    st.subheader("Update stock")
    prod = df_query("SELECT product_id, product_name, stock_quantity FROM Products ORDER BY product_name")
    if not prod.empty:
        with st.form("update_stock"):
            selected = st.selectbox("Product", prod["product_name"].tolist())
            current = int(prod.loc[prod.product_name == selected, "stock_quantity"].iloc[0])
            st.write(f"Current stock: **{current}**")
            mode = st.radio("Adjustment", ["Set exact quantity", "Add units", "Remove units"], horizontal=True)
            qty = st.number_input("Quantity", min_value=0, value=current if mode == "Set exact quantity" else 1, step=1)
            update = st.form_submit_button("Save stock")
            if update:
                product_id = int(prod.loc[prod.product_name == selected, "product_id"].iloc[0])
                if mode == "Set exact quantity":
                    new_qty = int(qty)
                elif mode == "Add units":
                    new_qty = current + int(qty)
                else:
                    new_qty = current - int(qty)
                if new_qty < 0:
                    st.error("Stock cannot be negative.")
                else:
                    run_write("UPDATE Products SET stock_quantity=? WHERE product_id=?", (new_qty, product_id))
                    st.success(f"Stock updated to {new_qty}.")
                    st.rerun()
    st.divider()
    st.subheader("Edit product price")
    if not prod.empty:
        with st.form("price_form"):
            pname = st.selectbox("Product to edit", prod["product_name"].tolist(), key="price_product")
            new_price = st.number_input("New price (₹)", min_value=0.0, value=100.0, step=50.0)
            if st.form_submit_button("Update price"):
                pid = int(prod.loc[prod.product_name == pname, "product_id"].iloc[0])
                run_write("UPDATE Products SET price=? WHERE product_id=?", (new_price, pid))
                st.success("Price updated.")
                st.rerun()

elif page == "Categories":
    st.subheader("Categories")
    st.dataframe(df_query("SELECT * FROM Categories ORDER BY category_id"), use_container_width=True, hide_index=True)
    with st.form("add_category", clear_on_submit=True):
        name = st.text_input("New category name")
        if st.form_submit_button("Add category"):
            if name.strip():
                try:
                    run_write("INSERT INTO Categories(category_name) VALUES (?)", (name.strip(),))
                    st.success("Category added.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("That category already exists.")
            else:
                st.error("Enter a category name.")

elif page == "Suppliers":
    st.subheader("Suppliers")
    st.dataframe(df_query("SELECT * FROM Suppliers ORDER BY supplier_id"), use_container_width=True, hide_index=True)
    with st.form("add_supplier", clear_on_submit=True):
        name = st.text_input("Supplier name")
        phone = st.text_input("Phone")
        if st.form_submit_button("Add supplier"):
            if name.strip():
                run_write("INSERT INTO Suppliers(supplier_name,phone) VALUES (?,?)", (name.strip(), phone.strip()))
                st.success("Supplier added.")
                st.rerun()
            else:
                st.error("Enter a supplier name.")

elif page == "Customers":
    st.subheader("Customers")
    st.dataframe(df_query("SELECT * FROM Customers ORDER BY customer_id"), use_container_width=True, hide_index=True)
    with st.form("add_customer", clear_on_submit=True):
        name = st.text_input("Customer name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        if st.form_submit_button("Add customer"):
            if name.strip():
                run_write("INSERT INTO Customers(customer_name,email,phone) VALUES (?,?,?)",
                          (name.strip(), email.strip(), phone.strip()))
                st.success("Customer added.")
                st.rerun()
            else:
                st.error("Enter a customer name.")

elif page == "Orders":
    st.subheader("Order history")
    st.dataframe(df_query("""SELECT o.order_id, c.customer_name, o.order_date, o.total_amount
                             FROM Orders o JOIN Customers c ON c.customer_id=o.customer_id
                             ORDER BY o.order_date DESC"""), use_container_width=True, hide_index=True)
    st.subheader("Create order")
    customers = df_query("SELECT customer_id, customer_name FROM Customers")
    products = df_query("SELECT product_id, product_name, price, stock_quantity FROM Products")
    if customers.empty or products.empty:
        st.info("Add at least one customer and product before creating an order.")
    else:
        with st.form("new_order"):
            customer_name = st.selectbox("Customer", customers["customer_name"].tolist())
            product_name = st.selectbox("Product", products["product_name"].tolist())
            available = int(products.loc[products.product_name == product_name, "stock_quantity"].iloc[0])
            price = float(products.loc[products.product_name == product_name, "price"].iloc[0])
            quantity = st.number_input("Quantity", min_value=1, max_value=max(1, available), value=1, step=1)
            st.write(f"Available stock: **{available}** · Unit price: **₹{price:,.2f}** · Subtotal: **₹{price*quantity:,.2f}**")
            order_date = st.date_input("Order date", value=date.today())
            create = st.form_submit_button("Create order")
            if create:
                if available < quantity:
                    st.error("Not enough stock for this order.")
                else:
                    cid = int(customers.loc[customers.customer_name == customer_name, "customer_id"].iloc[0])
                    pid = int(products.loc[products.product_name == product_name, "product_id"].iloc[0])
                    total = price * int(quantity)
                    with connect() as conn:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO Orders(customer_id,order_date,total_amount) VALUES (?,?,?)",
                                    (cid, str(order_date), total))
                        oid = cur.lastrowid
                        cur.execute("INSERT INTO Order_Items(order_id,product_id,quantity,subtotal) VALUES (?,?,?,?)",
                                    (oid, pid, int(quantity), total))
                        cur.execute("UPDATE Products SET stock_quantity=stock_quantity-? WHERE product_id=?",
                                    (int(quantity), pid))
                        conn.commit()
                    st.success(f"Order #{oid} created. Stock reduced by {int(quantity)}.")
                    st.rerun()
    st.subheader("Order line items")
    st.dataframe(df_query("""SELECT o.order_id, c.customer_name, p.product_name, i.quantity, i.subtotal, o.order_date
                             FROM Order_Items i JOIN Orders o ON i.order_id=o.order_id
                             JOIN Customers c ON c.customer_id=o.customer_id
                             JOIN Products p ON p.product_id=i.product_id
                             ORDER BY o.order_id DESC"""), use_container_width=True, hide_index=True)

elif page == "SQL Query Lab":
    st.subheader("SQL Query Lab")
    st.write("Run read-only SELECT queries against the app database. Use this to explore the SQL concepts from your project.")
    examples = {
        "All products": "SELECT * FROM Products;",
        "Product categories": "SELECT p.product_name, c.category_name, p.price FROM Products p JOIN Categories c ON p.category_id=c.category_id;",
        "Available stock": "SELECT product_name, stock_quantity FROM Products;",
        "Low stock (< 15)": "SELECT product_name, stock_quantity FROM Products WHERE stock_quantity < 15;",
        "Customer orders": "SELECT c.customer_name, o.order_id, o.order_date, o.total_amount FROM Customers c JOIN Orders o ON c.customer_id=o.customer_id;",
        "Inventory value": "SELECT SUM(price * stock_quantity) AS total_inventory_value FROM Products;",
        "Order details": "SELECT o.order_id, p.product_name, i.quantity, i.subtotal FROM Order_Items i JOIN Products p ON i.product_id=p.product_id JOIN Orders o ON i.order_id=o.order_id;",
    }
    chosen = st.selectbox("Example query", list(examples.keys()))
    query = st.text_area("SQL (SELECT only)", value=examples[chosen], height=120)
    if st.button("Run query"):
        cleaned = query.strip().rstrip(";")
        if not cleaned.lower().startswith("select") or ";" in cleaned:
            st.error("For safety, this query lab only accepts a single SELECT statement.")
        else:
            try:
                st.dataframe(df_query(cleaned), use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"SQL error: {e}")

st.divider()
st.caption("Academic demo application · Data persists in the local SQLite database file.")
