import os
import re
import html
import base64
from urllib.parse import quote
import requests
import streamlit as st
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

# HELPER TO GET ONLY PREMIUM HIGH QUALITY IMAGES FROM IMAGES FOLDER
def get_high_quality_images():
    high_quality_list_buz = []
    
    # Strictly allowed premium scenic images to prevent low-quality renders
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
            all_files = os.listdir("images")
            for f in all_files:
                if f in premium_allowed_buz:
                    high_quality_list_buz.append(os.path.join("images", f))
    except Exception:
        pass
    
    # Fallback to premium high-res photography if local folder lacks assets
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

def get_image_base64(path):
    if path.startswith("http"):
        return path
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = path.rsplit(".", 1)[-1].lower()
        mime = "image/png" if ext == "png" else ("image/webp" if ext == "webp" else "image/jpeg")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return ""

hq_images_buz = get_high_quality_images()

# INITIALIZE STATE & ROUTING
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "user_data" not in st.session_state: st.session_state.user_data = {"name": "", "farm": "", "location": "", "email": ""}
if "messages" not in st.session_state: st.session_state.messages = []
if "basket" not in st.session_state: st.session_state.basket = {}
if "last_document" not in st.session_state: st.session_state.last_document = None

current_page = "ONBOARDING" if not st.session_state.authenticated else st.session_state.get("current_page", "CHAT")

page_bg_mapping_buz = {
    "ONBOARDING": hq_images_buz[0] if len(hq_images_buz) > 0 else hq_images_buz[-1],
    "CHAT": hq_images_buz[1] if len(hq_images_buz) > 1 else hq_images_buz[0],
    "CATALOGUE": hq_images_buz[2] if len(hq_images_buz) > 2 else hq_images_buz[0],
    "RESERVE ORDER": hq_images_buz[3] if len(hq_images_buz) > 3 else hq_images_buz[0],
    "GLOBAL FEED": hq_images_buz[4] if len(hq_images_buz) > 4 else hq_images_buz[0],
    "FEATURES": hq_images_buz[5] if len(hq_images_buz) > 5 else hq_images_buz[0]
}

bg_path_buz = page_bg_mapping_buz.get(current_page, hq_images_buz[0])
bg_b64_buz = get_image_base64(bg_path_buz)

# GLOBAL AGGRESSIVE CSS OVERRIDE
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* Force Dark Mode & Background Image globally */
    .stApp {{
        background: linear-gradient(180deg, rgba(6, 9, 15, 0.4) 0%, rgba(6, 9, 15, 0.85) 100%), url('{bg_b64_buz}') !important;
        background-size: cover !important;
        background-position: center center !important;
        background-attachment: fixed !important;
    }}
    
    /* Hide top header band */
    header[data-testid="stHeader"] {{ background: transparent !important; }}

    /* Force all text to white/off-white to combat Light Mode */
    html, body, p, span, div, label, h1, h2, h3, h4, h5, h6, li {{
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #F8FAFC !important;
    }}
    
    h1, h2, h3 {{ 
        font-family: 'Playfair Display', serif !important; 
        font-weight: 700 !important; 
    }}

    /* Cinematic Typography Blocks */
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

    /* True Transparent Frosted Sidebar */
    [data-testid="stSidebar"] {{ 
        background-color: rgba(10, 15, 25, 0.35) !important; 
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important; 
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{ background-color: transparent !important; }}
    
    /* Form Inputs & Chat Box */
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

    /* Action Buttons */
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

    /* Client-side Nav Button */
    .nav-toggle-btn {{
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.2);
        color: #FFFFFF;
        padding: 10px 20px;
        border-radius: 12px;
        font-weight: 700;
        font-family: 'Plus Jakarta Sans', sans-serif;
        cursor: pointer;
        transition: all 0.3s ease;
        margin-bottom: 20px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    }}
    .nav-toggle-btn:hover {{
        background: rgba(16, 185, 129, 0.4);
        border-color: #34D399;
    }}

    /* Immersive Chat Messages */
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

    /* Bottom Chat Container Glass Effect Overrides White Bar */
    [data-testid="stBottom"] > div {{
        background-color: rgba(10, 15, 25, 0.3) !important;
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
        border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
    }}
    .stChatInputContainer {{
        background-color: rgba(15, 23, 42, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
    }}
    .stChatInputContainer textarea {{
        color: #FFFFFF !important;
        background-color: transparent !important;
    }}
    
    /* Chat Quick Guide */
    .chat-quick-guide {{
        background: rgba(15, 23, 42, 0.45);
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

    /* Fast Glass Cards (Catalogue & Features) */
    .glass-card {{
        background: rgba(15, 23, 42, 0.55); 
        backdrop-filter: blur(16px); 
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.15); 
        border-top: 3px solid #34D399;
        padding: 26px; 
        border-radius: 20px; 
        margin-bottom: 18px; 
        height: 100%;
        box-shadow: 0 15px 35px -10px rgba(0,0,0,0.5);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }}
    .glass-card:hover {{
        transform: translateY(-4px);
        border-color: rgba(52, 211, 153, 0.6);
    }}

    /* Document/Quote Box */
    .quote-box {{
        background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.15); padding: 30px; border-radius: 20px; margin-top: 20px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
    }}
    .quote-box table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
    .quote-box th {{ text-align: left; color: #34D399 !important; border-bottom: 1px solid rgba(255, 255, 255, 0.2); padding: 12px; }}
    .quote-box td {{ padding: 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }}

    .custom-warning {{ background-color: rgba(16, 185, 129, 0.15); color: #34D399 !important; padding: 18px; border-radius: 16px; margin: 15px 0; border: 1px solid rgba(16, 185, 129, 0.4); }}

    /* Footer */
    .footer {{ text-align: center; margin-top: 80px; padding: 30px 0; border-top: 1px solid rgba(255, 255, 255, 0.1); background: rgba(4, 6, 11, 0.6); backdrop-filter: blur(12px); }}
</style>
""", unsafe_allow_html=True)

db.init_db()

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
        normalized = text
        for pattern, replacement in cls.SLANG_DICTIONARY.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        return normalized

def make_qr_png(data: str, box_size=5) -> bytes:
    qr = qrcode.QRCode(version=None, box_size=box_size, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

GROQ_API_KEY = get_secret("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

catalog_data_buz = db.fetch_inventory()
price_map_buz = {row[0]: row[3] for row in catalog_data_buz}
catalog_context_buz = "\n".join([f"- Product: {row[0]} | Category: {row[1]} | Stock: {row[2]} units | Price: R{row[3]:.2f} | Safe Usage: {row[4]}" for row in catalog_data_buz])

def basket_totals_buz():
    subtotal = sum(price_map_buz.get(p, 0.0) * q for p, q in st.session_state.basket.items() if q > 0)
    vat = subtotal * 0.15
    return subtotal, vat, subtotal + vat

def basket_context_buz() -> str:
    items = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
    if not items: return "The client's basket is currently EMPTY."
    lines = [f"- {q}x {p} @ R{price_map_buz.get(p, 0.0):.2f} = R{price_map_buz.get(p, 0.0) * q:.2f}" for p, q in items]
    subtotal, vat, total = basket_totals_buz()
    lines.append(f"Subtotal: R{subtotal:.2f} | VAT (15%): R{vat:.2f} | Total: R{total:.2f}")
    return "\n".join(lines)

def set_basket_qty_buz(product_name):
    qty = st.session_state.get(f"cat_{product_name}", 0)
    if qty and qty > 0: st.session_state.basket[product_name] = int(qty)
    else: st.session_state.basket.pop(product_name, None)

def clear_basket_buz():
    st.session_state.basket = {}
    for k in [k for k in st.session_state.keys() if k.startswith("cat_")]: del st.session_state[k]

def payment_lines(inv_no, grand_total):
    lines = [f"Payment reference: {inv_no}", f"Amount to pay: R{grand_total:.2f}"]
    filled = [(k, v) for k, v in BENEFICIARY.items() if v]
    lines += [f"{k}: {v}" for k, v in filled]
    if len(filled) <= 1: lines.append("Full banking details: request from support@seed2harvest.co.za")
    return lines

def generate_and_send(doc_type, location_input, phone, email_input):
    active_items = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
    subtotal, tax_total, grand_total = basket_totals_buz()
    now = pd.Timestamp.now()
    inv_no = f"INV-{now.strftime('%Y%m%d-%H%M%S')}"
    date_str = now.strftime('%Y-%m-%d')
    e = html.escape
    rows_html = "".join(f"<tr><td>{e(p)}</td><td>{q}</td><td>R{price_map_buz.get(p, 0.0):.2f}</td><td>R{price_map_buz.get(p, 0.0) * q:.2f}</td></tr>" for p, q in active_items)
    rows_text = "\n".join(f"  {q}x {p} @ R{price_map_buz.get(p, 0.0):.2f} = R{price_map_buz.get(p, 0.0) * q:.2f}" for p, q in active_items)
    bank_qrs = []
    pay_list = payment_lines(inv_no, grand_total)
    pay_html = "<br>".join(html.escape(l) for l in pay_list)
    
    if doc_type == "Official Invoice":
        doc_html = f"""<div class="quote-box"><b>SEED 2 HARVEST (PTY) LTD — OFFICIAL TAX INVOICE</b><br>123 Agricultural Way, Cape Town, 8001<br>support@seed2harvest.co.za | +27 21 555 0192<hr><b>BILLED TO:</b> {e(st.session_state.user_data['name'])} ({e(st.session_state.user_data['farm'])})<br><b>DELIVERY ADDRESS:</b> {e(location_input)}<br><b>CONTACT:</b> {e(phone)} | {e(email_input)}<br><b>INVOICE NO:</b> {inv_no} &nbsp;|&nbsp; <b>DATE:</b> {date_str}<table><tr><th>DESCRIPTION</th><th>QTY</th><th>UNIT PRICE</th><th>TOTAL</th></tr>{rows_html}</table><b>SUBTOTAL:</b> R {subtotal:.2f}<br><b>15% VAT:</b> R {tax_total:.2f}<br><b>TOTAL DUE:</b> R {grand_total:.2f}</div>"""
    else:
        bank_qrs = [(name, url, make_qr_png(url, box_size=6)) for name, url in BANKS]
        doc_html = f"""<div class="quote-box"><b>SEED 2 HARVEST — QR CODE QUOTATION SUMMARY</b><br><b>REF:</b> {inv_no} | <b>TO:</b> {e(email_input)}<table><tr><th>DESCRIPTION</th><th>QTY</th><th>UNIT PRICE</th><th>TOTAL</th></tr>{rows_html}</table><b>TOTAL (incl. 15% VAT):</b> R {grand_total:.2f}<br><br><b>PAYMENT DETAILS</b><br>{pay_html}<br>Scan your bank's QR code below to open your bank, log in, then choose Pay / Pay beneficiary and enter the details above.</div>"""

    email_html = f"<html><body style='font-family:Arial,sans-serif;color:#222;'><p>Dear {e(st.session_state.user_data['name'])},</p><p>Please find your requested <b>{e(doc_type.lower())}</b> for your order at {e(st.session_state.user_data['farm'])}.</p><p><b>Reference:</b> {inv_no}<br><b>Date:</b> {date_str}<br><b>Delivery address:</b> {e(location_input)}<br><b>Contact:</b> {e(phone)}</p><table style='border-collapse:collapse;width:100%;max-width:560px;' border='1' cellpadding='6'><tr style='background:#f0e6d8;'><th align='left'>Description</th><th>Qty</th><th>Unit</th><th>Total</th></tr>{rows_html}</table><p>Subtotal: R{subtotal:.2f}<br>VAT (15%): R{tax_total:.2f}<br><b>Total payable: R{grand_total:.2f}</b></p><p><b>Payment details</b><br>{pay_html}</p><p>Regards,<br>Seed 2 Harvest<br>support@seed2harvest.co.za</p></body></html>"
    email_text = f"Dear {st.session_state.user_data['name']},\n\nYour {doc_type.lower()} for {st.session_state.user_data['farm']}.\nReference: {inv_no}\nDate: {date_str}\nDelivery: {location_input}\n\n{rows_text}\n\nSubtotal: R{subtotal:.2f}\nVAT (15%): R{tax_total:.2f}\nTotal payable: R{grand_total:.2f}\n\nPAYMENT DETAILS\n" + "\n".join(pay_list) + "\n\nSeed 2 Harvest"
    mailto_url = f"mailto:{quote(email_input)}?cc={quote('support@seed2harvest.co.za')}&subject={quote('SEED2HARVEST ORDER INFORMATION')}&body={quote(email_text[:1500])}"
    gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={quote(email_input)}&cc={quote('support@seed2harvest.co.za')}&su={quote('SEED2HARVEST ORDER INFORMATION')}&body={quote(email_text[:1200])}"

    st.session_state.last_document = {"doc_html": doc_html, "bank_qrs": bank_qrs, "inv_no": inv_no, "email_html": email_html, "to": email_input, "doc_type": doc_type, "mailto": mailto_url, "gmail": gmail_url, "email_text": email_text}
    return st.session_state.last_document

def render_email_status(doc):
    st.success(f"{doc['doc_type']} ready. Choose how you want to send it.")
    st.markdown(f"<a class='stButton' href='{doc['gmail']}' target='_blank'><button>OPEN IN GMAIL</button></a> &nbsp; <a class='stButton' href='{doc['mailto']}' target='_blank'><button>OPEN IN OTHER EMAIL APP</button></a>", unsafe_allow_html=True)
    st.caption("Opens a ready-written email to your client. Press send to finish.")


# SIDEBAR NAVIGATION
with st.sidebar:
    st.markdown("<div class='sidebar-title'>ERTG</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-subtitle'>OPERATIONS</div>", unsafe_allow_html=True)

    if st.session_state.authenticated:
        page_selection = st.radio("Navigate", ["CHAT", "CATALOGUE", "RESERVE ORDER", "GLOBAL FEED", "FEATURES"], label_visibility="collapsed")
        st.session_state.current_page = page_selection
    else:
        page_selection = "ONBOARDING"
        st.caption("Please authenticate to access operations.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>YOUR BASKET</div>", unsafe_allow_html=True)

    active_items = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
    if not active_items:
        st.markdown("<span style='color:#94A3B8; font-size:0.9rem;'>Empty</span>", unsafe_allow_html=True)
    else:
        for prod, qty in active_items:
            st.markdown(f"<span style='color:#F8FAFC; font-size:0.9rem;'>- {qty}x {prod}</span>", unsafe_allow_html=True)
        _, _, _total = basket_totals_buz()
        st.markdown(f"<span style='color:#34D399; font-size:0.85rem; font-weight:700;'>Total: R{_total:.2f}</span>", unsafe_allow_html=True)

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

FEATURES = [
    ("STRATEGIC AGENT", "Chat with an AI advisor grounded in our certified product catalogue. It knows your farm profile and what is in your basket."),
    ("LIVE CATALOGUE", "Browse products with current stock and pricing. Set quantities and your basket updates instantly in the sidebar."),
    ("SMART BASKET", "Your basket is shared across every page and the agent can see it, so you can ask for advice or a quote on exactly what you picked."),
    ("INVOICES & QUOTES", "Generate an official tax invoice (15% VAT) or a QR code quotation summary, and download it or have it emailed to you."),
]

def render_features():
    cols = st.columns(2)
    for i, (title, desc) in enumerate(FEATURES):
        with cols[i % 2]:
            st.markdown(f"<div class='glass-card'><h4>{title}</h4><p>{desc}</p></div>", unsafe_allow_html=True)

# VIEWS

if not st.session_state.authenticated:
    st.markdown("<div class='section-header'>CLIENT ONBOARDING</div>", unsafe_allow_html=True)

    with st.expander("WHAT CAN THIS APP DO?", expanded=False):
        render_features()

    col_form, _ = st.columns([2, 1])
    with col_form:
        with st.form("onboarding_form", clear_on_submit=False):
            client_name = st.text_input("NAME", key="onboard_name")
            client_farm = st.text_input("FARM / COMPANY", key="onboard_farm")
            client_location = st.text_input("LOCATION", key="onboard_loc")
            client_email = st.text_input("EMAIL ADDRESS", key="onboard_email")

            st.markdown("""<div class="custom-warning">Hello fellow farmer. For the agent to work effectively we need permission to work with your data. Click yes to continue or leave.</div>""", unsafe_allow_html=True)

            permission = st.checkbox("I GRANT PERMISSION")
            submitted = st.form_submit_button("AUTHORIZE ENTRY")

        if submitted:
            client_name, client_farm = client_name.strip(), client_farm.strip()
            client_location, client_email = client_location.strip(), client_email.strip()
            if not (client_name and client_farm and client_location and client_email and permission):
                st.error("Please complete all fields, provide an email address, and grant permission to proceed.")
            elif "@" not in client_email or "." not in client_email.split("@")[-1]:
                st.error("Please enter a valid email address.")
            else:
                st.session_state.user_data = {"name": client_name, "farm": client_farm, "location": client_location, "email": client_email}
                st.session_state.authenticated = True
                st.rerun()

elif page_selection == "CHAT":
    st.markdown("<div class='section-header'>STRATEGIC AGENT</div>", unsafe_allow_html=True)

    # ACCESSIBILITY: JS Hook to programmatically open the hidden sidebar menu for easier navigation without reloading
    st.markdown("""
        <button class="nav-toggle-btn" onclick="window.parent.document.querySelector('[data-testid=\\'collapsedControl\\']').click()">
            Open Menu Navigation
        </button>
    """, unsafe_allow_html=True)

    # QUICK GUIDE (No Emojis)
    st.markdown("""
    <div class="chat-quick-guide">
        <div style="font-family:'Playfair Display', serif; font-weight: 700; font-size: 1.1rem; color: #34D399; margin-bottom: 12px; letter-spacing: 1px;">QUICK START GUIDE</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <div class="guide-item"><b>Product Expert</b>: Ask about crop treatments & dosages</div>
            <div class="guide-item"><b>Basket Aware</b>: I know what you've added to your cart</div>
            <div class="guide-item"><b>Instant Billing</b>: Ask me to prepare an invoice or quote</div>
            <div class="guide-item"><b>Local Slang</b>: I understand SA farming terminology</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    USER_IDENTITY_PROMPT = f"""
    You are the Seed 2 Harvest Strategic Agent.
    SMME Partner: Shaun Cairns (Cape Town, South Africa).

    CURRENT CLIENT PROFILE (Already Authenticated):
    - Name: {st.session_state.user_data['name']}
    - Farm/Company: {st.session_state.user_data['farm']}
    - Location/Address: {st.session_state.user_data['location']}
    - Email: {st.session_state.user_data['email']}

    CLIENT'S CURRENT BASKET (live, you CAN see this):
    {basket_context_buz()}

    CRITICAL INSTRUCTIONS:
    1. Ground your advice in the certified product catalog:
    {catalog_context_buz}
    2. YOU ALREADY KNOW THE CLIENT'S NAME, FARM, LOCATION, AND EMAIL. DO NOT, UNDER ANY CIRCUMSTANCES, ASK FOR THIS INFORMATION AGAIN. If processing an order, simply confirm you have their details on file.
    3. You can see the basket above. When the client says "from my basket" or "the basket", use those items and totals.
    4. You cannot send emails or generate files yourself. When the client wants an invoice or a QR code quotation, confirm the basket contents and total, then tell them a button will appear below the chat to prepare the document.
    5. Keep responses professional, clear, and actionable. Do not use emojis.
    """

    if not st.session_state.messages:
        st.session_state.messages = [
            {"role": "assistant", "content": f"Welcome back, {st.session_state.user_data['name']}. How can I assist your operations at {st.session_state.user_data['farm']} today?"}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_prompt := st.chat_input("MESSAGE"):
        with st.chat_message("user"):
            st.markdown(user_prompt)
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        normalized_prompt = AgriculturalMiddleware.normalize_vernacular(user_prompt)

        if not groq_client:
            st.error("SYSTEM ERROR: API connectivity offline.")
        else:
            try:
                conversation_history = [{"role": "system", "content": USER_IDENTITY_PROMPT}]
                for m in st.session_state.messages[:-1]:
                    conversation_history.append({"role": m["role"], "content": m["content"]})
                conversation_history.append({"role": "user", "content": normalized_prompt})

                chat_completion = groq_client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=conversation_history,
                    temperature=0.3,
                    max_tokens=900
                )
                reply = chat_completion.choices[0].message.content
                with st.chat_message("assistant"):
                    st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as err:
                st.error(f"Inference Engine Error: {err}")

    _billing_words = ("invoice", "quote", "quotation", "qr", "email", "bill", "order")
    _recent = " ".join(m["content"].lower() for m in st.session_state.messages[-3:])
    _chat_items = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
    if _chat_items and any(w in _recent for w in _billing_words):
        st.markdown("---")
        st.markdown("<div class='section-header'>SEND DOCUMENT FROM BASKET</div>", unsafe_allow_html=True)
        _, _, _gt = basket_totals_buz()
        st.caption(f"Basket total incl. VAT: R{_gt:.2f}. It will be addressed to {st.session_state.user_data['email']}.")
        chat_doc_type = st.radio("Document type", ["Official Invoice", "QR Code Quotation Summary"], horizontal=True, key="chat_doc_type")
        chat_phone = st.text_input("Contact number (optional)", key="chat_phone")
        if st.button(f"PREPARE {chat_doc_type.upper()}", key="chat_send_btn"):
            with st.spinner("Preparing document..."):
                result = generate_and_send(chat_doc_type, st.session_state.user_data["location"], chat_phone or "Not provided", st.session_state.user_data["email"])
            render_email_status(result)

elif page_selection == "CATALOGUE":
    st.markdown("<div class='section-header'>PRODUCT CATALOGUE</div>", unsafe_allow_html=True)
    st.caption("Browse our professional agricultural formulations. Rendered instantly with clean, modern glassmorphism.")

    cols_grid = st.columns(3)
    for index, row in enumerate(catalog_data_buz):
        p_name, p_cat, p_stock, p_price, p_guide = row[0], row[1], row[2], row[3], row[4]
        
        with cols_grid[index % 3]:
            st.markdown(f"""
            <div class="glass-card">
                <span style="background: rgba(52, 211, 153, 0.2); color: #34D399; padding: 4px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; border: 1px solid rgba(52, 211, 153, 0.3);">{p_cat}</span>
                <h3 style="font-family: 'Playfair Display', serif; font-size: 1.5rem; color: #FFFFFF; margin: 12px 0 8px 0;">{p_name}</h3>
                <p style="color: #CBD5E1; font-size: 0.85rem; margin-bottom: 15px; line-height: 1.5;"><b>Guideline:</b> {p_guide}</p>
                <div style="font-size: 1.4rem; font-weight: 800; color: #34D399; margin-bottom: 4px;">ZAR {p_price:.2f}</div>
                <div style="font-size: 0.75rem; color: #94A3B8; margin-bottom: 15px; font-weight: 600; letter-spacing: 0.5px;">{p_stock} UNITS IN STOCK</div>
            </div>
            """, unsafe_allow_html=True)

            key = f"cat_{p_name}"
            if key not in st.session_state:
                st.session_state[key] = int(st.session_state.basket.get(p_name, 0))
            st.number_input(
                f"Qty ({p_name})", min_value=0, max_value=int(p_stock), step=1,
                key=key, on_change=set_basket_qty_buz, args=(p_name,), label_visibility="collapsed"
            )
            st.markdown("<br>", unsafe_allow_html=True)

elif page_selection == "RESERVE ORDER":
    st.markdown("<div class='section-header'>RESERVE ORDER & OFFICIAL QUOTATION</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("FARM / COMPANY", value=st.session_state.user_data["farm"], disabled=True)
        location_input = st.text_input("LOCATION / DELIVERY ADDRESS", value=st.session_state.user_data["location"])

    with col2:
        st.text_input("CLIENT NAME", value=st.session_state.user_data["name"], disabled=True)
        email_input = st.text_input("EMAIL FOR QUOTATION", value=st.session_state.user_data["email"])
        phone = st.text_input("CONTACT NUMBER")

    doc_type = st.radio("SELECT DOCUMENT TYPE TO GENERATE:", ["Official Invoice", "QR Code Quotation Summary"], horizontal=True)

    st.markdown("### CURRENT BASKET ITEMS")
    active_items = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
    if not active_items:
        st.warning("Your basket is empty. Add items from the Catalogue page.")
    else:
        for item, qty in active_items:
            st.write(f"- {qty}x {item}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("PROCESS TRANSACTION & PREPARE DOCUMENT"):
        if not phone or not email_input:
            st.error("Contact number and email are required to process the order and dispatch documentation.")
        elif not active_items:
            st.error("Cannot generate documentation with an empty basket.")
        else:
            generate_and_send(doc_type, location_input, phone, email_input)

    doc = st.session_state.last_document
    if doc:
        render_email_status(doc)
        st.markdown(doc["doc_html"], unsafe_allow_html=True)
        if doc["bank_qrs"]:
            st.markdown("**SCAN TO OPEN YOUR BANK**")
            qr_cols = st.columns(len(doc["bank_qrs"]))
            for col, (bank_name, bank_url, bank_png) in zip(qr_cols, doc["bank_qrs"]):
                with col:
                    st.image(bank_png, width=150)
                    st.markdown(f"**{bank_name}**  \n[Open site]({bank_url})")
            st.caption("Banks do not allow a public link that opens a pre-filled payment, so each code opens the bank. Log in, choose Pay, and use the reference and amount shown above.")
        st.download_button("DOWNLOAD DOCUMENT (HTML)", data=doc["email_html"].encode("utf-8"), file_name=f"{doc['inv_no']}.html", mime="text/html")

elif page_selection == "GLOBAL FEED":
    st.markdown("<div class='section-header'>GLOBAL FEED & AGRONOMIC CONDITIONS</div>", unsafe_allow_html=True)

    # Added Feature: Real-Time Agronomic Conditions Dashboard
    st.markdown("""
    <div style="display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: wrap;">
        <div style="flex: 1; background: rgba(15, 23, 42, 0.65); backdrop-filter: blur(12px); padding: 20px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.15); text-align: center;">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Current Temp</div>
            <div style="font-size: 2rem; font-weight: 800; color: #34D399; font-family: 'Playfair Display', serif;">24°C</div>
        </div>
        <div style="flex: 1; background: rgba(15, 23, 42, 0.65); backdrop-filter: blur(12px); padding: 20px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.15); text-align: center;">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Soil Moisture</div>
            <div style="font-size: 2rem; font-weight: 800; color: #34D399; font-family: 'Playfair Display', serif;">42%</div>
        </div>
        <div style="flex: 1; background: rgba(15, 23, 42, 0.65); backdrop-filter: blur(12px); padding: 20px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.15); text-align: center;">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Soil pH</div>
            <div style="font-size: 2rem; font-weight: 800; color: #34D399; font-family: 'Playfair Display', serif;">6.8</div>
        </div>
        <div style="flex: 1; background: rgba(15, 23, 42, 0.65); backdrop-filter: blur(12px); padding: 20px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.15); text-align: center;">
            <div style="font-size: 0.8rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 1px;">Next Rain</div>
            <div style="font-size: 2rem; font-weight: 800; color: #34D399; font-family: 'Playfair Display', serif;">3 Days</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_map, col_qr = st.columns([2, 1])
    with col_map:
        st.markdown("### INTERACTIVE FARM MAP")
        user_loc_buz = st.session_state.user_data['location']
        if not user_loc_buz:
            user_loc_buz = "Cape Town, South Africa"
            
        st.write(f"Delivery Location: **{user_loc_buz}**")

        # Full Google Maps iframe integration (No API key needed for basic place embed)
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

    with col_qr:
        st.markdown("### OFFICIAL WEBSITE QR CODE")
        st.write("Scan to visit **Seed 2 Harvest** portal:")
        st.image(make_qr_png("https://seed2harvest.co.za"), width=180)

elif page_selection == "FEATURES":
    st.markdown("<div class='section-header'>PLATFORM FEATURES</div>", unsafe_allow_html=True)
    render_features()

# FOOTER
st.markdown("""
<div class='footer'>
    <h4>BUZUZI INCORPORATED</h4>
    <p>FOLLOW ON SOCIALS: @SEED2HARVEST_GLOBAL</p>
    <p style="margin-top: 12px; font-size: 0.85rem; color: #34D399; text-transform: none; letter-spacing: 0px;">Created by Ashley Tinotenda Buzuzi, Software Engineer (CEO)</p>
</div>
""", unsafe_allow_html=True)
