import re
import smtplib
from datetime import datetime
from zoneinfo import ZoneInfo
from email.message import EmailMessage
import pandas as pd
import streamlit as st

# ============================================================
# 1. СИСТЕМД НЭВТРЭХ ХЭРЭГЛЭГЧИД & ИМЭЙЛ ТОХИРГОО
# ============================================================

# Программд нэвтрэх хэрэглэгчдийн эрх (Хэрэглэгч бүрт нууц үг үүсгэх)
USERS = {
    "agent1": "miat2026",
    "agent2": "pass1234",
    "admin": "admin8888"
}

# Системээс имэйл илгээхэд ашиглах бэлэн тохируулсан хаягууд
# (Та энд өөрийн ашиглах хаяг болон нууц үг/App Password-ыг тохируулна)
SENDER_ACCOUNTS = {
    "MIAT Main Service (Gmail/SMTP)": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 465,
        "is_ssl": True,
        "email": "your_company_email@gmail.com",      # Илгээгч имэйл
        "password": "xxxx xxxx xxxx xxxx"              # Түүний App Password
    },
    "MIAT Notification Backup": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 465,
        "is_ssl": True,
        "email": "backup_email@gmail.com",
        "password": "yyyy yyyy yyyy yyyy"
    }
}

# ============================================================
# AIRPORT DATA & HELPER FUNCTIONS
# ============================================================

AIRPORT_NAMES = {
    "UBN": {"MN": "Улаанбаатар", "EN": "Ulaanbaatar"},
    "ICN": {"MN": "Сөүл (Инчон)", "EN": "Seoul (Incheon)"},
    "NRT": {"MN": "Токио (Нарита)", "EN": "Tokyo (Narita)"},
    "PEK": {"MN": "Бээжин (Капитал)", "EN": "Beijing (Capital)"},
    "FRA": {"MN": "Франкфурт", "EN": "Frankfurt"},
    "IST": {"MN": "Истанбул", "EN": "Istanbul"},

    # Бусад бүх нисэх буудлуудыг өмнөх кодын дагуу энд оруулна...
}

def get_ubn_now():
    return datetime.now(ZoneInfo("Asia/Ulaanbaatar")).strftime("%Y-%m-%d %H:%M:%S")

def get_route_text(route_str, lang="MN"):
    if not route_str or "-" not in route_str:
        return route_str, route_str

    parts = route_str.strip().upper().split("-")
    if len(parts) == 2:
        dep_code, arr_code = parts[0], parts[1]
        dep_name = AIRPORT_NAMES.get(dep_code, {}).get(lang, dep_code)
        arr_name = AIRPORT_NAMES.get(arr_code, {}).get(lang, arr_code)

        city_title = f"{dep_name} – {arr_name}"
        full_route = f"{dep_name} ({dep_code}) – {arr_name} ({arr_code})"
        return city_title, full_route

    return route_str, route_str

def format_date_custom(raw_date_str):
    if not raw_date_str:
        return "", "", ""

    months = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
    }

    m = re.search(r"(\d{2})([A-Z]{3})(\d{2,4})?", raw_date_str.upper())
    if m:
        day = int(m.group(1))
        month_str = m.group(2)
        year_str = m.group(3) if m.group(3) else str(datetime.now(ZoneInfo("Asia/Ulaanbaatar")).year)

        if len(year_str) == 2:
            year_str = "20" + year_str

        year = int(year_str)
        month = months.get(month_str, 1)

        dt = datetime(year, month, day)
        mn_dot_date = dt.strftime("%Y.%m.%d")
        mn_dash_date = dt.strftime("%Y-%m-%d")
        en_date = dt.strftime("%B %d, %Y")

        return mn_dot_date, mn_dash_date, en_date

    return raw_date_str, raw_date_str, raw_date_str

def clean_and_decode_email(raw_str):
    raw_str = raw_str.strip()
    lang = "N/A"
    
    upper_str = raw_str.upper()
    if "/EN" in upper_str or "-EN" in upper_str:
        lang = "EN"
        raw_str = re.sub(r'[/_ \-]EN$', '', raw_str, flags=re.IGNORECASE)
    elif "/MN" in upper_str or "-MN" in upper_str:
        lang = "MN"
        raw_str = re.sub(r'[/_ \-]MN$', '', raw_str, flags=re.IGNORECASE)

    if "E+" in raw_str.upper():
        parts = re.split(r'E\+', raw_str, flags=re.IGNORECASE)
        if len(parts) > 1:
            raw_str = parts[1]

    email = raw_str.replace("//", "@").replace("..", "_").replace("./", "-")
    email = re.sub(r'^[^\w\.\-\+]+', '', email)
    email = re.sub(r'[^\w\.\-\+]+$', '', email)
    email = email.strip().lower()

    return email, lang

def is_valid_email(email):
    if not email or "@" not in email or " " in email:
        return False
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_regex, email))

# ============================================================
# PARSE AMADEUS PNL
# ============================================================

def parse_pnl(text):
    lines = text.splitlines()
    flight_number, flight_date, route = "", "", ""

    header_pattern = re.compile(
        r"LP[A-Z0-9/\*]*S\(CTCE\)/([A-Z0-9]+)(?:/(\d{2}[A-Z]{3}\d{2}))?", re.IGNORECASE
    )
    route_pattern = re.compile(r"^\s*([A-Z]{3})([A-Z]{3})\s*$")

    for line in lines:
        header_match = header_pattern.search(line)
        if header_match:
            flight_number = header_match.group(1).upper()
            flight_date = (header_match.group(2) or "").upper()

        route_match = route_pattern.match(line)
        if route_match:
            route = f"{route_match.group(1).upper()}-{route_match.group(2).upper()}"

    passenger_pattern = re.compile(
        r"^\s*(\d{1,3})[A-Z]?\s+(?:\*\d{1,2}|\d{1,2})?\s*(.+?)\s+([A-Z0-9]{5,8})(?:\s+([A-Z]))?\s+([A-Z]{2})\s+(\d{2}[A-Z]{3})\s*([A-Z0-9]+)?",
        re.IGNORECASE
    )
    ticket_pattern = re.compile(r"FA\s+PAX\s+(\d{3}-\d{9,10})", re.IGNORECASE)

    raw_passengers = []
    current = None

    for line in lines:
        passenger_match = passenger_pattern.search(line)
        if passenger_match:
            if current is not None:
                raw_passengers.append(current)

            pnl_no = passenger_match.group(1)
            pax_name_raw = passenger_match.group(2).strip()
            pax_name_cleaned = re.sub(r"^\s*\*?\d{1,2}\s*", "", pax_name_raw)

            pnr = passenger_match.group(3).upper()
            booking_class = (passenger_match.group(4) or "-").upper()
            status_code = (passenger_match.group(5) or "-").upper()
            booking_date = (passenger_match.group(6) or "-").upper()
            office_code = (passenger_match.group(7) or "-").upper()

            current = {
                "PNLNo": pnl_no,
                "Passenger Name": pax_name_cleaned,
                "PNR": pnr,
                "Class": booking_class,
                "Status Code": status_code,
                "Booking Date": booking_date,
                "OfficeCode": office_code,
                "TicketNo": "-",
                "emails_dict": {},
                "Flight": flight_number,
                "Date": flight_date,
                "Route": route
            }
            continue

        if current is not None:
            line_str = line.strip()
            tkt_match = ticket_pattern.search(line_str)
            if tkt_match:
                current["TicketNo"] = tkt_match.group(1)

            tokens = line_str.split()
            for token in tokens:
                if "//" in token or "@" in token or "E+" in token.upper():
                    email, lang = clean_and_decode_email(token)
                    if is_valid_email(email):
                        if email not in current["emails_dict"] or current["emails_dict"][email] == "N/A":
                            current["emails_dict"][email] = lang

    if current is not None:
        raw_passengers.append(current)

    formatted_records, missing_data_records = [], []
    valid_idx, missing_idx = 1, 1

    valid_statuses = ["HK", "TK", "SA", "RR", "UN"]

    for pax in raw_passengers:
        emails_list = list(pax["emails_dict"].keys())
        langs_list = list(pax["emails_dict"].values())

        joined_emails = ", ".join(emails_list) if emails_list else ""
        primary_lang = "MN" if "MN" in langs_list else ("EN" if "EN" in langs_list else "N/A")

        status = pax["Status Code"]
        missing_reasons = []

        if pax["TicketNo"] == "-":
            missing_reasons.append("ТК Т дугааргүй")

        if status == "UC":
            missing_reasons.append("Статус UC")
        elif status not in valid_statuses:
            missing_reasons.append(f"{status if status != '-' else 'Нэг ч'} статусгүй/буруу статус")
        
        if not joined_emails:
            missing_reasons.append("Имэйл хаяггүй")

        record = {
            "Selected": True,
            "SeqNo": "",
            "PNLNo": pax["PNLNo"],
            "Passenger Name": pax["Passenger Name"],
            "PNR": pax["PNR"],
            "Class": pax["Class"],
            "StatusCode": pax["Status Code"],
            "BookingDate": pax["Booking Date"],
            "OfficeCode": pax["OfficeCode"],
            "TicketNo": pax["TicketNo"],
            "Email": joined_emails if joined_emails else "ОЛДООГҮЙ",
            "EmailList": emails_list,
            "Language": primary_lang,
            "Flight": pax["Flight"],
            "Date": pax["Date"],
            "Route": pax["Route"],
            "SendStatus": "Not Processed",
            "SentTime": "-",
            "MissingReason": ", ".join(missing_reasons)
        }

        if missing_reasons:
            record["SeqNo"] = str(missing_idx)
            missing_data_records.append(record)
            missing_idx += 1
        else:
            record["SeqNo"] = str(valid_idx)
            formatted_records.append(record)
            valid_idx += 1

    return formatted_records, missing_data_records

# ============================================================
# TEMPLATE GENERATOR
# ============================================================

def generate_email_text_base(target_lang, flight_info):
    pax_name = "{PAX_NAME}"
    pnr_code = "{PNR}"
    tkt_no = "{TICKET_NO}"

    flt_no = flight_info['flight'] if flight_info['flight'] else ""
    flt_date = flight_info['date'] if flight_info['date'] else ""
    raw_route = flight_info['route'] if flight_info['route'] else ""
    dep_time = flight_info['dep_time']
    arr_time = flight_info['arr_time']
    reason = flight_info['reason']
    status_type = flight_info['status_type']

    mn_dot_date, mn_dash_date, en_date = format_date_custom(flt_date) if flt_date else ("", "", "")
    city_title, full_route_display = get_route_text(raw_route, lang=target_lang) if raw_route else ("", "")

    if target_lang == "MN":
        if status_type == "CANCEL":
            subject = f"{mn_dot_date} –ний {city_title} {flt_no} нислэг цуцлагдсан тухай мэдэгдэл".strip()
            body = f"Хүндэт {pax_name},\n\nТаны {mn_dash_date}-ны өдрийн {flt_no} дугаартай {full_route_display} чиглэлийн нислэг цуцлагдсан болохыг үүгээр мэдэгдэж байна.\n\nЗОРЧИГЧИЙН МЭДЭЭЛЭЛ:\n• Зорчигчийн нэр: {pax_name}\n• Захиалгын дугаар (PNR): {pnr_code}\n• Тийзийн дугаар: {tkt_no}\n\nЦУЦЛАГДСАН НИСЛЭГИЙН МЭДЭЭЛЭЛ:\n• Нислэг: {flt_no}\n• Огноо: {flt_date}\n• Чиглэл: {raw_route}"
            if dep_time: body += f"\n• Нисэх цаг: {dep_time}"
            if arr_time: body += f"\n• Буух цаг: {arr_time}"
            if reason: body += f"\n• Шалтгаан: {reason}"
            body += "\n\nТийз буцаалт болон өөр өдрийн нислэгээр тийзээ өөрчилж баталгаажуулах талаар тийз худалдан авсан аяллын агентлаг эсхүл тийз олгосон газартайгаа аль болох хурдан хугацаанд холбогдоно уу.\n\nДээрх өөрчлөлтөөс шалтгаалан Танд хүндрэл, чирэгдэл учруулж байгаад хүлцэл өчье.\n\nХүндэтгэсэн,\nМИАТ ТӨХК"
        else:
            subject = f"{mn_dot_date} –ний {city_title} {flt_no} нислэгийн хуваарийн өөрчлөлтийн тухай мэдэгдэл".strip()
            body = f"Хүндэт {pax_name},\n\nТаны {mn_dash_date}-ны өдрийн {flt_no} дугаартай {full_route_display} чиглэлийн нислэгийн цагийн хуваарьт өөрчлөлт орсон болохыг үүгээр мэдэгдэж байна.\n\nЗОРЧИГЧИЙН МЭДЭЭЛЭЛ:\n• Зорчигчийн нэр: {pax_name}\n• Захиалгын дугаар (PNR): {pnr_code}\n• Тийзийн дугаар: {tkt_no}\n\nШИНЭ НИСЛЭГИЙН МЭДЭЭЛЭЛ:\n• Нислэг: {flt_no}\n• Огноо: {flt_date}\n• Чиглэл: {raw_route}"
            if dep_time: body += f"\n• Нисэх цаг: {dep_time}"
            if arr_time: body += f"\n• Буух цаг: {arr_time}"
            body += "\n\nТаны тийзийн төлөв байдал болон шинэ нислэгийн мэдээллийг баталгаажуулахын тулд тийз худалдан авсан аяллын агентлаг эсхүл тийз олгосон газартайгаа аль болох хурдан хугацаанд холбогдоно уу.\n\nДээрх өөрчлөлтөөс шалтгаалан Танд хүндрэл, чирэгдэл учруулж байгаад хүлцэл өчье.\n\nХүндэтгэсэн,\nМИАТ ТӨХК"
    else: # EN
        if status_type == "CANCEL":
            subject = f"Flight Cancellation Notification - {flt_no} ({city_title}) - {en_date}".strip()
            body = f"Dear {pax_name},\n\nWe regret to inform you that your flight {flt_no} {full_route_display}, scheduled for {en_date}, has been cancelled.\n\nPASSENGER DETAILS:\n- Passenger Name: {pax_name}\n- Booking Reference (PNR): {pnr_code}\n- Ticket Number: {tkt_no}\n\nCANCELLED FLIGHT DETAILS:\n- Flight: {flt_no}\n- Date: {flt_date}\n- Route: {raw_route}"
            if dep_time: body += f"\n- Departure Time: {dep_time}"
            if arr_time: body += f"\n- Arrival Time: {arr_time}"
            if reason: body += f"\n- Reason: {reason}"
            body += "\n\nFor ticket refund or to change and confirm your ticket for a flight on another date, please contact your travel agent or ticket issuing office as soon as possible.\n\nBest regards,\nMIAT Mongolian Airlines"
        else:
            subject = f"Flight Schedule Change Notification - {flt_no} ({city_title}) – {en_date}".strip()
            body = f"Dear {pax_name},\n\nWe regret to inform you of a schedule change for your flight {flt_no} {full_route_display} on {en_date}.\n\nPASSENGER DETAILS:\n- Passenger Name: {pax_name}\n- Booking Reference (PNR): {pnr_code}\n- Ticket Number: {tkt_no}\n\nNEW FLIGHT SCHEDULE DETAILS:\n- Flight: {flt_no}\n- Date: {flt_date}\n- Route: {raw_route}"
            if dep_time: body += f"\n- Departure Time: {dep_time}"
            if arr_time: body += f"\n- Arrival Time: {arr_time}"
            body += "\n\nPlease contact your travel agent or issuing office as soon as possible to confirm your flight details.\n\nBest regards,\nMIAT Mongolian Airlines"

    return subject, body

def text_to_html(plain_text):
    formatted = plain_text.replace('\n', '<br>')
    formatted = re.sub(r'(\b[A-Z-0-9А-ЯӨҮөү\s]+:)', r'<b>\1</b>', formatted)
    return f'<div style="font-family: Calibri, sans-serif; font-size: 11pt; line-height: 1.5;">{formatted}</div>'

def render_custom_template(template_text, record):
    pax_name = record.get('Passenger Name', '{PAX_NAME}') if record else "{PAX_NAME}"
    pnr_code = record.get('PNR', '{PNR}') if record else "{PNR}"
    tkt_no = record.get('TicketNo', '{TICKET_NO}') if record else "{TICKET_NO}"

    rendered = template_text.replace("{PAX_NAME}", pax_name)
    rendered = rendered.replace("{PNR}", pnr_code)
    rendered = rendered.replace("{TICKET_NO}", tkt_no)
    return rendered

# ============================================================
# UNIVERSAL SMTP SENDER (GMAIL / GENERIC)
# ============================================================

def send_email_smtp_generic(account_config, recipient_email, subject, plain_text, html_text):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = account_config['email']
    msg['To'] = recipient_email
    msg.set_content(plain_text)
    msg.add_alternative(html_text, subtype='html')

    server_host = account_config['smtp_server']
    server_port = account_config['smtp_port']

    if account_config.get('is_ssl', False):
        with smtplib.SMTP_SSL(server_host, server_port) as server:
            server.login(account_config['email'], account_config['password'])
            server.send_message(msg)
    else:
        with smtplib.SMTP(server_host, server_port) as server:
            server.starttls()
            server.login(account_config['email'], account_config['password'])
            server.send_message(msg)

def clear_all_data():
    st.session_state.records = []
    st.session_state.missing_records = []
    st.session_state.pnl_text = ""
    st.session_state.pnl_textarea = ""
    st.session_state.custom_templates = {"MN": {"subject": "", "text": ""}, "EN": {"subject": "", "text": ""}}
    st.session_state.edit_mode = False

# ============================================================
# STREAMLIT UI & AUTHENTICATION SYSTEM
# ============================================================

st.set_page_config(page_title="MIAT Flight Notification System", layout="wide")

# Session state тохиргоо
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>✈️ MIAT Notification System - Нэвтрэх</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1, 1])
    
    with col_l2:
        with st.form("login_form"):
            username_input = st.text_input("Нэвтрэх Нэр (Username)")
            password_input = st.text_input("Нууц үг (Password)", type="password")
            submit_btn = st.form_submit_button("Нэвтрэх", use_container_width=True, type="primary")

            if submit_btn:
                if username_input in USERS and USERS[username_input] == password_input:
                    st.session_state.logged_in = True
                    st.session_state.user_name = username_input
                    st.success("Амжилттай нэвтэрлээ!")
                    st.rerun()
                else:
                    st.error("Нэвтрэх нэр эсвэл нууц үг буруу байна.")
    st.stop()

# --- MAIN APPLICATION (Нэвтэрсний дараа харагдах цонх) ---

if "records" not in st.session_state:
    st.session_state.records = []
if "missing_records" not in st.session_state:
    st.session_state.missing_records = []
if "pnl_text" not in st.session_state:
    st.session_state.pnl_text = ""
if "custom_templates" not in st.session_state:
    st.session_state.custom_templates = {"MN": {"subject": "", "text": ""}, "EN": {"subject": "", "text": ""}}
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# SIDEBAR: Хэрэглэгчийн мэдээлэл болон Илгээх Имэйл Хаяг Сонгох
with st.sidebar:
    st.write(f"👤 Нэвтэрсэн хэрэглэгч: **{st.session_state.user_name}**")
    if st.button("🚪 Системээс гарах"):
        st.session_state.logged_in = False
        st.session_state.user_name = ""
        st.rerun()

    st.divider()
    st.header("✉️ Илгээх Хаяг Сонгох")
    selected_account_name = st.selectbox(
        "Илгээх Имэйл Хаяг:",
        options=list(SENDER_ACCOUNTS.keys()),
        help="Та системд урьдчилан тохируулсан имэйл хаягуудаас сонгон илгээх боломжтой."
    )
    
    current_account_config = SENDER_ACCOUNTS[selected_account_name]
    st.info(f"Сонгосон хаяг: `{current_account_config['email']}`")

st.title("✈️ MIAT Flight Notification System")

# --- UI MAIN LAYOUT ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Amadeus Passenger Name List (PNL)")
    pnl_input = st.text_area("PNL Эх текст хуулах:", height=250, key="pnl_textarea")

    col_btn1, col_btn2 = st.columns([1, 1])
    if col_btn1.button("Extract PNL", type="primary"):
        if pnl_input.strip():
            st.session_state.pnl_text = pnl_input
            st.session_state.records, st.session_state.missing_records = parse_pnl(pnl_input)
            
            first_pax = st.session_state.records[0] if st.session_state.records else (st.session_state.missing_records[0] if st.session_state.missing_records else {})
            st.session_state.input_flt_no = first_pax.get("Flight", "")
            st.session_state.input_flt_date = first_pax.get("Date", "")
            st.session_state.input_route = first_pax.get("Route", "")
            
            st.success("PNL амжилттай уншигдлаа!")
            st.rerun()
        else:
            st.warning("PNL текстээ оруулна уу.")
            
    col_btn2.button("Clear All", on_click=clear_all_data)

with col2:
    st.subheader("2. Нислэгийн Мэдээлэл")
    status_type = st.radio("Мэдэгдлийн төрөл:", ["CHANGE", "CANCEL"], format_func=lambda x: "Schedule Change (Өөрчлөгдсөн)" if x == "CHANGE" else "Flight Cancelled (Цуцлагдсан)", horizontal=True)
    
    c1, c2, c3 = st.columns(3)
    flt_no = c1.text_input("Flight No:", value=st.session_state.get("input_flt_no", ""))
    flt_date = c2.text_input("Date:", value=st.session_state.get("input_flt_date", ""))
    route = c3.text_input("Route:", value=st.session_state.get("input_route", ""))
    
    c4, c5 = st.columns(2)
    dep_time = c4.text_input("Dep Time:", placeholder="10:00")
    arr_time = c5.text_input("Arr Time:", placeholder="14:30")
    
    reason = ""
    if status_type == "CANCEL":
        reason = st.text_input("Reason (Шалтгаан):", placeholder="Техникийн саатал...")

    na_action = st.radio("N/A Хэлтэй зорчигчийг авах хэл:", ["MN", "EN", "SKIP"], horizontal=True)

flight_info = {
    "flight": flt_no, "date": flt_date, "route": route,
    "dep_time": dep_time, "arr_time": arr_time,
    "reason": reason, "status_type": status_type
}

st.divider()

# --- TABLES & DIALOG & ACTIONS (Өмнөхтэй ижил дараалал) ---
tab1, tab2, tab3 = st.tabs(["📋 Идэвхтэй Зорчигчид", "⚠️ Мэдээлэл Дутуу Зорчигчид", "👁️ Email Preview"])

with tab1:
    if st.session_state.records:
        df_valid = pd.DataFrame(st.session_state.records)
        cols_to_show = ["Selected", "SeqNo", "PNLNo", "Passenger Name", "PNR", "Class", "StatusCode", "BookingDate", "OfficeCode", "TicketNo", "Email", "Language", "SendStatus"]
        
        edited_df = st.data_editor(
            df_valid[cols_to_show],
            column_config={"Selected": st.column_config.CheckboxColumn("Сонгох", default=True)},
            disabled=["SeqNo", "PNLNo", "Passenger Name", "PNR", "Class", "StatusCode", "BookingDate", "OfficeCode", "TicketNo", "Email", "Language", "SendStatus"],
            hide_index=True, use_container_width=True, key="passenger_editor"
        )
        for idx, row in edited_df.iterrows():
            st.session_state.records[idx]["Selected"] = row["Selected"]
    else:
        st.info("Одоогоор уншигдсан идэвхтэй зорчигч байхгүй байна.")

selected_passengers = [r for r in st.session_state.records if r.get("Selected", False)]

with tab3:
    if selected_passengers:
        preview_lang = st.radio("Preview Хэл:", ["MN", "EN"], horizontal=True)
        orig_subj, orig_text = generate_email_text_base(preview_lang, flight_info)
        rendered_plain = render_custom_template(orig_text, selected_passengers[0])
        st.components.v1.html(text_to_html(rendered_plain), height=300, scrolling=True)

# --- SEND ACTION ---
if st.button("🚀 СОНГОСОН ЗОРЧИГЧИДОД ИМЭЙЛ ИЛГЭЭХ", type="primary"):
    if not selected_passengers:
        st.warning("Нэг ч зорчигч сонгогдоогүй байна.")
    else:
        success_count, fail_count = 0, 0
        progress_bar = st.progress(0)
        
        for i, pax in enumerate(selected_passengers):
            lang = pax["Language"] if pax["Language"] != "N/A" else (na_action if na_action != "SKIP" else None)
            if not lang:
                pax["SendStatus"] = "Skipped"
                continue

            for recipient in pax.get("EmailList", []):
                try:
                    orig_subj, orig_text = generate_email_text_base(lang, flight_info)
                    final_plain = render_custom_template(orig_text, pax)
                    final_html = text_to_html(final_plain)

                    # Хэрэглэгчийн сонгосон системчилсэн хаягаас имэйл илгээнэ
                    send_email_smtp_generic(current_account_config, recipient, orig_subj, final_plain, final_html)
                    pax["SendStatus"] = "Sent Successfully"
                    pax["SentTime"] = get_ubn_now()
                    success_count += 1
                except Exception as e:
                    pax["SendStatus"] = f"Failed: {str(e)}"
                    fail_count += 1

            progress_bar.progress((i + 1) / len(selected_passengers))

        st.success(f"Ажиллагаа дууслаа! Нийт амжилттай: {success_count}, Амжилтгүй: {fail_count}")
        st.rerun()
