import sqlite3
import random

DB_NAME_BUZ = "the_farm_agent.db"

def get_connection():
    conn_buz = sqlite3.connect(DB_NAME_BUZ, timeout=10)
    conn_buz.execute("PRAGMA foreign_keys = ON")
    return conn_buz

def init_db():
    conn_buz = get_connection()
    cursor_buz = conn_buz.cursor()

    # Master inventory table with agronomic parameters
    cursor_buz.execute("""
        CREATE TABLE IF NOT EXISTS inventory_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            stock_qty INTEGER NOT NULL CHECK(stock_qty >= 0),
            unit_price REAL NOT NULL,
            dosage_guideline TEXT NOT NULL,
            ecocert_certified INTEGER DEFAULT 1
        )
    """)

    # POPIA Compliance isolated client table (PII isolation)
    cursor_buz.execute("""
        CREATE TABLE IF NOT EXISTS popia_encrypted_clients (
            farmer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone_contact TEXT NOT NULL,
            delivery_location TEXT NOT NULL,
            consent_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Transactional order commitment table
    cursor_buz.execute("""
        CREATE TABLE IF NOT EXISTS orders_commitment (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            total_cost REAL NOT NULL,
            order_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            order_status TEXT DEFAULT 'Reserved',
            FOREIGN KEY (farmer_id) REFERENCES popia_encrypted_clients(farmer_id)
        )
    """)

    # Seed baseline inventory and dummy analytics users if empty
    cursor_buz.execute("SELECT COUNT(*) FROM inventory_master")
    if cursor_buz.fetchone()[0] == 0:
        
        # Stock increased by approximately 675% for high-volume simulated trading
        seed_inventory_buz = [
            ("BioBoost 250ml", "Organic Fertilizer", 930, 185.00, "5ml per 1L of water weekly", 1),
            ("BioBoost 1L", "Organic Fertilizer", 500, 520.00, "20ml per 5L of water bi-weekly", 1),
            ("HydroCache Granules 500g", "Soil Enhancer", 620, 240.00, "15g per planting hole", 1),
            ("Carbon+ Soil Activator 5L", "Microbial Soil Treatment", 310, 780.00, "50ml per 10L of water", 1),
            ("BioShield Pest Repel 500ml", "Biological Pest Protection", 425, 310.00, "10ml per 1L spray solution", 1),
            ("NitroGrow Pellets 10kg", "Soil Nutrition", 230, 450.00, "100g per square meter", 1)
        ]
        cursor_buz.executemany("""
            INSERT INTO inventory_master 
            (product_name, category, stock_qty, unit_price, dosage_guideline, ecocert_certified)
            VALUES (?, ?, ?, ?, ?, ?)
        """, seed_inventory_buz)
        
        # SEED 115 DUMMY USERS & TRANSACTIONS FOR DASHBOARD ANALYTICS
        first_names_buz = ["Jan", "Piet", "Johan", "Willem", "Hendrik", "Thabo", "Sipho", "Lungile", "Zanele", "Ashley", "Michael", "Sarah", "David", "Emma", "James"]
        last_names_buz = ["Smit", "Van Der Merwe", "Botha", "Ndlovu", "Khumalo", "Dlamini", "Venter", "Nel", "Buzuzi", "Nkosi"]
        locations_buz = ["Stellenbosch, Western Cape", "Paarl, Western Cape", "Malmesbury, Western Cape", "Ceres, Western Cape", "Tzaneen, Limpopo", "Bethlehem, Free State", "Upington, Northern Cape", "Nelspruit, Mpumalanga"]
        
        for i in range(115):
            fname_buz = random.choice(first_names_buz)
            lname_buz = random.choice(last_names_buz)
            full_name_buz = f"{fname_buz} {lname_buz}"
            loc_buz = random.choice(locations_buz)
            phone_buz = f"0{random.randint(60,84)}{random.randint(1000000,9999999)}"
            
            cursor_buz.execute("""
                INSERT INTO popia_encrypted_clients (full_name, phone_contact, delivery_location)
                VALUES (?, ?, ?)
            """, (full_name_buz, phone_buz, loc_buz))
            farmer_id_buz = cursor_buz.lastrowid
            
            num_orders_buz = random.randint(1, 5)
            for _ in range(num_orders_buz):
                prod_buz = random.choice(seed_inventory_buz)
                prod_name_buz = prod_buz[0]
                unit_price_buz = prod_buz[3]
                qty_buz = random.randint(5, 45)
                total_cost_buz = unit_price_buz * qty_buz
                
                cursor_buz.execute("""
                    INSERT INTO orders_commitment (farmer_id, product_name, quantity, total_cost)
                    VALUES (?, ?, ?, ?)
                """, (farmer_id_buz, prod_name_buz, qty_buz, total_cost_buz))
    
    conn_buz.commit()
    conn_buz.close()

def fetch_inventory():
    conn_buz = get_connection()
    cursor_buz = conn_buz.cursor()
    cursor_buz.execute("SELECT product_name, category, stock_qty, unit_price, dosage_guideline FROM inventory_master")
    rows_buz = cursor_buz.fetchall()
    conn_buz.close()
    return rows_buz

def process_order_transaction(farmer_name, phone, location, product_name, quantity):
    conn_buz = get_connection()
    cursor_buz = conn_buz.cursor()
    try:
        cursor_buz.execute("BEGIN IMMEDIATE")
        
        cursor_buz.execute("SELECT stock_qty, unit_price FROM inventory_master WHERE product_name = ?", (product_name,))
        item_buz = cursor_buz.fetchone()
        if not item_buz:
            conn_buz.rollback()
            return False, f"Product '{product_name}' does not exist in inventory."
        
        stock_qty_buz, unit_price_buz = item_buz
        if stock_qty_buz < quantity:
            conn_buz.rollback()
            return False, f"Insufficient stock: {stock_qty_buz} units available, {quantity} requested."

        cursor_buz.execute("""
            INSERT INTO popia_encrypted_clients (full_name, phone_contact, delivery_location)
            VALUES (?, ?, ?)
        """, (farmer_name, phone, location))
        farmer_id_buz = cursor_buz.lastrowid

        new_stock_buz = stock_qty_buz - quantity
        cursor_buz.execute("UPDATE inventory_master SET stock_qty = ? WHERE product_name = ?", (new_stock_buz, product_name))

        total_cost_buz = unit_price_buz * quantity
        cursor_buz.execute("""
            INSERT INTO orders_commitment (farmer_id, product_name, quantity, total_cost)
            VALUES (?, ?, ?, ?)
        """, (farmer_id_buz, product_name, quantity, total_cost_buz))
        order_id_buz = cursor_buz.lastrowid

        conn_buz.commit()
        return True, {
            "order_id": order_id_buz,
            "product": product_name,
            "quantity": quantity,
            "total_cost": total_cost_buz,
            "remaining_stock": new_stock_buz
        }
    except Exception as e:
        conn_buz.rollback()
        return False, str(e)
    finally:
        conn_buz.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
