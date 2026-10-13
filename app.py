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

# PAGE CONFIG & STYLING
st.set_page_config(
    page_title="Seed 2 Harvest | Strategic Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    # Global Modern Reset
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp { 
        background-color: #0F172A; 
        color: #F8FAFC; 
    }

    h1, h2, h3 { 
        font-family: 'Inter', sans-serif; 
        font-weight: 700; 
        color: #F8FAFC; 
    }

    .main-title { 
        color: #F8FAFC; 
        font-size: 2.25rem; 
        line-height: 1.1; 
        margin-bottom: 2px; 
        margin-top: 5px;
        font-weight: 700;
    }
    
    .sub-title { 
        color: #10B981; 
        font-size: 0.85rem; 
        letter-spacing: 2px; 
        font-weight: 600; 
        margin-bottom: 15px;
        text-transform: uppercase;
    }
    
    .section-header { 
        color: #F8FAFC; 
        font-size: 1.25rem; 
        margin-top: 20px; 
        margin-bottom: 12px; 
        font-weight: 600;
        border-bottom: 2px solid #334155;
        padding-bottom: 6px;
    }

    # Hero banner
    .hero-banner {
        width: 100%; height: 110px; object-fit: cover; object-position: center;
        border-radius: 12px; border: 1px solid #334155; display: block; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .hero-placeholder { height: 60px; background-color: #1E293B; border: 1px solid #334155; border-radius: 12px; }

    # Inputs & Fields visibility fix
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {
        background-color: #1E293B !important; 
        color: #F8FAFC !important; 
        border: 1px solid #475569 !important; 
        border-radius: 8px;
    }
    .stTextInput > div > div > input:focus { 
        border-color: #10B981 !important; 
        box-shadow: 0 0 0 2px rgba(16,185,129,0.2); 
    }

    .custom-warning {
        background-color: #064E3B; color: #A7F3D0; padding: 14px; border-radius: 10px; margin: 12px 0; font-size: 0.9rem; border: 1px solid #059669;
    }

    # Buttons
    .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
        background-color: #10B981; color: #FFFFFF; border: none; border-radius: 8px; font-weight: 600; letter-spacing: 0.5px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover { 
        background-color: #059669; color: #FFFFFF; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);
    }

    # Sidebar Styling
    [data-testid="stSidebar"] { 
        background-color: #1E293B; 
        border-right: 1px solid #334155; 
    }
    .sidebar-title { color: #F8FAFC; font-size: 1rem; font-weight: 700; margin-bottom: 4px; }
    .sidebar-subtitle { color: #94A3B8; font-size: 0.7rem; letter-spacing: 1px; margin-bottom: 12px; font-weight: 600; }

    # Quote & Document Cards
    .quote-box {
        background-color: #1E293B; border: 1px solid #334155; padding: 24px; border-radius: 12px; font-family: 'Inter', sans-serif; color: #F8FAFC; margin-top: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .quote-box table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    .quote-box th { text-align: left; color: #34D399; border-bottom: 2px solid #334155; padding: 8px; font-size: 0.85rem; }
    .quote-box td { padding: 8px; border-bottom: 1px solid #334155; font-size: 0.9rem; color: #CBD5E1; }

    [data-testid="stForm"] { border: none !important; padding: 0 !important; }
    
    a.mailto-btn {
        display: inline-block; background-color: #10B981; color: #FFFFFF !important; text-decoration: none !important;
        padding: 10px 18px; border-radius: 8px; font-weight: 600; letter-spacing: 0.5px; font-size: 0.85rem; margin: 6px 0 12px 0;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    a.mailto-btn:hover { background-color: #059669; }

    # Feature Cards
    .feature-card {
        background-color: #1E293B; border: 1px solid #334155; border-left: 4px solid #10B981;
        padding: 18px; border-radius: 10px; margin-bottom: 14px; min-height: 130px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .feature-card h4 { color: #F8FAFC; margin: 0 0 6px 0; font-size: 1rem; font-weight: 600; }
    .feature-card p { color: #94A3B8; margin: 0; font-size: 0.88rem; line-height: 1.5; }

    .footer { text-align: center; margin-top: 40px; padding-top: 15px; border-top: 1px solid #334155; }
    .footer h4 { color: #F8FAFC; margin: 0; font-size: 0.9rem; letter-spacing: 1px; font-weight: 600;}
    .footer p { color: #94A3B8; font-size: 0.7rem; letter-spacing: 1px; margin-top: 4px;}
</style>
""", unsafe_allow_html=True)

db.init_db()

# SESSION STATE
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "user_data" not in st.session_state: st.session_state.user_data = {"name": "", "farm": "", "location": "", "email": ""}
if "messages" not in st.session_state: st.session_state.messages = []
if "basket" not in st.session_state: st.session_state.basket = {}
if "last_document" not in st.session_state: st.session_state.last_document = None


# HELPERS
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
    if val:
        return val
    try:
        return st.secrets[name]
    except Exception:
        return default


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


@st.cache_data(show_spinner=False, ttl=86400)
def geocode_location(query: str):
    if not query or not query.strip():
        return None
    headers = {"User-Agent": "seed2harvest-streamlit-app/1.0"}
    for q in (query, f"{query}, South Africa"):
        try:
            r = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": q, "format": "json", "limit": 1},
                headers=headers, timeout=8
            )
            data = r.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", q)
        except Exception:
            continue
    return None


def make_qr_png(data: str, box_size=5) -> bytes:
    qr = qrcode.QRCode(version=None, box_size=box_size, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def load_banner_html(path="images/maxresdefault.jpg"):
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = path.rsplit(".", 1)[-1].lower()
        mime = "image/png" if ext == "png" else "image/jpeg"
        return f"<img class='hero-banner' src='data:{mime};base64,{b64}'/>"
    except Exception:
        return "<div class='hero-placeholder'></div>"


# GROQ CLIENT SETUP
GROQ_API_KEY = get_secret("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

catalog_data = db.fetch_inventory()
price_map = {row[0]: row[3] for row in catalog_data}
catalog_context = "\n".join([
    f"- Product: {row[0]} | Category: {row[1]} | Stock: {row[2]} units | Price: R{row[3]:.2f} | Safe Usage: {row[4]}"
    for row in catalog_data
])


def basket_totals():
    subtotal = sum(price_map.get(p, 0.0) * q for p, q in st.session_state.basket.items() if q > 0)
    vat = subtotal * 0.15
    return subtotal, vat, subtotal + vat


def basket_context() -> str:
    items = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
    if not items:
        return "The client's basket is currently EMPTY."
    lines = [f"- {q}x {p} @ R{price_map.get(p, 0.0):.2f} = R{price_map.get(p, 0.0) * q:.2f}" for p, q in items]
    subtotal, vat, total = basket_totals()
    lines.append(f"Subtotal: R{subtotal:.2f} | VAT (15%): R{vat:.2f} | Total: R{total:.2f}")
    return "\n".join(lines)


def set_basket_qty(product_name):
    qty = st.session_state.get(f"cat_{product_name}", 0)
    if qty and qty > 0:
        st.session_state.basket[product_name] = int(qty)
    else:
        st.session_state.basket.pop(product_name, None)


def clear_basket():
    st.session_state.basket = {}
    for k in [k for k in st.session_state.keys() if k.startswith("cat_")]:
        del st.session_state[k]


def payment_lines(inv_no, grand_total):
    lines = [f"Payment reference: {inv_no}", f"Amount to pay: R{grand_total:.2f}"]
    filled = [(k, v) for k, v in BENEFICIARY.items() if v]
    lines += [f"{k}: {v}" for k, v in filled]
    if len(filled) <= 1:
        lines.append("Full banking details: request from support@seed2harvest.co.za")
    return lines


def generate_and_send(doc_type, location_input, phone, email_input):
    active_items = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
    subtotal, tax_total, grand_total = basket_totals()
    now = pd.Timestamp.now()
    inv_no = f"INV-{now.strftime('%Y%m%d-%H%M%S')}"
    date_str = now.strftime('%Y-%m-%d')

    e = html.escape
    rows_html = "".join(
        f"<tr><td>{e(p)}</td><td>{q}</td><td>R{price_map.get(p, 0.0):.2f}</td><td>R{price_map.get(p, 0.0) * q:.2f}</td></tr>"
        for p, q in active_items
    )
    rows_text = "\n".join(
        f"  {q}x {p} @ R{price_map.get(p, 0.0):.2f} = R{price_map.get(p, 0.0) * q:.2f}" for p, q in active_items
    )

    bank_qrs = []
    pay_list = payment_lines(inv_no, grand_total)
    pay_html = "<br>".join(html.escape(l) for l in pay_list)
    if doc_type == "Official Invoice":
        doc_html = f"""
        <div class="quote-box">
            <b>SEED 2 HARVEST (PTY) LTD — OFFICIAL TAX INVOICE</b><br>
            123 Agricultural Way, Cape Town, 8001<br>
            support@seed2harvest.co.za | +27 21 555 0192<hr>
            <b>BILLED TO:</b> {e(st.session_state.user_data['name'])} ({e(st.session_state.user_data['farm'])})<br>
            <b>DELIVERY ADDRESS:</b> {e(location_input)}<br>
            <b>CONTACT:</b> {e(phone)} | {e(email_input)}<br>
            <b>INVOICE NO:</b> {inv_no} &nbsp;|&nbsp; <b>DATE:</b> {date_str}
            <table>
                <tr><th>DESCRIPTION</th><th>QTY</th><th>UNIT PRICE</th><th>TOTAL</th></tr>
                {rows_html}
            </table>
            <b>SUBTOTAL:</b> R {subtotal:.2f}<br>
            <b>15% VAT:</b> R {tax_total:.2f}<br>
            <b>TOTAL DUE:</b> R {grand_total:.2f}
        </div>"""
    else:
        bank_qrs = [(name, url, make_qr_png(url, box_size=6)) for name, url in BANKS]
        doc_html = f"""
        <div class="quote-box">
            <b>SEED 2 HARVEST — QR CODE QUOTATION SUMMARY</b><br>
            <b>REF:</b> {inv_no} | <b>TO:</b> {e(email_input)}
            <table>
                <tr><th>DESCRIPTION</th><th>QTY</th><th>UNIT PRICE</th><th>TOTAL</th></tr>
                {rows_html}
            </table>
            <b>TOTAL (incl. 15% VAT):</b> R {grand_total:.2f}<br><br>
            <b>PAYMENT DETAILS</b><br>{pay_html}<br>
            Scan your bank's QR code below to open your bank, log in, then choose Pay / Pay beneficiary and enter the details above.
        </div>"""

    email_html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#222;">
    <p>Dear {e(st.session_state.user_data['name'])},</p>
    <p>Please find your requested <b>{e(doc_type.lower())}</b> for your order at {e(st.session_state.user_data['farm'])}.</p>
    <p><b>Reference:</b> {inv_no}<br><b>Date:</b> {date_str}<br><b>Delivery address:</b> {e(location_input)}<br><b>Contact:</b> {e(phone)}</p>
    <table style="border-collapse:collapse;width:100%;max-width:560px;" border="1" cellpadding="6">
      <tr style="background:#f0e6d8;"><th align="left">Description</th><th>Qty</th><th>Unit</th><th>Total</th></tr>
      {rows_html}
    </table>
    <p>Subtotal: R{subtotal:.2f}<br>VAT (15%): R{tax_total:.2f}<br><b>Total payable: R{grand_total:.2f}</b></p>
    <p><b>Payment details</b><br>{pay_html}</p>
    <p>Regards,<br>Seed 2 Harvest<br>support@seed2harvest.co.za</p>
    </body></html>"""

    email_text = (
        f"Dear {st.session_state.user_data['name']},\n\n"
        f"Your {doc_type.lower()} for {st.session_state.user_data['farm']}.\n"
        f"Reference: {inv_no}\nDate: {date_str}\nDelivery: {location_input}\n\n"
        f"{rows_text}\n\nSubtotal: R{subtotal:.2f}\nVAT (15%): R{tax_total:.2f}\n"
        f"Total payable: R{grand_total:.2f}\n\n"
        + "PAYMENT DETAILS\n" + "\n".join(pay_list) + "\n\nSeed 2 Harvest"
    )

    mailto_url = (
        f"mailto:{quote(email_input)}"
        f"?cc={quote('support@seed2harvest.co.za')}"
        f"&subject={quote('SEED2HARVEST ORDER INFORMATION')}"
        f"&body={quote(email_text[:1500])}"
    )

    gmail_url = (
        "https://mail.google.com/mail/?view=cm&fs=1"
        f"&to={quote(email_input)}"
        f"&cc={quote('support@seed2harvest.co.za')}"
        f"&su={quote('SEED2HARVEST ORDER INFORMATION')}"
        f"&body={quote(email_text[:1200])}"
    )

    st.session_state.last_document = {
        "doc_html": doc_html, "bank_qrs": bank_qrs, "inv_no": inv_no, "email_html": email_html,
        "to": email_input, "doc_type": doc_type, "mailto": mailto_url, "gmail": gmail_url, "email_text": email_text
    }
    return st.session_state.last_document


def render_email_status(doc):
    st.success(f"{doc['doc_type']} ready. Choose how you want to send it.")
    st.markdown(
        f"<a class='mailto-btn' href='{doc['gmail']}' target='_blank' rel='noopener noreferrer'>OPEN IN GMAIL</a> &nbsp; "
        f"<a class='mailto-btn' href='{doc['mailto']}' target='_blank' rel='noopener noreferrer'>OPEN IN OTHER EMAIL APP</a>",
        unsafe_allow_html=True
    )
    st.caption(f"Opens a ready-written email to {doc['to']} with Seed 2 Harvest support copied in. Press send to finish.")
    with st.expander("Or copy the email text yourself"):
        st.caption("To: " + doc["to"] + "  |  Cc: support@seed2harvest.co.za  |  Subject: SEED2HARVEST ORDER INFORMATION")
        st.code(doc["email_text"], language=None)


# SIDEBAR NAVIGATION & REAL-TIME BASKET
with st.sidebar:
    st.markdown("<div class='sidebar-title'>ERTG</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-subtitle'>OPERATIONS</div>", unsafe_allow_html=True)

    if st.session_state.authenticated:
        page_selection = st.radio(
            "Navigate",
            ["CHAT", "CATALOGUE", "RESERVE ORDER", "GLOBAL FEED", "FEATURES"],
            label_visibility="collapsed"
        )
    else:
        page_selection = "ONBOARDING"
        st.caption("Please authenticate to access operations.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-title'>YOUR BASKET</div>", unsafe_allow_html=True)

    active_items = [(p, q) for p, q in st.session_state.basket.items() if q > 0]
    if not active_items:
        st.write("Empty")
    else:
        for prod, qty in active_items:
            st.write(f"- {qty}x {prod}")
        _, _, _total = basket_totals()
        st.caption(f"Total incl. VAT: R{_total:.2f}")

    if st.button("CLEAR BASKET"):
        clear_basket()
        st.toast("Basket Cleared")
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("TERMINATE"):
        st.session_state.authenticated = False
        st.session_state.messages = []
        clear_basket()
        st.session_state.last_document = None
        st.rerun()

# COMPACT MAIN HEADER
st.markdown(load_banner_html(), unsafe_allow_html=True)
st.markdown("<div class='main-title'>SEED 2 HARVEST</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>ELEVATE YOUR EVERYDAY</div>", unsafe_allow_html=True)

# FEATURES CONTENT (shared)
FEATURES = [
    ("STRATEGIC AGENT", "Chat with an AI advisor grounded in our certified product catalogue. It knows your farm profile and what is in your basket, and understands Afrikaans farming slang."),
    ("LIVE CATALOGUE", "Browse products with current stock and pricing. Set quantities and your basket updates instantly in the sidebar."),
    ("SMART BASKET", "Your basket is shared across every page and the agent can see it, so you can ask for advice or a quote on exactly what you picked."),
    ("INVOICES & QUOTES", "Generate an official tax invoice (15% VAT) or a QR code quotation summary, and download it or have it emailed to you."),
    ("EMAIL YOUR DOCUMENT", "One button opens your own email app with the invoice or quotation already written and addressed, subject SEED2HARVEST ORDER INFORMATION. Seed 2 Harvest support is copied in."),
    ("FARM MAP", "The Global Feed page maps your delivery location so you can confirm where your order is going."),
    ("PORTAL QR", "Scan the QR code to open the Seed 2 Harvest portal on your phone."),
    ("POPIA COMPLIANT", "Your details are only used to run your session and process your orders, in line with POPIA."),
]


def render_features():
    cols = st.columns(2)
    for i, (title, desc) in enumerate(FEATURES):
        with cols[i % 2]:
            st.markdown(
                f"<div class='feature-card'><h4>{title}</h4><p>{desc}</p></div>",
                unsafe_allow_html=True
            )


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

            st.markdown("""
            <div class="custom-warning">
                Hello fellow farmer. For the agent to work effectively we need permission to work with your data. Click yes to continue or leave.
            </div>
            """, unsafe_allow_html=True)

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
                st.session_state.user_data = {
                    "name": client_name, "farm": client_farm, "location": client_location, "email": client_email
                }
                st.session_state.authenticated = True
                st.rerun()

elif page_selection == "CHAT":
    st.markdown("<div class='section-header'>STRATEGIC AGENT</div>", unsafe_allow_html=True)

    USER_IDENTITY_PROMPT = f"""
    You are the Seed 2 Harvest Strategic Agent.
    SMME Partner: Shaun Cairns (Cape Town, South Africa).

    CURRENT CLIENT PROFILE (Already Authenticated):
    - Name: {st.session_state.user_data['name']}
    - Farm/Company: {st.session_state.user_data['farm']}
    - Location/Address: {st.session_state.user_data['location']}
    - Email: {st.session_state.user_data['email']}

    CLIENT'S CURRENT BASKET (live, you CAN see this):
    {basket_context()}

    INSTRUCTIONS:
    1. Ground your advice in the certified product catalog:
    {catalog_context}
    2. Never ask for their name or address again. Use their profile context automatically.
    3. You can see the basket above. When the client says "from my basket" or "the basket", use those items and totals. Never ask them to re-list basket items.
    4. You cannot send emails or generate files yourself. When the client wants an invoice or a QR code quotation, confirm the basket contents and total, then tell them a button will appear below the chat to prepare the document, and that they send it from their own email app to {st.session_state.user_data['email']}. Never claim an email has already been sent.
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
        _, _, _gt = basket_totals()
        st.caption(f"Basket total incl. VAT: R{_gt:.2f}. It will be addressed to {st.session_state.user_data['email']}.")
        chat_doc_type = st.radio(
            "Document type", ["Official Invoice", "QR Code Quotation Summary"],
            horizontal=True, key="chat_doc_type"
        )
        chat_phone = st.text_input("Contact number (optional)", key="chat_phone")
        if st.button(f"PREPARE {chat_doc_type.upper()}", key="chat_send_btn"):
            with st.spinner("Preparing document..."):
                result = generate_and_send(
                    chat_doc_type,
                    st.session_state.user_data["location"],
                    chat_phone or "Not provided",
                    st.session_state.user_data["email"]
                )
            render_email_status(result)
            st.caption("The full document can also be downloaded on the RESERVE ORDER page.")

elif page_selection == "CATALOGUE":
    st.markdown("<div class='section-header'>PRODUCT CATALOGUE & REAL-TIME BASKET</div>", unsafe_allow_html=True)

    for row in catalog_data:
        p_name, p_cat, p_stock, p_price, p_guide = row[0], row[1], row[2], row[3], row[4]
        cols = st.columns([3, 1])
        with cols[0]:
            st.markdown(f"**{p_name}** ({p_cat}) — **ZAR {p_price:.2f}** | Stock: {p_stock}")
            st.caption(f"Guideline: {p_guide}")
        with cols[1]:
            key = f"cat_{p_name}"
            if key not in st.session_state:
                st.session_state[key] = int(st.session_state.basket.get(p_name, 0))
            st.number_input(
                "Qty", min_value=0, max_value=int(p_stock), step=1,
                key=key, on_change=set_basket_qty, args=(p_name,)
            )
        st.markdown("---")

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
        st.download_button(
            "DOWNLOAD DOCUMENT (HTML)",
            data=doc["email_html"].encode("utf-8"),
            file_name=f"{doc['inv_no']}.html",
            mime="text/html"
        )

elif page_selection == "GLOBAL FEED":
    st.markdown("<div class='section-header'>GLOBAL FEED, MAP EXTENSION & PORTAL QR</div>", unsafe_allow_html=True)

    col_map, col_qr = st.columns(2)

    with col_map:
        st.markdown("### INTERACTIVE FARM MAP")
        user_loc = st.session_state.user_data['location']
        st.write(f"Delivery Location: **{user_loc or 'Cape Town, South Africa'}**")

        result = geocode_location(user_loc)
        if result:
            lat, lon, resolved = result
            st.caption(f"Matched: {resolved}")
        else:
            lat, lon = -33.9249, 18.4241
            if user_loc:
                st.warning("Could not find that location, showing Cape Town instead. Try a town or suburb name.")

        st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), zoom=10)

    with col_qr:
        st.markdown("### OFFICIAL WEBSITE QR CODE")
        st.write("Scan to visit **Seed 2 Harvest** portal:")
        st.image(make_qr_png("https://seed2harvest.co.za"), width=180)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    **ACTIVE SYSTEMS ARCHITECTURE:**
    - **EA Middleware:** Python runtime translating regional vernacular & normalizing input streams.
    - **Persistence:** SQLite relational mapping (`orders`, `inventory`, `clients`).
    - **Compliance:** POPIA standards enforced on client data encapsulation.
    - **Inference Engine:** Groq LPU hardware routing to openai/gpt-oss-120b.
    """)

elif page_selection == "FEATURES":
    st.markdown("<div class='section-header'>WHAT THIS APP CAN DO</div>", unsafe_allow_html=True)
    render_features()

    st.markdown("### HOW TO PLACE AN ORDER")
    st.markdown("""
    1. Open **CATALOGUE** and set quantities. Your basket fills in the sidebar.
    2. Ask the **CHAT** agent for advice on dosage or what suits your crop.
    3. Open **RESERVE ORDER**, enter your contact number and pick Invoice or QR Quotation.
    4. Press **PROCESS TRANSACTION**. Then use the email button to send it from your own email app, or download the document.
    """)

# FOOTER
st.markdown("""
<div class='footer'>
    <h4>BUZUZI INCORPORATED</h4>
    <p>FOLLOW ON SOCIALS: @SEED2HARVEST_GLOBAL</p>
</div>
""", unsafe_allow_html=True)
