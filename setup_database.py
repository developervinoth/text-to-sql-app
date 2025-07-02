"""
Updated script to set up database with mock sample tables for PCI/MNPI compliance
"""
import sqlite3
import os
from datetime import datetime, timedelta
import random

def create_sample_database(db_path: str = "test2.db"):
    """Create sample database with tables and their corresponding mock sample tables"""
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create metadata tables first
    create_metadata_tables(cursor)
    
    # Create sample business tables
    create_sample_tables(cursor)
    
    # Create corresponding mock sample tables
    create_mock_sample_tables(cursor)
    
    # Insert sample data into real tables
    insert_sample_data(cursor)
    
    # Insert mock data into sample tables
    insert_mock_sample_data(cursor)
    
    # Insert metadata
    insert_metadata(cursor)
    
    conn.commit()
    conn.close()
    
    print(f"Sample database created: {db_path}")
    print("✅ Real tables: users, categories, products, orders, order_items")
    print("🔒 Mock tables: users_sample, categories_sample, products_sample, orders_sample, order_items_sample")

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
    """Create sample business tables (real tables)"""
    
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

def create_mock_sample_tables(cursor):
    """Create mock sample tables with identical structure to real tables"""
    
    print("Creating mock sample tables for PCI/MNPI compliance...")
    
    # Users sample table (identical structure)
    cursor.execute("""
    CREATE TABLE users_sample (
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
    
    # Categories sample table
    cursor.execute("""
    CREATE TABLE categories_sample (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT UNIQUE NOT NULL,
        description TEXT,
        parent_category_id INTEGER
    )
    """)
    
    # Products sample table
    cursor.execute("""
    CREATE TABLE products_sample (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        category_id INTEGER NOT NULL,
        stock_quantity INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
    """)
    
    # Orders sample table
    cursor.execute("""
    CREATE TABLE orders_sample (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_amount DECIMAL(10,2) NOT NULL,
        status TEXT CHECK(status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')) DEFAULT 'pending',
        shipping_address TEXT
    )
    """)
    
    # Order items sample table
    cursor.execute("""
    CREATE TABLE order_items_sample (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        total_price DECIMAL(10,2) NOT NULL
    )
    """)

def insert_sample_data(cursor):
    """Insert sample data into real tables"""
    
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

def insert_mock_sample_data(cursor):
    """Insert mock/fake data into sample tables for AI context"""
    
    print("Inserting mock sample data (PCI/MNPI safe)...")
    
    # Mock categories (safe, generic data)
    mock_categories = [
        (1, "Tech_Demo", "Demo technology products", None),
        (2, "Fashion_Test", "Test fashion items", None),
        (3, "Media_Sample", "Sample media content", None),
        (4, "Mobile_Mock", "Mock mobile devices", 1),
        (5, "Computer_Demo", "Demo computers", 1)
    ]
    
    cursor.executemany("""
    INSERT INTO categories_sample (category_id, category_name, description, parent_category_id)
    VALUES (?, ?, ?, ?)
    """, mock_categories)
    
    # Mock users (completely fictional)
    mock_users = [
        ("demo_user1", "demo1@example.com", "Alice", "Demo", "2023-01-15", 1, "customer"),
        ("demo_user2", "demo2@example.com", "Bob", "Test", "2023-02-20", 1, "customer"),
        ("demo_admin", "admin@example.com", "Demo", "Admin", "2023-01-01", 1, "admin"),
        ("demo_vendor", "vendor@example.com", "Test", "Vendor", "2023-03-10", 1, "vendor"),
        ("demo_inactive", "inactive@example.com", "Inactive", "User", "2022-12-01", 0, "customer")
    ]
    
    cursor.executemany("""
    INSERT INTO users_sample (username, email, first_name, last_name, date_joined, is_active, user_type)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, mock_users)
    
    # Mock products (safe product names and prices)
    mock_products = [
        ("Demo Phone X1", "Sample smartphone for testing", 599.99, 4, 25, 1),
        ("Test Laptop Pro", "Demo laptop computer", 1299.99, 5, 15, 1),
        ("Sample Shirt", "Demo clothing item", 29.99, 2, 50, 1),
        ("Mock Programming Guide", "Test educational book", 39.99, 3, 100, 1),
        ("Demo Tablet Z2", "Sample tablet device", 399.99, 1, 30, 1),
        ("Test Headphones", "Demo audio device", 149.99, 1, 75, 1),
        ("Sample Jeans", "Demo denim pants", 79.99, 2, 40, 1)
    ]
    
    cursor.executemany("""
    INSERT INTO products_sample (product_name, description, price, category_id, stock_quantity, is_active)
    VALUES (?, ?, ?, ?, ?, ?)
    """, mock_products)
    
    # Mock orders (safe transaction data)
    mock_orders = [
        (1, "2024-01-15 10:30:00", 629.98, "delivered", "123 Demo Street, Test City"),
        (2, "2024-01-20 14:20:00", 1329.98, "shipped", "456 Sample Ave, Mock Town"),
        (3, "2024-02-01 09:15:00", 219.98, "pending", "789 Example Blvd, Demo City"),
        (1, "2024-02-10 16:45:00", 149.99, "processing", "123 Demo Street, Test City"),
        (4, "2024-02-15 11:30:00", 79.99, "cancelled", "321 Test Lane, Sample City")
    ]
    
    cursor.executemany("""
    INSERT INTO orders_sample (user_id, order_date, total_amount, status, shipping_address)
    VALUES (?, ?, ?, ?, ?)
    """, mock_orders)
    
    # Mock order items (corresponding to mock orders)
    mock_order_items = [
        (1, 1, 1, 599.99, 599.99),      # Demo Phone X1
        (1, 3, 1, 29.99, 29.99),       # Sample Shirt
        (2, 2, 1, 1299.99, 1299.99),   # Test Laptop Pro
        (2, 3, 1, 29.99, 29.99),       # Sample Shirt
        (3, 6, 1, 149.99, 149.99),     # Test Headphones
        (3, 7, 1, 79.99, 79.99),       # Sample Jeans
        (4, 6, 1, 149.99, 149.99),     # Test Headphones
        (5, 7, 1, 79.99, 79.99)        # Sample Jeans (cancelled order)
    ]
    
    cursor.executemany("""
    INSERT INTO order_items_sample (order_id, product_id, quantity, unit_price, total_price)
    VALUES (?, ?, ?, ?, ?)
    """, mock_order_items)

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
    
    # Column descriptions (for all real tables)
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

def create_additional_mock_tables_script():
    """Generate a script for creating mock tables for any additional real tables"""
    
    script = """
-- Additional Mock Tables Setup Script
-- Use this template to create mock tables for any additional real tables

-- Template for creating a mock table:
-- 1. Copy the structure of your real table
-- 2. Create {table_name}_sample with identical structure
-- 3. Insert 3-5 rows of safe, fictional data

-- Example for a new table called 'payments':
/*
CREATE TABLE payments_sample (
    payment_id INTEGER PRIMARY KEY,
    order_id INTEGER,
    payment_method TEXT,
    amount DECIMAL(10,2),
    payment_date TIMESTAMP,
    status TEXT
);

INSERT INTO payments_sample VALUES 
(1, 1, 'demo_card_****1234', 629.98, '2024-01-15 10:35:00', 'completed'),
(2, 2, 'demo_card_****5678', 1329.98, '2024-01-20 14:25:00', 'completed'),
(3, 3, 'demo_paypal', 219.98, '2024-02-01 09:20:00', 'pending');
*/

-- Guidelines for mock data:
-- [OK] Use fictional names, emails, addresses
-- [OK] Use demo/test/sample prefixes
-- [OK] Use safe card numbers (4111-1111-1111-1111 for testing)
-- [OK] Use realistic but fake amounts and dates
-- [NO] Never use real customer data
-- [NO] Never use real payment information
-- [NO] Never use real personal identifiers
"""
    
    return script

if __name__ == "__main__":
    create_sample_database()
    
    # Create additional setup script with proper encoding
    try:
        with open("additional_mock_tables.sql", "w", encoding='utf-8') as f:
            f.write(create_additional_mock_tables_script())
        print("\n[INFO] Created additional_mock_tables.sql for future tables")
        print("[INFO] Database is now PCI/MNPI compliant with mock sample data")
    except Exception as e:
        print(f"\n[WARNING] Could not create additional_mock_tables.sql: {e}")
        print("[INFO] Database setup completed successfully anyway")