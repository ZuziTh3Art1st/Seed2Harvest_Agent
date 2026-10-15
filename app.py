import os
import re
import html
import base64
import time
from urllib.parse import quote
import datetime
import sqlite3
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import qrcode
from io import BytesIO
from groq import Groq
import The_Database as db

# PAGE CONFIG 
st.set_page_config(
    page_title="Seed 2 Harvest | Cinematic Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CACHED HELPER TO GET ONLY PREMIUM HIGH QUALITY IMAGES
@st.cache_data(show_spinner=False)
def get_high_quality_images():
    high_quality_list_buz = []
    premium_allowed_buz = [
        "pexels-dirrez-3672776.jpg",
        "pexels-joran-quinten-2125825-3775331.jpg",
        "pexels-tatianasyrikova-3934023.jpg",
        "pexels-richard-pan-5305182-12643137.jpg",
        "pexels-arndt-peter-bergfeld-151632051-39888320.jpg",
        "v2osk-1Z2niiBPg5A-unsplash.jpg",
        "pietro-de-grandi-T7K4aEPoGGk-unsplash.jpg",
        "mark-harpur-K2s_YE031CA-unsplash.jpg"
    ]
    try:
        if os.path.exists("images"):
            all_files_buz = sorted(os.listdir("images"))
            for f in all_files_buz:
                if f in premium_allowed_buz:
                    high_quality_list_buz.append(os.path.join("images", f))
    except Exception:
        pass
    
    if not high_quality_list_buz:
        high_quality_list_buz = [
            "https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=2032&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?q=80&w=2040&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1511497584788-876761142212?q=80&w=2032&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=2070&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1464226184884-fa280b87c399?q=80&w=2070&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=2032&auto=format&fit=crop"
        ]
    return high_quality_list_buz

@st.cache_data(show_spinner=False)
def get_image_base64(path):
    if path.startswith("http"):
        return path
    try:
        with open(path, "rb") as f:
            b64_buz = base64.b64encode(f.read()).decode()
        ext_buz = path.rsplit(".", 1)[-1].lower()
        mime_buz = "image/png" if ext_buz == "png" else ("image/webp" if ext_buz == "webp" else "image/jpeg")
        return f"data:{mime_buz};base64,{b64_buz}"
    except Exception:
        return ""

def aes_256_decrypt_mock(ciphertext: str) -> str:
    if not ciphertext or not ciphertext.startswith("AES256::ENCRYPTED::"):
        return ciphertext
    clean_cipher = ciphertext.replace("AES256::ENCRYPTED::", "")
    return base64.b64decode(clean_cipher).decode('utf-8')

# INITIALIZE STATE & ROUTING
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "user_data" not in st.session_state: st.session_state.user_data = {"name": "", "farm": "", "location": "", "email": "", "farmer_uuid": None}
if "messages" not in st.session_state: st.session_state.messages = []
if "basket" not in st.session_state: st.session_state.basket = {}
if "last_document" not in st.session_state: st.session_state.last_document = None
if "tts_enabled" not in st.session_state: st.session_state.tts_enabled = False

current_page_buz = "ONBOARDING" if not st.session_state.authenticated else st.session_state.get("current_page", "CHAT")

if "bg_mapping_buz" not in st.session_state:
    hq_images_buz = get_high_quality_images()
    st.session_state.bg_mapping_buz = {
        "ONBOARDING": hq_images_buz[0] if len(hq_images_buz) > 0 else hq_images_buz[-1],
        "CHAT": hq_images_buz[1] if len(hq_images_buz) > 1 else hq_images_buz[0],
        "CATALOGUE": hq_images_buz[2] if len(hq_images_buz) > 2 else hq_images_buz[0],
        "RESERVE ORDER": hq_images_buz[3] if len(hq_images_buz) > 3 else hq_images_buz[0],
        "GLOBAL FEED": hq_images_buz[4] if len(hq_images_buz) > 4 else hq_images_buz[0],
        "FEATURES": hq_images_buz[5] if len(hq_images_buz) > 5 else hq_images_buz[0]
    }

bg_path_buz = st.session_state.bg_mapping_buz.get(current_page_buz, "images/maxresdefault.jpg")
bg_b64_buz = get_image_base64(bg_path_buz)

# DYNAMIC SIDEBAR VISIBILITY
sidebar_css_buz = ""
if not st.session_state.authenticated:
    sidebar_css_buz = """
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
    """

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    .stApp {{
        background: linear-gradient(180deg, rgba(6, 9, 15, 0.4) 0%, rgba(6, 9, 15, 0.85) 100%), url('{bg_b64_buz}') !important;
        background-size: cover !important;
        background-position: center center !important;
        background-attachment: fixed !important;
    }}
    
    header[data-testid="stHeader"] {{ background: transparent !important; }}

    html, body, p, span, div, label, h1, h2, h3, h4, h5, h6, li {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #F8FAFC !important;
    }}
    
    h1, h2, h3 {{ font-family: 'Playfair Display', serif !important; font-weight: 700 !important; }}

    .main-title {{
        font-family: 'Playfair Display', serif !important;
        font-size: 4rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 2rem 0 0.5rem 0;
        text-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }}
    .sub-title {{
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #34D399 !important;
        font-size: 1rem;
        letter-spacing: 5px;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 3rem;
        text-shadow: 0 2px 10px rgba(0,0,0,0.5);
    }}
    .section-header {{
        font-family: 'Playfair Display', serif !important;
        font-size: 2rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        padding-bottom: 10px;
        margin: 2rem 0 1.5rem 0;
    }}

    {sidebar_css_buz}

    [data-testid="stSidebar"] {{ 
        background-color: rgba(10, 15, 25, 0.35) !important; 
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important; 
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{ background-color: transparent !important; }}
    
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"], [data-testid="stChatInput"] {{
        background-color: rgba(15, 23, 42, 0.65) !important; 
        color: #FFFFFF !important; 
        border: 1px solid rgba(255, 255, 255, 0.2) !important; 
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
    }}
    .stTextInput input:focus, [data-testid="stChatInput"]:focus-within {{ 
        border-color: #34D399 !important; 
        box-shadow: 0 0 0 2px rgba(52, 211, 153, 0.3) !important; 
    }}

    .stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button {{
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important; 
        color: #FFFFFF !important; 
        border: 1px solid rgba(255,255,255,0.1) !important; 
        border-radius: 12px !important; 
        font-weight: 700 !important; 
        padding: 0.6rem 1.4rem !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.3s ease !important;
    }}
    .stButton button:hover {{ 
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 25px rgba(16, 185, 129, 0.4) !important;
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    }}

    [data-testid="stChatMessage"] {{
        background-color: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2) !important;
    }}

    [data-testid="stBottom"] > div {{
        background-color: rgba(10, 15, 25, 0.3) !important;
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
    }}
    [data-testid="stChatInput"] > div {{
        background-color: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
    }}
    [data-testid="stChatInput"] textarea {{ color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; background-color: transparent !important; }}
    [data-testid="stChatInput"] textarea::placeholder {{ color: #94A3B8 !important; -webkit-text-fill-color: #94A3B8 !important; }}
    [data-testid="stChatInput"] svg {{ fill: #34D399 !important; }}
    
    .glass-panel {{
        background: rgba(15, 23, 42, 0.55);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }}
    .guide-item {{
        font-size: 0.85rem;
        background: rgba(255, 255, 255, 0.08);
        padding: 8px 14px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        display: inline-block;
        margin: 4px 8px 4px 0;
    }}

    .glass-card {{
        background: rgba(15, 23, 42, 0.55); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.15); border-top: 3px solid #34D399;
        padding: 26px; border-radius: 20px; margin-bottom: 18px; height: 100%;
        box-shadow: 0 15px 35px -10px rgba(0,0,0,0.5); transition: transform 0.3s ease, border-color 0.3s ease;
    }}
    .glass-card:hover {{ transform: translateY(-4px); border-color: rgba(52, 211, 153, 0.6); }}

    .quote-box {{
        background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.15); padding: 30px; border-radius: 20px; margin-top: 20px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
    }}
    .quote-box table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
    .quote-box th {{ text-align: left; color: #34D399 !important; border-bottom: 1px solid rgba(255, 255, 255, 0.2); padding: 12px; }}
    .quote-box td {{ padding: 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }}

    .custom-warning {{ background-color: rgba(16, 185, 129, 0.15); color: #34D399 !important; padding: 18px; border-radius: 16px; margin: 15px 0; border: 1px solid rgba(16, 185, 129, 0.4); }}
    .success-receipt {{ background-color: rgba(52, 211, 153, 0.2); color: #F8FAFC !important; padding: 22px; border-radius: 16px; margin: 20px 0; border: 1px solid rgba(52, 211, 153, 0.6); font-size: 1.1rem; text-align: center; box-shadow: 0 10px 30px rgba(16, 185, 129, 0.2); }}

    .footer {{ text-align: center; margin-top: 80px; padding: 30px 0; border-top: 1px solid rgba(255, 255, 255, 0.1); background: rgba(4, 6, 11, 0.6); backdrop-filter: blur(12px); }}
</style>
""", unsafe_allow_html=True)

db.init_db()

# DB HELPER QUERIES FOR DASHBOARD & LOGIN
def get_platform_stats():
    try:
        conn_buz = sqlite3.connect("the_farm_agent.db")
        c_buz = conn_buz.cursor()
        
        c_buz.execute("SELECT COUNT(DISTINCT farmer_uuid) FROM clients_vault")
        total_users_buz = c_buz.fetchone()[0] or 0
        
        c_buz.execute("SELECT AVG(user_total) FROM (SELECT SUM(quantity) as user_total FROM orders_ledger GROUP BY farmer_ref)")
        avg_items_buz = c_buz.fetchone()[0] or 0
        
        c_buz.execute("SELECT delivery_address FROM clients_vault GROUP BY delivery_address ORDER BY COUNT(*) DESC LIMIT 1")
        top_loc_row_buz = c_buz.fetchone()
        top_loc_buz = aes_256_decrypt_mock(top_loc_row_buz[0]) if top_loc_row_buz else "N/A"
        
        conn_buz.close()
        return total_users_buz, round(avg_items_buz, 1), top_loc_buz
    except Exception:
        return 0, 0.0, "N/A"

def login_with_receipt(receipt_str):
    if not receipt_str or not receipt_str.startswith("C"):
        return None
        
    try:
        conn_buz = sqlite3.connect("the_farm_agent.db")
        c_buz = conn_buz.cursor()
        search_str = receipt_str.replace("C", "").lower() + "%"
        
        c_buz.execute("""
            SELECT c.farmer_uuid, c.first_name, c.last_name, c.delivery_address
            FROM orders_ledger o
            JOIN clients_vault c ON o.farmer_ref = c.farmer_uuid
            WHERE o.order_id LIKE ?
        """, (search_str,))
        row_buz = c_buz.fetchone()
        conn_buz.close()
        
        if row_buz:
            fid = row_buz[0]
            fname = aes_256_decrypt_mock(row_buz[1])
            lname = aes_256_decrypt_mock(row_buz[2])
            full_name = f"{fname} {lname}"
            loc = aes_256_decrypt_mock(row_buz[3])
            email_guess_buz = f"{fname.replace(' ', '').lower()}@farm.co.za"
            return {"name": full_name, "farm": "Registered Farm", "location": loc, "email": email_guess_buz, "farmer_uuid": fid}
    except Exception:
        pass
    return None

# DYNAMIC AGRONOMIC TELEMETRY & SAFEX COMMODITY SIMULATION
def get_live_agronomic_telemetry(location_str: str):
    """Generates realistic time-of-day and location-influenced sensor telemetry."""
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    
    # Diurnal temperature cycle: peaks around 14:00, coolest at 05:00
    base_temp = 17.0 + 8.0 * max(0.0, 1.0 - abs(hour - 14) / 9.0)
    temp_c = round(base_temp + (minute % 5) * 0.2, 1)
    
    # Soil moisture inverse to diurnal heat
    soil_moisture = round(45.0 - (temp_c - 17.0) * 0.7 + (minute % 3) * 0.3, 1)
    
    # Soil pH dynamic oscillation around sweet spot (6.6 - 6.9)
    soil_ph = round(6.7 + ((hour + minute) % 7) * 0.03, 2)
    
    # Next rain forecast in days
    next_rain_days = max(1, (hour * 3 + minute) % 5 + 1)
    
    return temp_c, soil_moisture, soil_ph, next_rain_days

def get_live_commodity_prices():
    """Returns dynamic SAFEX commodity spot prices with live daily deltas."""
    now = datetime.datetime.now()
    seed_day = now.day + now.hour
    
    commodities = [
        {"name": "White Maize", "base": 4250, "delta_pct": round(((seed_day * 7) % 25 - 12) / 10.0, 2)},
        {"name": "Yellow Maize", "base": 4100, "delta_pct": round(((seed_day * 5) % 20 - 10) / 10.0, 2)},
        {"name": "Wheat", "base": 6150, "delta_pct": round(((seed_day * 9) % 22 - 8) / 10.0, 2)},
        {"name": "Soybeans", "base": 8450, "delta_pct": round(((seed_day * 3) % 26 - 13) / 10.0, 2)},
        {"name": "Sunflower Seed", "base": 9200, "delta_pct": round(((seed_day * 11) % 24 - 11) / 10.0, 2)},
    ]
    
    results = []
    for c in commodities:
        cur_price = round(c["base"] * (1 + c["delta_pct"] / 100.0))
        results.append({
            "name": c["name"],
            "price": f"R {cur_price:,}",
            "delta": f"{'+' if c['delta_pct'] >= 0 else ''}{c['delta_pct']:.1f}%",
            "is_up": c["delta_pct"] >= 0
        })
    return results

# HELPERS & LOGIC
BANKS = [
    ("FNB", "https://www.fnb.co.za"),
    ("Standard Bank", "https://www.standardbank.co.za"),
    ("Absa", "https://www.absa.co.za"),
    ("Nedbank", "https://www.nedbank.co.za"),
    ("Capitec", "https://www.capitecbank.co.za"),
]

BENEFICIARY = {
    "Account name": "Seed 2 Harvest (Pty) Ltd",
    "Bank": "",
    "Account type": "",
    "Account number": "",
    "Branch code": "",
}

def get_secret(name, default=None):
    val = os.environ.get(name)
    if val: return val
    try: return st.secrets[name]
    except Exception: return default

class AgriculturalMiddleware:
    SLANG_DICTIONARY = {
        r"\bblaarbrand\b": "leaf scorch / fungal burn",
        r"\bkunsmis\b": "organic fertilizer",
        r"\bgoggas\b": "agricultural pests / insects",
        r"\bspuit\b": "spray application / foliar dosage",
        r"\bbrak grond\b": "saline dry alkaline soil",
        r"\bcompost\b": "organic matter / soil enhancer",
        r"\bboer\b": "farmer",
        r"\blap\b": "cultivated field plot",
        r"\bplaag\b": "pest infestation",
        r"\bgif\b": "crop protection remedy"
    }

    @classmethod
    def normalize_vernacular(cls, text: str) -> str:
        normalized_buz = text
        for pattern_buz, replacement_buz in cls.SLANG_DICTIONARY.items():
            normalized_buz = re.sub(pattern_buz, replacement_buz, normalized_buz, flags=re.IGNORECASE)
        return normalized_buz

def make_qr_png(data: str, box_size=5) -> bytes:
    qr_buz = qrcode.QRCode(version=None, box_size=box_size, border=2)
    qr_buz.add_data(data)
    qr_buz.make(fit=True)
    img_buz = qr_buz.make_image(fill_color="black", back_color="white")
    buf_buz = BytesIO()
    img_buz.save(buf_buz, format="PNG")
    return buf_buz.getvalue()

GROQ_API_KEY = get_secret("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

catalog_data_buz = db.fetch_inventory()
price_map_buz = {row[0]: row[3] for row in catalog_data_buz}
catalog_context_buz = "\n".join([f"- Product: {row[0]} | Category: {row[1]} | Stock: {row[2]} units | Price: R{row[3]:.2f} | Safe Usage: {row[4]}" for row in catalog_data_buz])

def basket_totals_buz():
    subtotal_buz = sum(price_map_buz.get(p, 0.0) * q for p, q in st.session_state.basket.items() if q > 0)
    vat_buz = subtotal_buz * 0.15
    return subtotal_buz, vat_buz, subtotal_buz + vat_buz

def basket_context_buz() -> str:
    items_buz = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
    if not items_buz: return "The client's basket is currently EMPTY."
    lines_buz = [f"- {q}x {p} @ R{price_map_buz.get(p, 0.0):.2f} = R{price_map_buz.get(p, 0.0) * q:.2f}" for p, q in items_buz]
    subtotal_buz, vat_buz, total_buz = basket_totals_buz()
    lines_buz.append(f"Subtotal: R{subtotal_buz:.2f} | VAT (15%): R{vat_buz:.2f} | Total: R{total_buz:.2f}")
    return "\n".join(lines_buz)

def set_basket_qty_buz(product_name):
    qty_buz = st.session_state.get(f"cat_{product_name}", 0)
    if qty_buz and qty_buz > 0: st.session_state.basket[product_name] = int(qty_buz)
    else: st.session_state.basket.pop(product_name, None)

def clear_basket_buz():
    st.session_state.basket = {}
    for k_buz in [k_buz for k_buz in st.session_state.keys() if k_buz.startswith("cat_")]: del st.session_state[k_buz]

def payment_lines(inv_no, grand_total):
    lines_buz = [f"Payment reference: {inv_no}", f"Amount to pay: R{grand_total:.2f}"]
    filled_buz = [(k, v) for k, v in BENEFICIARY.items() if v]
    lines_buz += [f"{k}: {v}" for k, v in filled_buz]
    if len(filled_buz) <= 1: lines_buz.append("Full banking details: request from support@seed2harvest.co.za")
    return lines_buz

def generate_and_send(doc_type, location_input, phone, email_input, receipt_no):
    active_items_buz = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
    subtotal_buz, tax_total_buz, grand_total_buz = basket_totals_buz()
    date_str_buz = pd.Timestamp.now().strftime('%Y-%m-%d')
    e_buz = html.escape
    
    rows_html_buz = "".join(f"<tr><td>{e_buz(p)}</td><td>{q}</td><td>R{price_map_buz.get(p, 0.0):.2f}</td><td>R{price_map_buz.get(p, 0.0) * q:.2f}</td></tr>" for p, q in active_items_buz)
    rows_text_buz = "\n".join(f"  {q}x {p} @ R{price_map_buz.get(p, 0.0):.2f} = R{price_map_buz.get(p, 0.0) * q:.2f}" for p, q in active_items_buz)
    bank_qrs_buz = []
    pay_list_buz = payment_lines(receipt_no, grand_total_buz)
    pay_html_buz = "<br>".join(html.escape(l) for l in pay_list_buz)
    
    if doc_type == "Official Invoice":
        doc_html_buz = f"""<div class="quote-box"><b>SEED 2 HARVEST (PTY) LTD — OFFICIAL TAX INVOICE</b><br>123 Agricultural Way, Cape Town, 8001<br>support@seed2harvest.co.za | +27 21 555 0192<hr><b>BILLED TO:</b> {e_buz(st.session_state.user_data['name'])} ({e_buz(st.session_state.user_data['farm'])})<br><b>DELIVERY ADDRESS:</b> {e_buz(location_input)}<br><b>CONTACT:</b> {e_buz(phone)} | {e_buz(email_input)}<br><b>INVOICE NO:</b> {receipt_no} &nbsp;|&nbsp; <b>DATE:</b> {date_str_buz}<table><tr><th>DESCRIPTION</th><th>QTY</th><th>UNIT PRICE</th><th>TOTAL</th></tr>{rows_html_buz}</table><b>SUBTOTAL:</b> R {subtotal_buz:.2f}<br><b>15% VAT:</b> R {tax_total_buz:.2f}<br><b>TOTAL DUE:</b> R {grand_total_buz:.2f}</div>"""
    else:
        bank_qrs_buz = [(name, url, make_qr_png(url, box_size=6)) for name, url in BANKS]
        doc_html_buz = f"""<div class="quote-box"><b>SEED 2 HARVEST — QR CODE QUOTATION SUMMARY</b><br><b>REF:</b> {receipt_no} | <b>TO:</b> {e_buz(email_input)}<table><tr><th>DESCRIPTION</th><th>QTY</th><th>UNIT PRICE</th><th>TOTAL</th></tr>{rows_html_buz}</table><b>TOTAL (incl. 15% VAT):</b> R {grand_total_buz:.2f}<br><br><b>PAYMENT DETAILS</b><br>{pay_html_buz}<br>Scan your bank's QR code below to open your bank, log in, then choose Pay / Pay beneficiary and enter the details above.</div>"""

    email_html_buz = f"<html><body style='font-family:Arial,sans-serif;color:#222;'><p>Dear {e_buz(st.session_state.user_data['name'])},</p><p>Please find your requested <b>{e_buz(doc_type.lower())}</b> for your order at {e_buz(st.session_state.user_data['farm'])}.</p><p><b>Reference:</b> {receipt_no}<br><b>Date:</b> {date_str_buz}<br><b>Delivery address:</b> {e_buz(location_input)}<br><b>Contact:</b> {e_buz(phone)}</p><table style='border-collapse:collapse;width:100%;max-width:560px;' border='1' cellpadding='6'><tr style='background:#f0e6d8;'><th align='left'>Description</th><th>Qty</th><th>Unit</th><th>Total</th></tr>{rows_html_buz}</table><p>Subtotal: R{subtotal_buz:.2f}<br>VAT (15%): R{tax_total_buz:.2f}<br><b>Total payable: R{grand_total_buz:.2f}</b></p><p><b>Payment details</b><br>{pay_html_buz}</p><p>Regards,<br>Seed 2 Harvest<br>support@seed2harvest.co.za</p></body></html>"
    email_text_buz = f"Dear {st.session_state.user_data['name']},\n\nYour {doc_type.lower()} for {st.session_state.user_data['farm']}.\nReference: {receipt_no}\nDate: {date_str_buz}\nDelivery: {location_input}\n\n{rows_text_buz}\n\nSubtotal: R{subtotal_buz:.2f}\nVAT (15%): R{tax_total_buz:.2f}\nTotal payable: R{grand_total_buz:.2f}\n\nPAYMENT DETAILS\n" + "\n".join(pay_list_buz) + "\n\nSeed 2 Harvest"
    mailto_url_buz = f"mailto:{quote(email_input)}?cc={quote('support@seed2harvest.co.za')}&subject={quote('SEED2HARVEST ORDER INFORMATION')}&body={quote(email_text_buz[:1500])}"
    gmail_url_buz = f"https://mail.google.com/mail/?view=cm&fs=1&to={quote(email_input)}&cc={quote('support@seed2harvest.co.za')}&su={quote('SEED2HARVEST ORDER INFORMATION')}&body={quote(email_text_buz[:1200])}"

    st.session_state.last_document = {"doc_html": doc_html_buz, "bank_qrs": bank_qrs_buz, "inv_no": receipt_no, "email_html": email_html_buz, "to": email_input, "doc_type": doc_type, "mailto": mailto_url_buz, "gmail": gmail_url_buz, "email_text": email_text_buz}
    return st.session_state.last_document

def render_email_status(doc):
    st.markdown(f"<a class='stButton' href='{doc['gmail']}' target='_blank'><button>OPEN IN GMAIL</button></a> &nbsp; <a class='stButton' href='{doc['mailto']}' target='_blank'><button>OPEN IN OTHER EMAIL APP</button></a>", unsafe_allow_html=True)
    st.caption("Opens a ready-written email to your client. Press send to finish.")

def render_persistent_document(doc_buz, key_prefix):
    st.markdown(f"""
    <div class="success-receipt">
        <b>TRANSACTION COMPLETE (END OF DEMONSTRATION)</b><br><br>
        Please save your specific Receipt Number to securely log in and bypass registration in the future:<br>
        <span style="font-size: 2rem; font-weight: 800; letter-spacing: 2px; color: #FFFFFF;">{doc_buz['inv_no']}</span><br><br>
        <span style="font-size: 0.85rem; color: #047857; font-weight: 600;">*Demo Note: Database synced. Active basket preserved for presentation review.</span>
    </div>
    """, unsafe_allow_html=True)
    
    render_email_status(doc_buz)
    st.markdown(doc_buz["doc_html"], unsafe_allow_html=True)
    
    if doc_buz.get("bank_qrs"):
        st.markdown("<h4 style='color: #34D399; margin-top: 20px; font-family: \"Playfair Display\", serif;'>SCAN TO OPEN YOUR BANK</h4>", unsafe_allow_html=True)
        qr_cols_buz = st.columns(len(doc_buz["bank_qrs"]))
        for col_buz, (bank_name_buz, bank_url_buz, bank_png_buz) in zip(qr_cols_buz, doc_buz["bank_qrs"]):
            with col_buz:
                st.image(bank_png_buz, width=130)
                st.markdown(f"**{bank_name_buz}**  \n[Open site]({bank_url_buz})")
        st.caption("Banks do not allow a public link that opens a pre-filled payment, so each code opens the bank. Log in, choose Pay, and use the reference and amount shown above.")
        
    st.download_button("DOWNLOAD DOCUMENT (HTML)", data=doc_buz["email_html"].encode("utf-8"), file_name=f"{doc_buz['inv_no']}.html", mime="text/html", key=f"{key_prefix}_dl_btn")

# SIDEBAR NAVIGATION
if st.session_state.authenticated:
    with st.sidebar:
        st.markdown("<div class='sidebar-title'>SEED 2 HARVEST</div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-subtitle'>OPERATIONS</div>", unsafe_allow_html=True)

        page_selection_buz = st.radio("Navigate", ["CHAT", "CATALOGUE", "RESERVE ORDER", "GLOBAL FEED", "FEATURES"], label_visibility="collapsed")
        st.session_state.current_page = page_selection_buz

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-title'>YOUR BASKET</div>", unsafe_allow_html=True)

        active_items_buz = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
        if not active_items_buz:
            st.markdown("<span style='color:#94A3B8; font-size:0.9rem;'>Empty</span>", unsafe_allow_html=True)
        else:
            for prod_buz, qty_buz in active_items_buz:
                st.markdown(f"<span style='color:#F8FAFC; font-size:0.9rem;'>- {qty_buz}x {prod_buz}</span>", unsafe_allow_html=True)
            _, _, _total_buz = basket_totals_buz()
            st.markdown(f"<span style='color:#34D399; font-size:0.85rem; font-weight:700;'>Total: R{_total_buz:.2f}</span>", unsafe_allow_html=True)

        if st.button("CLEAR BASKET"):
            clear_basket_buz()
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("TERMINATE"):
            st.session_state.authenticated = False
            st.session_state.messages = []
            clear_basket_buz()
            st.session_state.last_document = None
            st.rerun()

# MAIN APP HEADER
st.markdown("""
<div class="cinematic-hero">
    <h1>Seed. Intelligence. Harvest.</h1>
    <p>Precision Agricultural Operations Suite</p>
</div>
""", unsafe_allow_html=True)


# ================= VIEWS =================
if not st.session_state.authenticated:
    st.markdown("<div class='section-header'>CLIENT ONBOARDING</div>", unsafe_allow_html=True)

    tot_users_buz, avg_items_buz, top_location_buz = get_platform_stats()
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap;">
        <div class="glass-panel" style="flex: 1; text-align: center; margin-bottom: 0;">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Registered Users</div>
            <div style="font-size: 2rem; font-weight: 800; color: #34D399; font-family: 'Playfair Display', serif;">{tot_users_buz}</div>
        </div>
        <div class="glass-panel" style="flex: 1; text-align: center; margin-bottom: 0;">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Avg Items / User</div>
            <div style="font-size: 2rem; font-weight: 800; color: #34D399; font-family: 'Playfair Display', serif;">{avg_items_buz}</div>
        </div>
        <div class="glass-panel" style="flex: 1; text-align: center; margin-bottom: 0;">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Top Region</div>
            <div style="font-size: 1.5rem; font-weight: 800; color: #34D399; font-family: 'Playfair Display', serif; margin-top: 8px;">{top_location_buz}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1_buz, tab2_buz = st.tabs(["NEW REGISTRATION", "RETURNING CLIENT"])
    
    with tab1_buz:
        col_form_buz, _ = st.columns([2, 1])
        with col_form_buz:
            with st.form("onboarding_form", clear_on_submit=False):
                client_name_buz = st.text_input("NAME", key="onboard_name")
                client_farm_buz = st.text_input("FARM / COMPANY", key="onboard_farm")
                client_location_buz = st.text_input("LOCATION", key="onboard_loc")
                client_email_buz = st.text_input("EMAIL ADDRESS", key="onboard_email")
                st.markdown("""<div class="custom-warning">Hello fellow farmer. For the agent to work effectively we need permission to work with your data. Click yes to continue or leave.</div>""", unsafe_allow_html=True)
                permission_buz = st.checkbox("I GRANT PERMISSION")
                submitted_buz = st.form_submit_button("AUTHORIZE ENTRY")

            if submitted_buz:
                client_name_buz, client_farm_buz = client_name_buz.strip(), client_farm_buz.strip()
                client_location_buz, client_email_buz = client_location_buz.strip(), client_email_buz.strip()
                if not (client_name_buz and client_farm_buz and client_location_buz and client_email_buz and permission_buz):
                    st.error("Please complete all fields, provide an email address, and grant permission to proceed.")
                elif "@" not in client_email_buz or "." not in client_email_buz.split("@")[-1]:
                    st.error("Please enter a valid email address.")
                else:
                    # IMMEDIATELY REGISTER TO DATABASE -> INCREMENTS 115 TO 116+
                    new_uuid = db.register_new_client(client_name_buz, client_email_buz, client_location_buz)
                    st.session_state.user_data = {
                        "name": client_name_buz, 
                        "farm": client_farm_buz, 
                        "location": client_location_buz, 
                        "email": client_email_buz,
                        "farmer_uuid": new_uuid
                    }
                    st.session_state.authenticated = True
                    st.rerun()
                    
    with tab2_buz:
        col_login_buz, _ = st.columns([2, 1])
        with col_login_buz:
            st.markdown("""<div class="custom-warning">Welcome back. Enter your receipt or invoice number (e.g. C715, CF6834558) to instantly restore your operational profile.</div>""", unsafe_allow_html=True)
            receipt_input_buz = st.text_input("RECEIPT NUMBER")
            if st.button("VERIFY & LOGIN"):
                if not receipt_input_buz:
                    st.error("Please enter a valid receipt number.")
                else:
                    recovered_data_buz = login_with_receipt(receipt_input_buz)
                    if recovered_data_buz:
                        st.session_state.user_data = recovered_data_buz
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("Authentication Failed: Receipt number not found in active database.")

elif page_selection_buz == "CHAT":
    st.markdown("<div class='section-header'>STRATEGIC AGENT</div>", unsafe_allow_html=True)

    # DYNAMIC AGRONOMIC TELEMETRY WIDGET (LIVE IOT STREAM)
    loc_val = st.session_state.user_data.get("location") or "Western Cape"
    temp_val, moist_val, ph_val, rain_val = get_live_agronomic_telemetry(loc_val)
    
    st.caption(f"● LIVE IOT TELEMETRY — SENSOR ARRAY #021 [{loc_val.upper()}] — UPDATED {datetime.datetime.now().strftime('%H:%M:%S')}")
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap;">
        <div class="glass-panel" style="flex: 1; text-align: center; margin-bottom: 0;">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Current Temp</div>
            <div style="font-size: 2rem; font-weight: 800; color: #34D399; font-family: 'Playfair Display', serif;">{temp_val} °C</div>
        </div>
        <div class="glass-panel" style="flex: 1; text-align: center; margin-bottom: 0;">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Soil Moisture</div>
            <div style="font-size: 2rem; font-weight: 800; color: #34D399; font-family: 'Playfair Display', serif;">{moist_val}%</div>
        </div>
        <div class="glass-panel" style="flex: 1; text-align: center; margin-bottom: 0;">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Soil pH</div>
            <div style="font-size: 2rem; font-weight: 800; color: #34D399; font-family: 'Playfair Display', serif;">{ph_val}</div>
        </div>
        <div class="glass-panel" style="flex: 1; text-align: center; margin-bottom: 0;">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Next Rain</div>
            <div style="font-size: 2rem; font-weight: 800; color: #34D399; font-family: 'Playfair Display', serif;">{rain_val} Days</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # VOICE INPUT (WEB SPEECH API REQ-05) & MENU TOGGLE CONTROLS
    components.html("""
    <style>
        .btn-panel { display: flex; gap: 12px; margin-bottom: 10px; font-family: 'Plus Jakarta Sans', sans-serif; }
        .action-btn {
            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
            color: #FFFFFF;
            padding: 10px 18px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 0.82rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 6px 16px rgba(16, 185, 129, 0.3);
            border: none;
            letter-spacing: 0.5px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(16, 185, 129, 0.45);
        }
        .voice-recording {
            background: linear-gradient(135deg, #EF4444 0%, #B91C1C 100%) !important;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
            70% { box-shadow: 0 0 0 12px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }
        body { margin: 0; padding: 0; background: transparent; }
    </style>

    <div class="btn-panel">
        <button class="action-btn" onclick="
            let btn = window.parent.document.querySelector(`[data-testid='stSidebarCollapsedControl']`) || 
                      window.parent.document.querySelector(`[data-testid='collapsedControl']`);
            if(btn) btn.click();
        ">
            ☰ OPEN MENU NAVIGATION
        </button>
        <button id="micBtn" class="action-btn" onclick="toggleSpeech()">
            🎙️ SPEAK PROMPT (VOICE INPUT)
        </button>
    </div>

    <script>
        let recognition = null;
        let isRecording = false;

        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRec();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-ZA';

            recognition.onstart = function() {
                isRecording = true;
                const mic = document.getElementById('micBtn');
                mic.classList.add('voice-recording');
                mic.innerText = '🔴 LISTENING... SPEAK NOW';
            };

            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                const inputArea = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (inputArea) {
                    inputArea.value = transcript;
                    inputArea.dispatchEvent(new Event('input', { bubbles: true }));
                    inputArea.focus();
                }
            };

            recognition.onerror = function(event) {
                console.error("Speech error", event);
                resetMic();
            };

            recognition.onend = function() {
                resetMic();
            };
        } else {
            document.getElementById('micBtn').style.display = 'none';
        }

        function resetMic() {
            isRecording = false;
            const mic = document.getElementById('micBtn');
            if (mic) {
                mic.classList.remove('voice-recording');
                mic.innerText = '🎙️ SPEAK PROMPT (VOICE INPUT)';
            }
        }

        function toggleSpeech() {
            if (!recognition) return;
            if (isRecording) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }
    </script>
    """, height=55)

    # QUICK GUIDE
    st.markdown("""
    <div class="chat-quick-guide">
        <div style="font-family:'Playfair Display', serif; font-weight: 700; font-size: 1.1rem; color: #34D399; margin-bottom: 12px; letter-spacing: 1px;">QUICK START GUIDE</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <div class="guide-item"><b>Voice Enabled</b>: Click 'Speak Prompt' to talk via microphone</div>
            <div class="guide-item"><b>Conversational Cart</b>: Tell me 'add 10 BioBoost' to load basket directly</div>
            <div class="guide-item"><b>Product Expert</b>: Ask about crop dosages and fungal remedies</div>
            <div class="guide-item"><b>Local Slang</b>: I understand SA vernacular (blaarbrand, kunsmis)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    USER_IDENTITY_PROMPT_BUZ = f"""
    You are the Seed 2 Harvest Strategic Agent.
    SMME Partner: Shaun Cairns (Cape Town, South Africa).

    CURRENT CLIENT PROFILE:
    - Name: {st.session_state.user_data['name']}
    - Farm/Company: {st.session_state.user_data['farm']}
    - Location/Address: {st.session_state.user_data['location']}
    - Email: {st.session_state.user_data['email']}

    CLIENT'S CURRENT BASKET:
    {basket_context_buz()}

    CRITICAL INSTRUCTIONS:
    1. Ground your advice in the certified product catalog:
    {catalog_context_buz}
    2. YOU ALREADY KNOW THE CLIENT'S NAME, FARM, LOCATION, AND EMAIL. DO NOT ASK FOR THIS INFORMATION AGAIN.
    3. You can see the LIVE basket above. If it says "EMPTY" and they ask for an invoice, tell them you can add the products to their basket right now if they state which items, or they can use the CATALOGUE menu.
    4. You cannot send emails or generate files yourself. Tell them to use the "PREPARE" button below the chat.
    5. AGENTIC ACTION (CONVERSATIONAL COMMERCE): You have full power to update the user's basket directly!
    Whenever the user asks you to add, order, buy, or put products into their basket, append this exact command tag at the very end of your response:
    ||UPDATE: Exact Product Name : Quantity||
    Example: ||UPDATE: NitroGrow Pellets 10kg : 62||
    Use the exact catalogue name. Never show code blocks around it.
    6. Keep responses concise, professional, and actionable. Do not use emojis.
    """

    if not st.session_state.messages:
        st.session_state.messages = [
            {"role": "assistant", "content": f"Welcome back, {st.session_state.user_data['name']}. How can I assist your operations at {st.session_state.user_data['farm']} today?"}
        ]

    for msg_buz in st.session_state.messages:
        with st.chat_message(msg_buz["role"]):
            st.markdown(msg_buz["content"])

    # CHAT INPUT
    if user_prompt_buz := st.chat_input("MESSAGE"):
        with st.chat_message("user"):
            st.markdown(user_prompt_buz)
        st.session_state.messages.append({"role": "user", "content": user_prompt_buz})

        normalized_prompt_buz = AgriculturalMiddleware.normalize_vernacular(user_prompt_buz)

        if not groq_client:
            st.error("SYSTEM ERROR: API connectivity offline.")
        else:
            try:
                conversation_history_buz = [{"role": "system", "content": USER_IDENTITY_PROMPT_BUZ}]
                for m in st.session_state.messages[:-1]:
                    conversation_history_buz.append({"role": m["role"], "content": m["content"]})
                conversation_history_buz.append({"role": "user", "content": normalized_prompt_buz})

                chat_completion_buz = groq_client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=conversation_history_buz,
                    temperature=0.3,
                    max_tokens=900
                )
                original_reply_buz = chat_completion_buz.choices[0].message.content
                reply_buz = original_reply_buz
                
                # Conversational Commerce AI Interceptor
                updates_buz = re.findall(r'\|\|UPDATE:\s*(.*?)\s*:\s*(\d+)\|\|', reply_buz)
                basket_was_updated = False
                
                if updates_buz:
                    for prod_name, qty_str in updates_buz:
                        prod_name = prod_name.strip()
                        qty = int(qty_str)
                        if prod_name in price_map_buz:
                            if qty > 0:
                                st.session_state.basket[prod_name] = qty
                                st.session_state[f"cat_{prod_name}"] = qty
                            else:
                                st.session_state.basket.pop(prod_name, None)
                                st.session_state[f"cat_{prod_name}"] = 0
                            basket_was_updated = True
                    reply_buz = re.sub(r'\|\|UPDATE:.*?\|\|', '', reply_buz).strip()

                with st.chat_message("assistant"):
                    st.markdown(reply_buz)
                st.session_state.messages.append({"role": "assistant", "content": reply_buz})
                
                # BROWSER SPEECH SYNTHESIS (READ ALOUD REQ-05)
                clean_speech_text = re.sub(r'[*_#`\n]', ' ', reply_buz).replace('"', '\\"')[:300]
                components.html(f"""
                <script>
                    if ('speechSynthesis' in window) {{
                        window.speechSynthesis.cancel();
                        const utterance = new SpeechSynthesisUtterance("{clean_speech_text}");
                        utterance.rate = 1.0;
                        utterance.pitch = 1.0;
                        window.speechSynthesis.speak(utterance);
                    }}
                </script>
                """, height=0)

                if basket_was_updated:
                    st.rerun()
                    
            except Exception as err:
                st.error(f"Inference Engine Error: {err}")

    # DOCUMENT ACTION GATEWAY
    _billing_words_buz = ("invoice", "quote", "quotation", "qr", "email", "bill", "order")
    _recent_buz = " ".join(m["content"].lower() for m in st.session_state.messages[-3:])
    _chat_items_buz = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
    
    if any(w in _recent_buz for w in _billing_words_buz):
        st.markdown("---")
        if not _chat_items_buz:
            st.warning("⚠️ **Your basket is currently empty.** The system cannot generate an invoice for R0.00. Please navigate to the **CATALOGUE** via the menu, or tell the agent 'Add [product]' to load your cart directly.")
        else:
            st.markdown("<div class='section-header'>SEND DOCUMENT FROM BASKET</div>", unsafe_allow_html=True)
            _, _, _gt_buz = basket_totals_buz()
            st.caption(f"Basket total incl. VAT: R{_gt_buz:.2f}. It will be addressed to {st.session_state.user_data['email']}.")
            chat_doc_type_buz = st.radio("Document type", ["Official Invoice", "QR Code Quotation Summary"], horizontal=True, key="chat_doc_type")
            chat_phone_buz = st.text_input("Contact number (optional)", key="chat_phone")
            
            if st.button(f"PREPARE {chat_doc_type_buz.upper()}", key="chat_send_btn"):
                with st.spinner("Processing transaction and preparing document..."):
                    order_ids_buz = []
                    for prod_buz, qty_buz in _chat_items_buz:
                        success_buz, db_result_buz = db.process_order_transaction(
                            farmer_name=st.session_state.user_data["name"],
                            phone=chat_phone_buz or "Not provided",
                            location=st.session_state.user_data["location"],
                            product_name=prod_buz,
                            quantity=qty_buz,
                            existing_uuid=st.session_state.user_data.get("farmer_uuid")
                        )
                        if success_buz:
                            order_ids_buz.append(str(db_result_buz["order_id"]))
                    
                    if order_ids_buz:
                        receipt_no_buz = f"C{order_ids_buz[0]}"
                        generate_and_send(chat_doc_type_buz, st.session_state.user_data["location"], chat_phone_buz or "Not provided", st.session_state.user_data["email"], receipt_no_buz)
                    else:
                        st.error("Failed to commit transaction to database. Stock may be depleted.")
                        
    if st.session_state.last_document:
        render_persistent_document(st.session_state.last_document, "chat")

elif page_selection_buz == "CATALOGUE":
    st.markdown("<div class='section-header'>PRODUCT CATALOGUE</div>", unsafe_allow_html=True)
    st.caption("Browse our professional agricultural formulations. Rendered instantly with clean, modern glassmorphism.")

    cols_grid_buz = st.columns(3)
    for index_buz, row_buz in enumerate(catalog_data_buz):
        p_name_buz, p_cat_buz, p_stock_buz, p_price_buz, p_guide_buz = row_buz[0], row_buz[1], row_buz[2], row_buz[3], row_buz[4]
        
        with cols_grid_buz[index_buz % 3]:
            st.markdown(f"""
            <div class="glass-card">
                <span style="background: rgba(52, 211, 153, 0.2); color: #34D399; padding: 4px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; border: 1px solid rgba(52, 211, 153, 0.3);">{p_cat_buz}</span>
                <h3 style="font-family: 'Playfair Display', serif; font-size: 1.5rem; color: #FFFFFF; margin: 12px 0 8px 0;">{p_name_buz}</h3>
                <p style="color: #CBD5E1; font-size: 0.85rem; margin-bottom: 15px; line-height: 1.5;"><b>Guideline:</b> {p_guide_buz}</p>
                <div style="font-size: 1.4rem; font-weight: 800; color: #34D399; margin-bottom: 4px;">ZAR {p_price_buz:.2f}</div>
                <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 15px; font-weight: 600; letter-spacing: 0.5px;">{p_stock_buz} UNITS IN STOCK</div>
            </div>
            """, unsafe_allow_html=True)

            key_buz = f"cat_{p_name_buz}"
            if key_buz not in st.session_state:
                st.session_state[key_buz] = int(st.session_state.basket.get(p_name_buz, 0))
            st.number_input(
                f"Qty ({p_name_buz})", min_value=0, max_value=int(p_stock_buz), step=1,
                key=key_buz, on_change=set_basket_qty_buz, args=(p_name_buz,), label_visibility="collapsed"
            )
            st.markdown("<br>", unsafe_allow_html=True)

elif page_selection_buz == "RESERVE ORDER":
    st.markdown("<div class='section-header'>RESERVE ORDER & OFFICIAL QUOTATION</div>", unsafe_allow_html=True)

    col1_buz, col2_buz = st.columns(2)
    with col1_buz:
        st.text_input("FARM / COMPANY", value=st.session_state.user_data["farm"], disabled=True)
        location_input_buz = st.text_input("LOCATION / DELIVERY ADDRESS", value=st.session_state.user_data["location"])

    with col2_buz:
        st.text_input("CLIENT NAME", value=st.session_state.user_data["name"], disabled=True)
        email_input_buz = st.text_input("EMAIL FOR QUOTATION", value=st.session_state.user_data["email"])
        phone_buz = st.text_input("CONTACT NUMBER")

    doc_type_buz = st.radio("SELECT DOCUMENT TYPE TO GENERATE:", ["Official Invoice", "QR Code Quotation Summary"], horizontal=True)

    st.markdown("### CURRENT BASKET ITEMS")
    active_items_buz = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
    if not active_items_buz:
        st.warning("Your basket is empty. Add items from the Catalogue page.")
    else:
        for item_buz, qty_buz in active_items_buz:
            st.write(f"- {qty_buz}x {item_buz}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("PROCESS TRANSACTION & PREPARE DOCUMENT"):
        if not phone_buz or not email_input_buz:
            st.error("Contact number and email are required to process the order and dispatch documentation.")
        elif not active_items_buz:
            st.error("Cannot generate documentation with an empty basket.")
        else:
            order_ids_buz = []
            for prod_buz, qty_buz in active_items_buz:
                success_buz, result_buz = db.process_order_transaction(
                    farmer_name=st.session_state.user_data["name"],
                    phone=phone_buz,
                    location=location_input_buz,
                    product_name=prod_buz,
                    quantity=qty_buz,
                    existing_uuid=st.session_state.user_data.get("farmer_uuid")
                )
                if success_buz:
                    order_ids_buz.append(str(result_buz["order_id"]))
            
            if order_ids_buz:
                receipt_no_buz = f"C{order_ids_buz[0]}"
                generate_and_send(doc_type_buz, location_input_buz, phone_buz, email_input_buz, receipt_no_buz)
            else:
                st.error("Failed to commit transaction to database. Stock may be depleted.")

    if st.session_state.last_document:
        render_persistent_document(st.session_state.last_document, "reserve")

elif page_selection_buz == "GLOBAL FEED":
    st.markdown("<div class='section-header'>GLOBAL FEED & MARKET CONDITIONS</div>", unsafe_allow_html=True)

    # DYNAMIC SAFEX COMMODITY MARKET TICKER
    commodities = get_live_commodity_prices()
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M SAST')
    
    st.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.65); backdrop-filter: blur(16px); padding: 30px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.15); margin-bottom: 25px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.6);">
        <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap;">
            <h3 style="color: #34D399; font-family: 'Playfair Display', serif; margin-top:0; font-size: 1.5rem;">DAILY SAFEX COMMODITY PRICES</h3>
            <span style="color: #94A3B8; font-size: 0.78rem;">LIVE FEED • LAST SYNC: {now_time}</span>
        </div>
        <p style="color: #94A3B8; font-size: 0.85rem; margin-bottom: 15px;">Simulated spot market closing prices (ZAR/TON) with daily variance delta</p>
        {"".join([f'''
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding: 12px 0;">
                <span style="font-weight: 500;">{c['name']}</span>
                <div>
                    <span style="color: {'#34D399' if c['is_up'] else '#F87171'}; font-size: 0.82rem; margin-right: 14px; font-weight: 700;">{c['delta']}</span>
                    <b style="color: #F8FAFC; font-size: 1.05rem;">{c['price']}</b>
                </div>
            </div>
        ''' for c in commodities])}
    </div>
    """, unsafe_allow_html=True)

    col_map_buz, col_qr_buz = st.columns([2, 1])
    with col_map_buz:
        st.markdown("### INTERACTIVE FARM MAP")
        user_loc_buz = st.session_state.user_data['location'] or "Cape Town, South Africa"
        st.write(f"Delivery Location: **{user_loc_buz}**")

        encoded_loc_buz = quote(user_loc_buz)
        gmaps_iframe_buz = f"""
        <iframe 
            width="100%" 
            height="400" 
            frameborder="0" 
            scrolling="no" 
            marginheight="0" 
            marginwidth="0" 
            src="https://maps.google.com/maps?q={encoded_loc_buz}&hl=en&z=14&amp;output=embed"
            style="border-radius: 16px; border: 1px solid rgba(255,255,255,0.15); box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
        </iframe>
        """
        st.markdown(gmaps_iframe_buz, unsafe_allow_html=True)

    with col_qr_buz:
        st.markdown("### OFFICIAL WEBSITE QR CODE")
        st.write("Scan to visit **Seed 2 Harvest** portal:")
        st.image(make_qr_png("https://seed2harvest.co.za"), width=180)

elif page_selection_buz == "FEATURES":
    st.markdown("<div class='section-header'>PLATFORM FEATURES</div>", unsafe_allow_html=True)
    
    FEATURES_LIST_BUZ = [
        ("STRATEGIC AGENT", "Chat with an AI advisor grounded in our certified product catalogue. It knows your farm profile and what is in your basket."),
        ("LIVE CATALOGUE", "Browse products with current stock and pricing. Set quantities and your basket updates instantly in the sidebar."),
        ("SMART BASKET", "Your basket is shared across every page and the agent can see it, so you can ask for advice or a quote on exactly what you picked."),
        ("INVOICES & QUOTES", "Generate an official tax invoice (15% VAT) or a QR code quotation summary, and download it or have it emailed to you."),
        ("VOICE ACCESSIBILITY", "Web Speech API integration supporting microphone voice input and text-to-speech feedback for low-literacy farmers."),
        ("POPIA CRYPTOGRAPHIC VAULT", "PII isolation decoupled with AES-256 application encryption and Write-Ahead Logging for transactional integrity."),
    ]
    
    cols_buz = st.columns(2)
    for i_buz, (title_buz, desc_buz) in enumerate(FEATURES_LIST_BUZ):
        with cols_buz[i_buz % 2]:
            st.markdown(f"<div class='glass-card'><h4>{title_buz}</h4><p>{desc_buz}</p></div>", unsafe_allow_html=True)

# FOOTER
st.markdown("""
<div class='footer'>
    <h4>BUZUZI INCORPORATED</h4>
    <p>FOLLOW ON SOCIALS: @SEED2HARVEST_GLOBAL</p>
    <p style="margin-top: 12px; font-size: 0.85rem; color: #34D399; text-transform: none; letter-spacing: 0px;">Created by Ashley Tinotenda Buzuzi, Software Engineer (CEO)</p>
</div>
""", unsafe_allow_html=True)
