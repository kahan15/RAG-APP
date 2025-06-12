import sqlite3
from datetime import datetime, timedelta
import random

# Create database
conn = sqlite3.connect('example_data/sample.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    price DECIMAL(10,2),
    category TEXT,
    in_stock BOOLEAN
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    joined_date DATE,
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(10,2) DEFAULT 0.00
)
''')

# Sample product data
products = [
    ("Smart Watch Pro", "Advanced smartwatch with health tracking features", 199.99, "Electronics", True),
    ("Yoga Mat Premium", "Extra thick eco-friendly yoga mat", 49.99, "Fitness", True),
    ("Coffee Maker Deluxe", "Programmable coffee maker with thermal carafe", 129.99, "Appliances", True),
    ("Wireless Earbuds", "True wireless earbuds with noise cancellation", 159.99, "Electronics", False),
    ("Running Shoes Air", "Lightweight running shoes with air cushioning", 89.99, "Fitness", True),
    ("Blender Pro", "High-speed blender for smoothies and more", 79.99, "Appliances", True),
    ("Fitness Tracker", "Water-resistant fitness tracker with heart rate monitor", 69.99, "Electronics", True),
    ("Meditation Cushion", "Comfortable cushion for meditation practice", 39.99, "Fitness", True),
    ("Air Fryer XL", "Large capacity air fryer with digital display", 149.99, "Appliances", False),
    ("Smart Scale", "WiFi-enabled scale with body composition analysis", 59.99, "Electronics", True)
]

# Insert product data
cursor.executemany(
    "INSERT INTO products (name, description, price, category, in_stock) VALUES (?, ?, ?, ?, ?)",
    products
)

# Generate sample customer data
customers = []
start_date = datetime(2023, 1, 1)
for i in range(1, 11):
    joined_date = start_date + timedelta(days=random.randint(0, 365))
    total_orders = random.randint(1, 20)
    total_spent = round(random.uniform(50, 1000), 2)
    
    customers.append((
        f"Customer {i}",
        f"customer{i}@example.com",
        joined_date.strftime('%Y-%m-%d'),
        total_orders,
        total_spent
    ))

# Insert customer data
cursor.executemany(
    "INSERT INTO customers (name, email, joined_date, total_orders, total_spent) VALUES (?, ?, ?, ?, ?)",
    customers
)

# Commit changes and close connection
conn.commit()
conn.close()

print("Sample database created successfully!") 