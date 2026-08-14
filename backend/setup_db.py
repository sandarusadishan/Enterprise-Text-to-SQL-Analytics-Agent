import sqlite3

# Database එක සාදා connection එක Open කරගැනීම
conn = sqlite3.connect("company_sales.db")
cursor = conn.cursor()

# 1. Customers Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    created_at DATE
)
''')

# 2. Products Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL
)
''')

# 3. Orders Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    total_amount REAL,
    order_date DATE,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY(product_id) REFERENCES products(product_id)
)
''')

# Sample Data ඇතුළත් කිරීම (මීට කලින් Data නැත්නම් විතරක් Add වේ)
cursor.execute("SELECT COUNT(*) FROM customers")
if cursor.fetchone()[0] == 0:
    cursor.executemany('''
    INSERT INTO customers (name, country, created_at) VALUES (?, ?, ?)
    ''', [
        ('Kasun Perera', 'Sri Lanka', '2025-01-10'),
        ('John Doe', 'USA', '2025-02-15'),
        ('Amali Silva', 'Sri Lanka', '2025-03-01'),
        ('Saman Kumara', 'Sri Lanka', '2025-03-10')
    ])

    cursor.executemany('''
    INSERT INTO products (product_name, category, price) VALUES (?, ?, ?)
    ''', [
        ('Laptop', 'Electronics', 1200.00),
        ('Smart Phone', 'Electronics', 800.00),
        ('Office Chair', 'Furniture', 150.00),
        ('Wireless Mouse', 'Electronics', 25.00)
    ])

    cursor.executemany('''
    INSERT INTO orders (customer_id, product_id, quantity, total_amount, order_date) VALUES (?, ?, ?, ?, ?)
    ''', [
        (1, 1, 1, 1200.00, '2026-01-15'),
        (1, 4, 2, 50.00, '2026-01-20'),
        (2, 2, 1, 800.00, '2026-02-01'),
        (3, 3, 4, 600.00, '2026-02-10'),
        (4, 1, 1, 1200.00, '2026-03-05')
    ])

conn.commit()
conn.close()
print("✅ Database 'company_sales.db' created and populated with sample data successfully!")