
import sqlite3
import os
from datetime import datetime, timedelta
import random

def create_sample_database(db_path: str = "text_to_sql1.db"):
    """Create sample database with tables and metadata"""
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("creating sqlite3 tables...")
    # Create metadata tables first
    create_metadata_tables(cursor)
    
    # Create sample business tables
    create_sample_tables(cursor)
    
    # Insert sample data
    insert_sample_data(cursor)
    
    # Insert metadata
    insert_metadata(cursor)
    
    conn.commit()
    conn.close()
    
    print(f"Sample database created: {db_path}")

def create_metadata_tables(cursor):
    """Create metadata tables for descriptions"""
    
    # Table descriptions
    cursor.execute("""
    CREATE TABLE table_descriptions (
        table_name TEXT PRIMARY KEY,
        description TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Column descriptions
    cursor.execute("""
    CREATE TABLE column_descriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT NOT NULL,
        column_name TEXT NOT NULL,
        description TEXT NOT NULL,
        business_meaning TEXT,
        data_examples TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(table_name, column_name)
    )
    """)

def create_sample_tables(cursor):
    """Create sample business tables"""
    
    # Users table
    cursor.execute("""
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        date_joined DATE NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        user_type TEXT CHECK(user_type IN ('customer', 'admin', 'vendor')) DEFAULT 'customer'
    )
    """)
    
    # Categories table
    cursor.execute("""
    CREATE TABLE categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT UNIQUE NOT NULL,
        description TEXT,
        parent_category_id INTEGER,
        FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
    )
    """)
    
    # Products table
    cursor.execute("""
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        category_id INTEGER NOT NULL,
        stock_quantity INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
    )
    """)
    
    # Orders table
    cursor.execute("""
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_amount DECIMAL(10,2) NOT NULL,
        status TEXT CHECK(status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')) DEFAULT 'pending',
        shipping_address TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """)
    
    # Order items table
    cursor.execute("""
    CREATE TABLE order_items (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        total_price DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """)

def insert_sample_data(cursor):
    """Insert sample data into tables"""
    
    # Insert categories
    categories = [
        (1, "Electronics", "Electronic devices and gadgets", None),
        (2, "Clothing", "Apparel and fashion items", None),
        (3, "Books", "Books and educational materials", None),
        (4, "Smartphones", "Mobile phones and accessories", 1),
        (5, "Laptops", "Computers and laptops", 1)
    ]
    
    cursor.executemany("""
    INSERT OR IGNORE INTO categories (category_id, category_name, description, parent_category_id)
    VALUES (?, ?, ?, ?)
    """, categories)
    
    # Insert users
    users = [
        ("john_doe", "john@email.com", "John", "Doe", "2023-01-15", 1, "customer"),
        ("jane_smith", "jane@email.com", "Jane", "Smith", "2023-02-20", 1, "customer"),
        ("admin_user", "admin@company.com", "Admin", "User", "2023-01-01", 1, "admin"),
        ("vendor_abc", "vendor@abc.com", "ABC", "Vendor", "2023-03-10", 1, "vendor")
    ]
    
    cursor.executemany("""
    INSERT INTO users (username, email, first_name, last_name, date_joined, is_active, user_type)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, users)
    
    # Insert products
    products = [
        ("iPhone 15", "Latest iPhone model", 999.99, 4, 50, 1),
        ("MacBook Pro", "Professional laptop", 1999.99, 5, 25, 1),
        ("T-Shirt", "Cotton t-shirt", 19.99, 2, 100, 1),
        ("Python Book", "Learn Python programming", 49.99, 3, 75, 1),
        ("Samsung Galaxy", "Android smartphone", 799.99, 4, 30, 1)
    ]
    
    cursor.executemany("""
    INSERT INTO products (product_name, description, price, category_id, stock_quantity, is_active)
    VALUES (?, ?, ?, ?, ?, ?)
    """, products)
    
    # Insert orders
    orders = [
        (1, "2024-06-01 10:00:00", 1019.98, "delivered", "123 Main St"),
        (2, "2024-06-15 14:30:00", 2049.98, "shipped", "456 Oak Ave"),
        (1, "2024-06-20 09:15:00", 49.99, "pending", "123 Main St"),
        (4, "2024-06-25 16:45:00", 819.98, "processing", "789 Pine Rd")
    ]
    
    cursor.executemany("""
    INSERT INTO orders (user_id, order_date, total_amount, status, shipping_address)
    VALUES (?, ?, ?, ?, ?)
    """, orders)
    
    # Insert order items
    order_items = [
        (1, 1, 1, 999.99, 999.99),
        (1, 3, 1, 19.99, 19.99),
        (2, 2, 1, 1999.99, 1999.99),
        (2, 4, 1, 49.99, 49.99),
        (3, 4, 1, 49.99, 49.99),
        (4, 5, 1, 799.99, 799.99),
        (4, 3, 1, 19.99, 19.99)
    ]
    
    cursor.executemany("""
    INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
    VALUES (?, ?, ?, ?, ?)
    """, order_items)

def insert_metadata(cursor):
    """Insert table and column descriptions"""
    
    # Table descriptions
    table_descriptions = [
        ("users", "Contains information about all users in the system including customers, admins, and vendors"),
        ("categories", "Product categories with hierarchical structure supporting parent-child relationships"),
        ("products", "Product catalog with pricing, inventory, and category information"),
        ("orders", "Customer orders with status tracking and delivery information"),
        ("order_items", "Individual items within each order with pricing and quantity details")
    ]
    
    cursor.executemany("""
    INSERT INTO table_descriptions (table_name, description)
    VALUES (?, ?)
    """, table_descriptions)
    
    # Column descriptions
    column_descriptions = [
        # Users table
        ("users", "user_id", "Unique identifier for each user", "Primary key for user records", "1, 2, 3"),
        ("users", "username", "Unique username for login", "User's chosen login name", "john_doe, jane_smith"),
        ("users", "email", "User's email address", "Contact email and alternate login method", "john@email.com"),
        ("users", "first_name", "User's first name", "Given name for personalization", "John, Jane"),
        ("users", "last_name", "User's last name", "Family name for full identification", "Doe, Smith"),
        ("users", "date_joined", "Date when user registered", "Account creation timestamp", "2023-01-15"),
        ("users", "is_active", "Whether user account is active", "Account status flag", "1 (active), 0 (inactive)"),
        ("users", "user_type", "Type of user account", "Role-based access control", "customer, admin, vendor"),
        
        # Categories table
        ("categories", "category_id", "Unique identifier for category", "Primary key for categories", "1, 2, 3"),
        ("categories", "category_name", "Name of the category", "Display name for product grouping", "Electronics, Clothing"),
        ("categories", "description", "Category description", "Detailed explanation of category", "Electronic devices and gadgets"),
        ("categories", "parent_category_id", "Parent category reference", "Enables hierarchical categories", "1 (Electronics parent of Smartphones)"),
        
        # Products table
        ("products", "product_id", "Unique identifier for product", "Primary key for products", "1, 2, 3"),
        ("products", "product_name", "Name of the product", "Display name for catalog", "iPhone 15, MacBook Pro"),
        ("products", "description", "Product description", "Detailed product information", "Latest iPhone model"),
        ("products", "price", "Product price in USD", "Current selling price", "999.99, 19.99"),
        ("products", "category_id", "Category reference", "Links product to category", "4 (Smartphones)"),
        ("products", "stock_quantity", "Available inventory", "Current stock level", "50, 100, 0"),
        ("products", "created_at", "Product creation date", "When product was added", "2024-01-15 10:30:00"),
        ("products", "is_active", "Product availability status", "Whether product is currently sold", "1 (available), 0 (discontinued)"),
        
        # Orders table
        ("orders", "order_id", "Unique identifier for order", "Primary key for orders", "1, 2, 3"),
        ("orders", "user_id", "Customer reference", "Links order to customer", "1 (john_doe's orders)"),
        ("orders", "order_date", "When order was placed", "Order creation timestamp", "2024-06-01 10:00:00"),
        ("orders", "total_amount", "Total order value", "Sum of all items plus tax/shipping", "1019.98, 49.99"),
        ("orders", "status", "Current order status", "Order processing stage", "pending, shipped, delivered"),
        ("orders", "shipping_address", "Delivery address", "Where order should be sent", "123 Main St, Apt 4B"),
        
        # Order items table
        ("order_items", "order_item_id", "Unique identifier for order line", "Primary key for order items", "1, 2, 3"),
        ("order_items", "order_id", "Order reference", "Links item to specific order", "1 (items in order #1)"),
        ("order_items", "product_id", "Product reference", "Links to specific product", "1 (iPhone 15)"),
        ("order_items", "quantity", "Number of items ordered", "How many units purchased", "1, 2, 5"),
        ("order_items", "unit_price", "Price per item", "Individual item cost at time of order", "999.99, 19.99"),
        ("order_items", "total_price", "Total for this line item", "quantity * unit_price", "999.99, 39.98")
    ]
    
    cursor.executemany("""
    INSERT INTO column_descriptions (table_name, column_name, description, business_meaning, data_examples)
    VALUES (?, ?, ?, ?, ?)
    """, column_descriptions)

if __name__ == "__main__":
    create_sample_database()