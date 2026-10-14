import sqlite3
import uuid
import base64
import random

DB_NAME_BUZ = "the_farm_agent.db"

# ==========================================
# ENTERPRISE SECURITY: AES-256 SIMULATION LAYER
# ==========================================
def aes_256_encrypt_mock(plaintext: str) -> str:
    """Simulates AES-256 application-layer encryption for POPIA compliance."""
    if not plaintext:
        return ""
    encoded = base64.b64encode(plaintext.encode('utf-8')).decode('utf-8')
    return f"AES256::ENCRYPTED::{encoded}"

def aes_256_decrypt_mock(ciphertext: str) -> str:
    """Decrypts the simulated AES-256 POPIA vault data."""
    if not ciphertext or not ciphertext.startswith("AES256::ENCRYPTED::"):
        return ciphertext
    clean_cipher = ciphertext.replace("AES256::ENCRYPTED::", "")
    return base64.b64decode(clean_cipher).decode('utf-8')

# ==========================================
# DATABASE CONNECTION & PRAGMAS
# ==========================================
def get_connection():
    conn_buz = sqlite3.connect(DB_NAME_BUZ, timeout=10)
    conn_buz.execute("PRAGMA foreign_keys = ON")
    conn_buz.execute("PRAGMA journal_mode = WAL")
    return conn_buz

# ==========================================
# SCHEMA INITIALIZATION & SEEDING
# ==========================================
def init_db():
    conn_buz = get_connection()
    cursor_buz = conn_buz.cursor()

    # 1. POPIA Compliance Isolated Client Table
    cursor_buz.execute("""
        CREATE TABLE IF NOT EXISTS clients_vault (
            farmer_uuid VARCHAR(36) PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            contact_phone VARCHAR(100),
            delivery_address TEXT NOT NULL
        )
    """)

    # 2. Master Inventory Table 
    cursor_buz.execute("""
        CREATE TABLE IF NOT EXISTS inventory_master (
            product_sku VARCHAR(50) PRIMARY KEY,
            product_name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            stock_quantity INTEGER NOT NULL CHECK(stock_quantity >= 0),
            unit_price_cents INTEGER NOT NULL,
            dosage_guideline TEXT NOT NULL
        )
    """)

    # 3. Transactional Order Commitment Table
    cursor_buz.execute("""
        CREATE TABLE IF NOT EXISTS orders_ledger (
            order_id VARCHAR(36) PRIMARY KEY,
            farmer_ref VARCHAR(36) NOT NULL,
            product_sku VARCHAR(50) NOT NULL,
            quantity INTEGER NOT NULL,
            total_cost_cents INTEGER NOT NULL,
            order_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farmer_ref) REFERENCES clients_vault(farmer_uuid),
            FOREIGN KEY (product_sku) REFERENCES inventory_master(product_sku)
        )
    """)

    # 4. Dialog Audit Table
    cursor_buz.execute("""
        CREATE TABLE IF NOT EXISTS dialog_audit (
            chat_session_id VARCHAR(36) NOT NULL,
            normalized_prompt TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Inject Baseline Inventory ONLY if table is empty
    cursor_buz.execute("SELECT COUNT(*) FROM inventory_master")
    if cursor_buz.fetchone()[0] == 0:
        
        # LOCK THE RANDOM GENERATOR SO DASHBOARD STATS NEVER CHANGE ON REBOOT
        random.seed(42)
        
        seed_inventory_buz = [
            ("SKU-BIO-250", "BioBoost 250ml", "Organic Fertilizer", 930, 18500, "5ml per 1L of water weekly"),
            ("SKU-BIO-1L", "BioBoost 1L", "Organic Fertilizer", 500, 52000, "20ml per 5L of water bi-weekly"),
            ("SKU-HYD-500", "HydroCache Granules 500g", "Soil Enhancer", 620, 24000, "15g per planting hole"),
            ("SKU-CAR-5L", "Carbon+ Soil Activator 5L", "Microbial Soil Treatment", 310, 78000, "50ml per 10L of water"),
            ("SKU-REP-500", "BioShield Pest Repel 500ml", "Biological Pest Protection", 425, 31000, "10ml per 1L spray solution"),
            ("SKU-NIT-10K", "NitroGrow Pellets 10kg", "Soil Nutrition", 230, 45000, "100g per square meter")
        ]
        cursor_buz.executemany("""
            INSERT INTO inventory_master 
            (product_sku, product_name, category, stock_quantity, unit_price_cents, dosage_guideline)
            VALUES (?, ?, ?, ?, ?, ?)
        """, seed_inventory_buz)

        # Inject 115 Dummy Users & Transactions
        first_names_buz = ["Jan", "Piet", "Johan", "Willem", "Hendrik", "Thabo", "Sipho", "Lungile", "Zanele", "Ashley", "Michael", "Sarah", "David", "Emma", "James"]
        last_names_buz = ["Smit", "Van Der Merwe", "Botha", "Ndlovu", "Khumalo", "Dlamini", "Venter", "Nel", "Buzuzi", "Nkosi"]
        locations_buz = ["Stellenbosch, Western Cape", "Paarl, Western Cape", "Malmesbury, Western Cape", "Ceres, Western Cape", "Tzaneen, Limpopo", "Bethlehem, Free State", "Upington, Northern Cape", "Nelspruit, Mpumalanga"]
        
        for i in range(115):
            farmer_uuid = str(uuid.uuid4())
            fname_buz = random.choice(first_names_buz)
            lname_buz = random.choice(last_names_buz)
            loc_buz = random.choice(locations_buz)
            phone_buz = f"0{random.randint(60,84)}{random.randint(1000000,9999999)}"
            
            cursor_buz.execute("""
                INSERT INTO clients_vault (farmer_uuid, first_name, last_name, contact_phone, delivery_address)
                VALUES (?, ?, ?, ?, ?)
            """, (farmer_uuid, aes_256_encrypt_mock(fname_buz), aes_256_encrypt_mock(lname_buz), aes_256_encrypt_mock(phone_buz), aes_256_encrypt_mock(loc_buz)))
            
            num_orders_buz = random.randint(1, 5)
            for _ in range(num_orders_buz):
                prod_buz = random.choice(seed_inventory_buz)
                prod_sku_buz = prod_buz[0]
                unit_price_cents_buz = prod_buz[4]
                qty_buz = random.randint(5, 45)
                total_cost_cents_buz = unit_price_cents_buz * qty_buz
                order_id_buz = str(uuid.uuid4())
                
                cursor_buz.execute("""
                    INSERT INTO orders_ledger (order_id, farmer_ref, product_sku, quantity, total_cost_cents)
                    VALUES (?, ?, ?, ?, ?)
                """, (order_id_buz, farmer_uuid, prod_sku_buz, qty_buz, total_cost_cents_buz))

    conn_buz.commit()
    conn_buz.close()

# ==========================================
# TRANSACTION EXECUTIONS
# ==========================================
def fetch_inventory():
    conn_buz = get_connection()
    cursor_buz = conn_buz.cursor()
    cursor_buz.execute("SELECT product_name, category, stock_quantity, (unit_price_cents / 100.0) AS unit_price, dosage_guideline FROM inventory_master")
    rows_buz = cursor_buz.fetchall()
    conn_buz.close()
    return rows_buz

def process_order_transaction(farmer_name, phone, location, product_name, quantity):
    conn_buz = get_connection()
    cursor_buz = conn_buz.cursor()
    name_parts = farmer_name.split(" ", 1)
    first_name_buz = name_parts[0]
    last_name_buz = name_parts[1] if len(name_parts) > 1 else "Unknown"
    
    try:
        cursor_buz.execute("BEGIN IMMEDIATE")
        
        cursor_buz.execute("SELECT product_sku, stock_quantity, unit_price_cents FROM inventory_master WHERE product_name = ?", (product_name,))
        item_buz = cursor_buz.fetchone()
        if not item_buz:
            conn_buz.rollback()
            return False, f"Product '{product_name}' does not exist in inventory."
        
        product_sku_buz, stock_quantity_buz, unit_price_cents_buz = item_buz
        if stock_quantity_buz < quantity:
            conn_buz.rollback()
            return False, f"Insufficient stock: {stock_quantity_buz} units available, {quantity} requested."

        farmer_uuid_buz = str(uuid.uuid4())
        cursor_buz.execute("""
            INSERT INTO clients_vault (farmer_uuid, first_name, last_name, contact_phone, delivery_address)
            VALUES (?, ?, ?, ?, ?)
        """, (farmer_uuid_buz, aes_256_encrypt_mock(first_name_buz), aes_256_encrypt_mock(last_name_buz), aes_256_encrypt_mock(phone), aes_256_encrypt_mock(location)))

        new_stock_buz = stock_quantity_buz - quantity
        cursor_buz.execute("UPDATE inventory_master SET stock_quantity = ? WHERE product_sku = ?", (new_stock_buz, product_sku_buz))

        order_id_buz = str(uuid.uuid4())
        total_cost_cents_buz = unit_price_cents_buz * quantity
        
        cursor_buz.execute("""
            INSERT INTO orders_ledger (order_id, farmer_ref, product_sku, quantity, total_cost_cents)
            VALUES (?, ?, ?, ?, ?)
        """, (order_id_buz, farmer_uuid_buz, product_sku_buz, quantity, total_cost_cents_buz))

        conn_buz.commit()
        short_receipt_no = order_id_buz.split("-")[0].upper()
        return True, {
            "order_id": short_receipt_no, 
            "product": product_name,
            "quantity": quantity,
            "total_cost": (total_cost_cents_buz / 100.0),
            "remaining_stock": new_stock_buz
        }
    except Exception as e:
        conn_buz.rollback()
        return False, str(e)
    finally:
        conn_buz.close()

if __name__ == "__main__":
    init_db()
