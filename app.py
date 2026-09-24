import re
import smtplib
from datetime import datetime
from email.message import EmailMessage
import pandas as pd
import streamlit as st

# ============================================================
# SETTINGS & DATA
# ============================================================

AIRPORT_NAMES = {
    "UBN": {"MN": "Улаанбаатар", "EN": "Ulaanbaatar"},
    "NRT": {"MN": "Токио", "EN": "Tokyo"},
    "HND": {"MN": "Токио", "EN": "Tokyo"},
    "FRA": {"MN": "Франкфурт", "EN": "Frankfurt"},
    "ICN": {"MN": "Сөүл", "EN": "Seoul"},
    "PEK": {"MN": "Бээжин", "EN": "Beijing"},
    "PKX": {"MN": "Бээжин", "EN": "Beijing"},
    "BKK": {"MN": "Бангкок", "EN": "Bangkok"},
    "PUS": {"MN": "Пусан", "EN": "Busan"},
    "IST": {"MN": "Истанбул", "EN": "Istanbul"},
    "SVO": {"MN": "Москва", "EN": "Moscow"},
    "HKG": {"MN": "Хонконг", "EN": "Hong Kong"},
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

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
        now = datetime.now()
        return now.strftime("%Y.%m.%d"), now.strftime("%Y-%m-%d"), now.strftime("%B %d, %Y")

    months = {
        "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
        "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
    }

    m = re.search(r"(\d{2})([A-Z]{3})(\d{2,4})?", raw_date_str.upper())
    if m:
        day = int(m.group(1))
        month_str = m.group(2)
        year_str = m.group(3) if m.group(3) else str(datetime.now().year)

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
        r"^\s*(\d{3})\s+(?:\d{2})?(.+?)\s+([A-Z0-9]{5,8})(?:\s+([A-Z]{2})\s*(\d{2}[A-Z]{3})?)?", 
        re.IGNORECASE
    )
    ticket_pattern = re.compile(r"FA\s+PAX\s+(\d{3}-\d{9,10})", re.IGNORECASE)

    raw_passengers = []
    current = None

    for line in lines:
        passenger_match = passenger_pattern.search(line)
        if passenger_match and passenger_match.group(1).isdigit():
            if current is not None:
                raw_passengers.append(current)

            pax_name_raw = passenger_match.group(2).strip()
            pnr = passenger_match.group(3).upper()
            status_code = (passenger_match.group(4) or "").upper()
            booking_date = (passenger_match.group(5) or "").upper()

            if not status_code or not booking_date:
                m_stat = re.search(r"\b([A-Z]{2})\s*(\d{2}[A-Z]{3})\b", line)
                if m_stat:
                    status_code = m_stat.group(1).upper()
                    booking_date = m_stat.group(2).upper()

            current = {
                "PNLNo": passenger_match.group(1),
                "Passenger Name": pax_name_raw,
                "PNR": pnr,
                "Status Code": status_code,
                "Booking Date": booking_date,
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

    for pax in raw_passengers:
        emails_list = list(pax["emails_dict"].keys())
        langs_list = list(pax["emails_dict"].values())

        joined_emails = ", ".join(emails_list) if emails_list else ""
        primary_lang = "MN" if "MN" in langs_list else ("EN" if "EN" in langs_list else "N/A")

        missing_reasons = []
        if pax["Status Code"] == "RR":
            missing_reasons.append("RR статус")
        if not joined_emails:
            missing_reasons.append("Имэйл хаяггүй")
        if pax["TicketNo"] == "-":
            missing_reasons.append("TKT дугааргүй")

        record = {
            "Selected": True,
            "SeqNo": str(valid_idx) if not missing_reasons else "",
            "PNLNo": pax["PNLNo"],
            "Passenger Name": pax["Passenger Name"],
            "PNR": pax["PNR"],
            "StatusCode": pax["Status Code"] or "-",
            "BookingDate": pax["Booking Date"] or "-",
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
            formatted_records.append(record)
            valid_idx += 1

    return formatted_records, missing_data_records

# ============================================================
# TEMPLATE GENERATOR
# ============================================================

def generate_email_for_passenger(record, target_lang, flight_info):
    pax_name = record.get('Passenger Name') if record else "{PAX_NAME}"
    pnr_code = record.get('PNR') if record else "{PNR}"
    tkt_no = record.get('TicketNo') if record else "{TICKET_NO}"

    flt_no = flight_info['flight'] or (record.get('Flight') if record else "OM137")
    flt_date = flight_info['date'] or (record.get('Date') if record else "08NOV30")
    raw_route = flight_info['route'] or (record.get('Route') if record else "UBN-FRA")
    dep_time = flight_info['dep_time']
    arr_time = flight_info['arr_time']
    reason = flight_info['reason']
    status_type = flight_info['status_type']

    mn_dot_date, mn_dash_date, en_date = format_date_custom(flt_date)
    city_title, full_route_display = get_route_text(raw_route, lang=target_lang)

    if target_lang == "MN":
        if status_type == "CANCEL":
            subject = f"{mn_dot_date} –ний {city_title} {flt_no} нислэг цуцлагдсан тухай мэдэгдэл"
            html_body = f"""<div style="font-family: Calibri, sans-serif; font-size: 11pt;">
Хүндэт {pax_name},<br><br>
Таны {mn_dash_date}-ны өдрийн {flt_no} дугаартай {full_route_display} чиглэлийн нислэг <b>цуцлагдсан</b> болохыг үүгээр мэдэгдэж байна.<br><br>
<b>ЗОРЧИГЧИЙН МЭДЭЭЛЭЛ:</b><br>
• Зорчигчийн нэр: {pax_name}<br>
• Захиалгын дугаар (PNR): {pnr_code}<br>
• Тийзийн дугаар: {tkt_no}<br><br>
<b>ЦУЦЛАГДСАН НИСЛЭГИЙН МЭДЭЭЛЭЛ:</b><br>
• Нислэг: {flt_no}<br>
• Огноо: {flt_date}<br>
• Чиглэл: {raw_route}"""
            if dep_time: html_body += f"<br>• Нисэх цаг: {dep_time}"
            if arr_time: html_body += f"<br>• Буух цаг: {arr_time}"
            if reason: html_body += f"<br>• Шалтгаан: {reason}"
            html_body += "<br><br>Тийз буцаалт болон өөр өдрийн нислэгээр тийзээ өөрчилж баталгаажуулах талаар тийз худалдан авсан аяллын агентлаг эсхүл тийз олгосон газартайгаа аль болох хурдан хугацаанд холбогдоно уу.<br><br>Дээрх өөрчлөлтөөс шалтгаалан Танд хүндрэл, чирэгдэл учруулж байгаад хүлцэл өчье.<br><br>Хүндэтгэсэн,<br>МИАТ ТӨХК</div>"
            
            plain_body = f"Хүндэт {pax_name},\n\nТаны {mn_dash_date}-ны өдрийн {flt_no} дугаартай {full_route_display} чиглэлийн нислэг цуцлагдсан болохыг үүгээр мэдэгдэж байна.\n\nЗОРЧИГЧИЙН МЭДЭЭЛЭЛ:\n• Зорчигчийн нэр: {pax_name}\n• Захиалгын дугаар (PNR): {pnr_code}\n• Тийзийн дугаар: {tkt_no}\n\nЦУЦЛАГДСАН НИСЛЭГИЙН МЭДЭЭЛЭЛ:\n• Нислэг: {flt_no}\n• Огноо: {flt_date}\n• Чиглэл: {raw_route}\n\nХүндэтгэсэн,\nМИАТ ТӨХК"
        else:
            subject = f"{mn_dot_date} –ний {city_title} {flt_no} нислэгийн хуваарийн өөрчлөлтийн тухай мэдэгдэл"
            html_body = f"""<div style="font-family: Calibri, sans-serif; font-size: 11pt;">
Хүндэт {pax_name},<br><br>
Таны {mn_dash_date}-ны өдрийн {flt_no} дугаартай {full_route_display} чиглэлийн нислэгийн <b>цагийн хуваарьт өөрчлөлт</b> орсон болохыг үүгээр мэдэгдэж байна.<br><br>
<b>ЗОРЧИГЧИЙН МЭДЭЭЛЭЛ:</b><br>
• Зорчигчийн нэр: {pax_name}<br>
• Захиалгын дугаар (PNR): {pnr_code}<br>
• Тийзийн дугаар: {tkt_no}<br><br>
<b>ШИНЭ НИСЛЭГИЙН МЭДЭЭЛЭЛ:</b><br>
• Нислэг: {flt_no}<br>
• Огноо: {flt_date}<br>
• Чиглэл: {raw_route}"""
            if dep_time: html_body += f"<br>• Нисэх цаг: {dep_time}"
            if arr_time: html_body += f"<br>• Буух цаг: {arr_time}"
            html_body += "<br><br>Таны тийзийн төлөв байдал болон шинэ нислэгийн мэдээллийг баталгаажуулахын тулд тийз худалдан авсан аяллын агентлаг эсхүл тийз олгосон газартайгаа аль болох хурдан хугацаанд холбогдоно уу.<br><br>Дээрх өөрчлөлтөөс шалтгаалан Танд хүндрэл, чирэгдэл учруулж байгаад хүлцэл өчье.<br><br>Хүндэтгэсэн,<br>МИАТ ТӨХК</div>"
            
            plain_body = f"Хүндэт {pax_name},\n\nТаны {mn_dash_date}-ны өдрийн {flt_no} дугаартай {full_route_display} чиглэлийн нислэгийн цагийн хуваарьт өөрчлөлт орсон болохыг үүгээр мэдэгдэж байна.\n\nЗОРЧИГЧИЙН МЭДЭЭЛЭЛ:\n• Зорчигчийн нэр: {pax_name}\n• Захиалгын дугаар (PNR): {pnr_code}\n• Тийзийн дугаар: {tkt_no}\n\nШИНЭ НИСЛЭГИЙН МЭДЭЭЛЭЛ:\n• Нислэг: {flt_no}\n• Огноо: {flt_date}\n• Чиглэл: {raw_route}\n\nХүндэтгэсэн,\nМИАТ ТӨХК"

    else: # EN
        if status_type == "CANCEL":
            subject = f"Flight Cancellation Notification - {flt_no} ({city_title}) - {en_date}"
            html_body = f"""<div style="font-family: Calibri, sans-serif; font-size: 11pt;">
Dear {pax_name},<br><br>
We regret to inform you that your flight {flt_no} {full_route_display}, scheduled for {en_date}, has been <b>cancelled</b>.<br><br>
<b>PASSENGER DETAILS:</b><br>
- Passenger Name: {pax_name}<br>
- Booking Reference (PNR): {pnr_code}<br>
- Ticket Number: {tkt_no}<br><br>
<b>CANCELLED FLIGHT DETAILS:</b><br>
- Flight: {flt_no}<br>
- Date: {flt_date}<br>
- Route: {raw_route}"""
            if dep_time: html_body += f"<br>- Departure Time: {dep_time}"
            if arr_time: html_body += f"<br>- Arrival Time: {arr_time}"
            if reason: html_body += f"<br>- Reason: {reason}"
            html_body += "<br><br>For ticket refund or to change and confirm your ticket for a flight on another date, please contact your travel agent or ticket issuing office as soon as possible.<br><br>Best regards,<br>MIAT Mongolian Airlines</div>"
            
            plain_body = f"Dear {pax_name},\n\nWe regret to inform you that your flight {flt_no} {full_route_display}, scheduled for {en_date}, has been cancelled.\n\nPASSENGER DETAILS:\n- Passenger Name: {pax_name}\n- Booking Reference (PNR): {pnr_code}\n- Ticket Number: {tkt_no}\n\nBest regards,\nMIAT Mongolian Airlines"
        else:
            subject = f"Flight Schedule Change Notification - {flt_no} ({city_title}) – {en_date}"
            html_body = f"""<div style="font-family: Calibri, sans-serif; font-size: 11pt;">
Dear {pax_name},<br><br>
We regret to inform you of a <b>schedule change</b> for your flight {flt_no} {full_route_display} on {en_date}.<br><br>
<b>PASSENGER DETAILS:</b><br>
- Passenger Name: {pax_name}<br>
- Booking Reference (PNR): {pnr_code}<br>
- Ticket Number: {tkt_no}<br><br>
<b>NEW FLIGHT SCHEDULE DETAILS:</b><br>
- Flight: {flt_no}<br>
- Date: {flt_date}<br>
- Route: {raw_route}"""
            if dep_time: html_body += f"<br>- Departure Time: {dep_time}"
            if arr_time: html_body += f"<br>- Arrival Time: {arr_time}"
            html_body += "<br><br>Please contact your travel agent or issuing office as soon as possible to confirm your flight details.<br><br>Best regards,<br>MIAT Mongolian Airlines</div>"
            
            plain_body = f"Dear {pax_name},\n\nWe regret to inform you of a schedule change for your flight {flt_no} {full_route_display} on {en_date}.\n\nPASSENGER DETAILS:\n- Passenger Name: {pax_name}\n- Booking Reference (PNR): {pnr_code}\n- Ticket Number: {tkt_no}\n\nBest regards,\nMIAT Mongolian Airlines"

    return subject, plain_body, html_body

def render_custom_template(template_html, record):
    pax_name = record.get('Passenger Name', '') if record else "{PAX_NAME}"
    pnr_code = record.get('PNR', '') if record else "{PNR}"
    tkt_no = record.get('TicketNo', '') if record else "{TICKET_NO}"

    rendered = template_html.replace("{PAX_NAME}", pax_name)
    rendered = rendered.replace("{PNR}", pnr_code)
    rendered = rendered.replace("{TICKET_NO}", tkt_no)
    return rendered

# ============================================================
# SMTP SENDER
# ============================================================

def send_email_smtp(sender_email, app_password, recipient_email, subject, plain_text, html_text):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg.set_content(plain_text)
    msg.add_alternative(html_text, subtype='html')

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)

# ============================================================
# STREAMLIT UI
# ============================================================

st.set_page_config(page_title="MIAT Flight Notification System", layout="wide")
st.title("✈️ MIAT Flight Notification System (Web)")

if "records" not in st.session_state:
    st.session_state.records = []
if "missing_records" not in st.session_state:
    st.session_state.missing_records = []
if "pnl_text" not in st.session_state:
    st.session_state.pnl_text = ""
if "custom_templates" not in st.session_state:
    st.session_state.custom_templates = {"MN": {"subject": "", "html": ""}, "EN": {"subject": "", "html": ""}}
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# --- SIDEBAR: AUTHENTICATION ---
with st.sidebar:
    st.header("🔑 Илгээгчийн Тохиргоо")
    st.info("Таны нууц үг системд хадгалагдахгүй бөгөөд зөвхөн одоогийн сесс дээр ашиглагдана.")
    sender_email = st.text_input("Gmail Хаяг", placeholder="example@gmail.com")
    app_password = st.text_input("Gmail App Password", type="password", help="Google Account -> Security -> App Passwords хэсгээс үүсгэнэ.")

# --- MAIN LAYOUT ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Amadeus Passenger Name List (PNL)")
    pnl_input = st.text_area("PNL Эх текст хуулах:", value=st.session_state.pnl_text, height=250, key="pnl_textarea")
    st.session_state.pnl_text = pnl_input

    col_btn1, col_btn2 = st.columns([1, 1])
    if col_btn1.button("Extract PNL", type="primary"):
        if pnl_input.strip():
            st.session_state.records, st.session_state.missing_records = parse_pnl(pnl_input)
            st.success("PNL амжилттай уншигдлаа!")
        else:
            st.warning("PNL текстээ оруулна уу.")
            
    if col_btn2.button("Clear All"):
        st.session_state.records = []
        st.session_state.missing_records = []
        st.session_state.pnl_text = ""
        st.session_state.custom_templates = {"MN": {"subject": "", "html": ""}, "EN": {"subject": "", "html": ""}}
        st.session_state.edit_mode = False
        st.rerun()

with col2:
    st.subheader("2. Нислэгийн Мэдээлэл")
    
    first_pax = st.session_state.records[0] if st.session_state.records else {}
    
    status_type = st.radio("Мэдэгдлийн төрөл:", ["CHANGE", "CANCEL"], format_func=lambda x: "Schedule Change (Өөрчлөгдсөн)" if x == "CHANGE" else "Flight Cancelled (Цуцлагдсан)", horizontal=True)
    
    c1, c2, c3 = st.columns(3)
    flt_no = c1.text_input("Flight No:", value=first_pax.get("Flight", ""))
    flt_date = c2.text_input("Date:", value=first_pax.get("Date", ""))
    route = c3.text_input("Route:", value=first_pax.get("Route", ""))
    
    c4, c5 = st.columns(2)
    dep_time = c4.text_input("Dep Time:", placeholder="10:00")
    arr_time = c5.text_input("Arr Time:", placeholder="14:30")
    
    reason = ""
    if status_type == "CANCEL":
        reason = st.text_input("Reason (Шалтгаан):", placeholder="Техникийн саатал...")

    na_action = st.radio("N/A Хэлтэй зорчигчийг авах хэл:", ["MN", "EN", "SKIP"], horizontal=True)

flight_info = {
    "flight": flt_no,
    "date": flt_date,
    "route": route,
    "dep_time": dep_time,
    "arr_time": arr_time,
    "reason": reason,
    "status_type": status_type
}

st.divider()

# --- PASSENGER TABLES & PREVIEW ---
tab1, tab2, tab3 = st.tabs(["📋 Идэвхтэй Зорчигчид", "⚠️ Мэдээлэл Дутуу Зорчигчид", "👁️ Email Preview"])

with tab1:
    if st.session_state.records:
        df_valid = pd.DataFrame(st.session_state.records)
        cols_to_show = ["Selected", "SeqNo", "PNLNo", "Passenger Name", "PNR", "StatusCode", "BookingDate", "TicketNo", "Email", "Language", "SendStatus"]
        
        edited_df = st.data_editor(
            df_valid[cols_to_show],
            column_config={
                "Selected": st.column_config.CheckboxColumn("Сонгох", default=True)
            },
            disabled=["SeqNo", "PNLNo", "Passenger Name", "PNR", "StatusCode", "BookingDate", "TicketNo", "Email", "Language", "SendStatus"],
            hide_index=True,
            use_container_width=True
        )
        
        # DataFrame-ийн сонгогдсон төлвийг session_state руу шууд синк хийх
        for idx, row in edited_df.iterrows():
            st.session_state.records[idx]["Selected"] = row["Selected"]

        mn_cnt = sum(1 for r in st.session_state.records if r["Language"] == "MN" and r["Selected"])
        en_cnt = sum(1 for r in st.session_state.records if r["Language"] == "EN" and r["Selected"])
        na_cnt = sum(1 for r in st.session_state.records if r["Language"] == "N/A" and r["Selected"])
        
        st.write(f"**Сонгогдсон МЭДЭЭЛЭЛ:** 🔵 MN: {mn_cnt} | 🟢 EN: {en_cnt} | 🔴 N/A: {na_cnt}")
    else:
        st.info("Одоогоор уншигдсан зорчигч байхгүй байна.")

with tab2:
    if st.session_state.missing_records:
        df_missing = pd.DataFrame(st.session_state.missing_records)
        cols_missing = ["SeqNo", "PNLNo", "Passenger Name", "PNR", "StatusCode", "BookingDate", "TicketNo", "Email", "MissingReason"]
        st.dataframe(df_missing[cols_missing], hide_index=True, use_container_width=True)
    else:
        st.info("Дутуу мэдээлэлтэй зорчигч байхгүй байна.")

with tab3:
    col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
    with col_p1:
        preview_lang = st.radio("Preview Хэл:", ["MN", "EN"], horizontal=True)
    with col_p2:
        st.write("")
        if st.button("✏️ Засах" if not st.session_state.edit_mode else "👁️ Харж шалгах"):
            st.session_state.edit_mode = not st.session_state.edit_mode
            st.rerun()
    with col_p3:
        st.write("")
        if st.session_state.custom_templates[preview_lang]["html"]:
            if st.button("🔄 Анхны хэвэнд нь оруулах"):
                st.session_state.custom_templates[preview_lang] = {"subject": "", "html": ""}
                st.session_state.edit_mode = False
                st.rerun()

    sample_rec = st.session_state.records[0] if st.session_state.records else None
    orig_subj, orig_plain, orig_html = generate_email_for_passenger(sample_rec, preview_lang, flight_info)

    curr_subj = st.session_state.custom_templates[preview_lang]["subject"] or orig_subj
    curr_html = st.session_state.custom_templates[preview_lang]["html"] or orig_html

    lbl_title = "ГАРЧИГ:" if preview_lang == "MN" else "SUBJECT:"

    if st.session_state.edit_mode:
        st.info("💡 Текст доторх `{PAX_NAME}`, `{PNR}`, `{TICKET_NO}` түлхүүр үгс нь зорчигч бүрийн мэдээллээр автоматаар солигдох болно.")
        new_subj = st.text_input(f"{lbl_title}", value=curr_subj)
        new_html = st.text_area("HTML Template Эх текст:", value=curr_html, height=300)
        
        st.session_state.custom_templates[preview_lang]["subject"] = new_subj
        st.session_state.custom_templates[preview_lang]["html"] = new_html
    else:
        st.markdown(f"**{lbl_title}** {curr_subj}")
        rendered_preview = render_custom_template(curr_html, sample_rec) if st.session_state.custom_templates[preview_lang]["html"] else curr_html
        st.components.v1.html(rendered_preview, height=350, scrolling=True)

st.divider()

# --- DIALOG / MODAL FOR CONFIRMATION ---
@st.dialog("Имэйл текстийг шалгах ба Баталгаажуулах", width="large")
def confirm_and_send_dialog():
    st.warning("⚠️ Дараах имэйлийн эх текст зорчигчид руу илгээгдэх гэж байна. Шалгаад 'Илгээх' эсвэл 'Засах' товчийг сонгоно уу.")
    
    tab_mn, tab_en = st.tabs(["🇲🇳 Монгол (MN)", "🇬🇧 Англи (EN)"])
    sample_rec = st.session_state.records[0] if st.session_state.records else None
    
    with tab_mn:
        orig_subj, _, orig_html = generate_email_for_passenger(sample_rec, "MN", flight_info)
        s_subj = st.session_state.custom_templates["MN"]["subject"] or orig_subj
        s_html = st.session_state.custom_templates["MN"]["html"] or orig_html
        st.markdown(f"**ГАРЧИГ:** {s_subj}")
        st.components.v1.html(render_custom_template(s_html, sample_rec), height=250, scrolling=True)
        
    with tab_en:
        orig_subj_en, _, orig_html_en = generate_email_for_passenger(sample_rec, "EN", flight_info)
        s_subj_en = st.session_state.custom_templates["EN"]["subject"] or orig_subj_en
        s_html_en = st.session_state.custom_templates["EN"]["html"] or orig_html_en
        st.markdown(f"**SUBJECT:** {s_subj_en}")
        st.components.v1.html(render_custom_template(s_html_en, sample_rec), height=250, scrolling=True)
        
    col_d1, col_d2 = st.columns([1, 1])
    if col_d1.button("✅ Зөв, одоо илгээх", type="primary", use_container_width=True):
        st.session_state.start_send_process = True
        st.rerun()
        
    if col_d2.button("✏️ Засах шаардлагатай", use_container_width=True):
        st.rerun()

# --- ACTIONS: SEND & EXPORT ---
col_act1, col_act2 = st.columns([2, 1])

with col_act1:
    if st.button("🚀 СОНГОСОН ЗОРЧИГЧИДОД ИМЭЙЛ ИЛГЭЭХ", type="primary", use_container_width=True):
        if not sender_email or not app_password:
            st.error("Систем нэвтрэх Gmail хаяг болон App Password оруулаагүй байна!")
        elif not st.session_state.records:
            st.warning("Илгээх зорчигч байхгүй байна.")
        else:
            confirm_and_send_dialog()

    if st.session_state.get("start_send_process", False):
        st.session_state.start_send_process = False
        selected_pax = [r for r in st.session_state.records if r.get("Selected", True)]
        success_count, fail_count = 0, 0
        
        progress_bar = st.progress(0)
        
        for i, pax in enumerate(selected_pax):
            lang = pax["Language"]
            if lang == "N/A":
                if na_action == "SKIP":
                    pax["SendStatus"] = "Skipped (N/A)"
                    continue
                lang = na_action

            for recipient in pax.get("EmailList", []):
                try:
                    orig_subj, orig_plain, orig_html = generate_email_for_passenger(pax, lang, flight_info)
                    
                    cust_subj = st.session_state.custom_templates[lang]["subject"]
                    cust_html = st.session_state.custom_templates[lang]["html"]
                    
                    final_subj = cust_subj if cust_subj else orig_subj
                    final_html = render_custom_template(cust_html, pax) if cust_html else orig_html
                    final_plain = orig_plain

                    send_email_smtp(sender_email, app_password, recipient, final_subj, final_plain, final_html)
                    pax["SendStatus"] = "Sent Successfully"
                    pax["SentTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    success_count += 1
                except Exception as e:
                    pax["SendStatus"] = f"Failed: {str(e)}"
                    fail_count += 1
            
            progress_bar.progress((i + 1) / len(selected_pax))

        st.success(f"Ажиллагаа дууслаа! Нийт амжилттай: {success_count}, Амжилтгүй: {fail_count}")
        st.rerun()

with col_act2:
    all_data = st.session_state.records + st.session_state.missing_records
    if all_data:
        df_export = pd.DataFrame(all_data)
        
        # Selected, SeqNo, EmailList багануудыг экспортлохоос хасах
        cols_to_drop = ["Selected", "SeqNo", "EmailList"]
        df_export_cleaned = df_export.drop(columns=[c for c in cols_to_drop if c in df_export.columns])
        
        csv_data = df_export_cleaned.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 EXCEL тайлан татах",
            data=csv_data,
            file_name=f"PNL_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
