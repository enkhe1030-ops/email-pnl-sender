import re
import smtplib
import time
import uuid
import random
import io
import os
import json
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo  
from email.message import EmailMessage
from email.utils import formatdate, formataddr
import pandas as pd
import streamlit as st
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ============================================================
# AUTHENTICATION, CONFIG & LOGGING SYSTEM
# ============================================================

USERS_FILE = "users.json"
LOGS_FILE = "logs.csv"
CREDENTIALS_FILE = "saved_credentials.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": {
                "password_hash": hash_password("admin123"),
                "role": "admin"
            },
            "Anujin": {
                "password_hash": hash_password("Anuujin111"),
                "role": "user"
            },
            "Bayartsetseg": {
                "password_hash": hash_password("Bayartsetseg7854"),
                "role": "user"
            },
            "Baigalmaa": {
                "password_hash": hash_password("Baigalmaa"),
                "role": "user"
            },
            "Buyka": {
                "password_hash": hash_password("Buyka1234"),
                "role": "user"
            },
            "Jagana": {
                "password_hash": hash_password("Jagana333"),
                "role": "user"
            },
            "Namuun": {
                "password_hash": hash_password("Namuun999"),
                "role": "user"
            },
            "Narangarav": {
                "password_hash": hash_password("Narangarav987"),
                "role": "user"
            },
            "Nyamtsetseg": {
                "password_hash": hash_password("Nyamtsetseg2247"),
                "role": "user"
            },
            "Odsuren": {
                "password_hash": hash_password("Odsuren369"),
                "role": "user"
            },
            "otgonbileg": {
                "password_hash": hash_password("Otgonbileg4567"),
                "role": "user"
            },
            "Sunderiya": {
                "password_hash": hash_password("Sunderiya1234"),
                "role": "user"
            },
            "Selenge": {
                "password_hash": hash_password("Selenge4785"),
                "role": "user"
            },
            "Uugantsetseg": {
                "password_hash": hash_password("Uugantsetseg222"),
                "role": "user"
            },
            "Uyaraa": {
                "password_hash": hash_password("Uyaraa1265"),
                "role": "user"
            },
            "Khulan": {
                "password_hash": hash_password("Khulan6157"),
                "role": "user"
            },
            "Tsetsegmaa": {
                "password_hash": hash_password("Tsetsegmaa8541"),
                "role": "user"
            },
            "Chuluuntsetseg": {
                "password_hash": hash_password("Chuluuntsetseg976"),
                "role": "user"
            },
            "Erdnetsetseg": {
                "password_hash": hash_password("Erdnetsetseg7432"),
                "role": "user"
            },
            "Enkhtuul": {
                "password_hash": hash_password("Etu0610"),
                "role": "user"
            },
            "Jargal": {
                "password_hash": hash_password("Jargal2345"),
                "role": "user"
            },
            "Maralmaa": {
                "password_hash": hash_password("Maralmaa9711"),
                "role": "user"
            },
            "Enkhtuya": {
                "password_hash": hash_password("Enkhtuya2247"),
                "role": "user"
            },
            "Unurjargal": {
                "password_hash": hash_password("Unurjargal3346"),
                "role": "user"
            },
            "Enkhamgalan": {
                "password_hash": hash_password("Enkhamgalan7821"),
                "role": "user"
            },
            "Javzandulam": {
                "password_hash": hash_password("Javzandulam3954"),
                "role": "user"
            },
            "Enkhmaa": {
                "password_hash": hash_password("Enkhmaa3399"),
                "role": "user"
            },
            "Enkhtsetseg": {
                "password_hash": hash_password("Enkhtsetseg333999"),
                "role": "user"
            }
        }
        save_users(default_users)
        return default_users
    
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users_dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=4)

def load_smtp_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"sender_email": "no.reply.mongolian.airlines@gmail.com", "app_password": ""}
    return {"sender_email": "no.reply.mongolian.airlines@gmail.com", "app_password": ""}

def save_smtp_credentials(sender_email, app_password):
    data = {
        "sender_email": sender_email,
        "app_password": app_password
    }
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_log(username, action, flight_no="", route="", details=""):
    now_str = get_ubn_now()
    log_data = {
        "Timestamp": now_str,
        "Username": username,
        "Action": action,
        "Flight No": flight_no,
        "Route": route,
        "Details": details
    }
    df_new = pd.DataFrame([log_data])
    if not os.path.exists(LOGS_FILE):
        df_new.to_csv(LOGS_FILE, index=False, encoding="utf-8-sig")
    else:
        df_new.to_csv(LOGS_FILE, mode="a", header=False, index=False, encoding="utf-8-sig")

# ============================================================
# SETTINGS & DATA
# ============================================================

AIRPORT_NAMES = {
    "UBN": {"MN": "Улаанбаатар", "EN": "Ulaanbaatar"},
    "ULN": {"MN": "Улаанбаатар (Буянт-Ухаа)", "EN": "Ulaanbaatar (Old)"},
    "HVD": {"MN": "Ховд", "EN": "Khovd"},
    "ULG": {"MN": "Өлгий", "EN": "Olgii"},
    "UGA": {"MN": "Улаангом", "EN": "Ulaangom"},
    "UNR": {"MN": "Өндөрхаан (Чингис город)", "EN": "Undurkhaan"},
    "DLZ": {"MN": "Даланзадгад", "EN": "Dalanzadgad"},
    "LTI": {"MN": "Алтай", "EN": "Altai"},
    "MWR": {"MN": "Мөрөн", "EN": "Moron"},
    "UZZ": {"MN": "Улиастай (Донной)", "EN": "Uliastai"},
    "COQ": {"MN": "Чойбалсан", "EN": "Choibalsan"},
    "BYN": {"MN": "Баянхонгор", "EN": "Bayankhongor"},
    "EAV": {"MN": "Алтат (Оюут толгой)", "EN": "Khanbumbat / Oyu Tolgoi"},
    "THN": {"MN": "Таван толгой", "EN": "Tavan Tolgoi"},
    "TST": {"MN": "Цагаан суварга", "EN": "Tsagaan Suvarga"},
    "PST": {"MN": "Баян-Өндөр (Орхон)", "EN": "Erdenet"},
    "TXN": {"MN": "Ташаанта", "EN": "Tashaanta"},

    "ICN": {"MN": "Сөүл (Инчон)", "EN": "Seoul (Incheon)"},
    "GMP": {"MN": "Сөүл (Кимпо)", "EN": "Seoul (Gimpo)"},
    "PUS": {"MN": "Пусан", "EN": "Busan"},
    "CJU": {"MN": "Чежу", "EN": "Jeju"},
    "TAE": {"MN": "Тэгү", "EN": "Daegu"},
    "CJJ": {"MN": "Чонжу", "EN": "Cheongju"},
    "NRT": {"MN": "Токио (Нарита)", "EN": "Tokyo (Narita)"},
    "HND": {"MN": "Токио (Ханеда)", "EN": "Tokyo (Haneda)"},
    "KIX": {"MN": "Осака (Кансай)", "EN": "Osaka (Kansai)"},
    "ITM": {"MN": "Осака (Итами)", "EN": "Osaka (Itami)"},
    "NGO": {"MN": "Нагоя", "EN": "Nagoya"},
    "CTS": {"MN": "Саппоро", "EN": "Sapporo"},
    "FUK": {"MN": "Фукуока", "EN": "Fukuoka"},
    "OKA": {"MN": "Окинава", "EN": "Okinawa"},
    "PEK": {"MN": "Бээжин (Капитал)", "EN": "Beijing (Capital)"},
    "PKX": {"MN": "Бээжин (Дашин)", "EN": "Beijing (Daxing)"},
    "PVG": {"MN": "Шанхай (Пудон)", "EN": "Shanghai (Pudong)"},
    "SHA": {"MN": "Шанхай (Хунчяо)", "EN": "Shanghai (Hongqiao)"},
    "CAN": {"MN": "Гуанжоу", "EN": "Guangzhou"},
    "SZX": {"MN": "Шэньчжэнь", "EN": "Shenzhen"},
    "CTU": {"MN": "Чэнду", "EN": "Chengdu"},
    "CKG": {"MN": "Чунцин", "EN": "Chongqing"},
    "KMG": {"MN": "Куньмин", "EN": "Kunming"},
    "XIY": {"MN": "Сиань", "EN": "Xi'an"},
    "HET": {"MN": "Хөх хот", "EN": "Hohhot"},
    "DSN": {"MN": "Ордос", "EN": "Ordos"},
    "EER": {"MN": "Эрээн", "EN": "Erenhot"},
    "SYX": {"MN": "Санья (Хайнань)", "EN": "Sanya (Hainan)"},
    "HAK": {"MN": "Хайкоу (Хайнань)", "EN": "Haikou (Hainan)"},
    "HKG": {"MN": "Хонконг", "EN": "Hong Kong"},
    "MFM": {"MN": "Макао", "EN": "Macau"},
    "TPE": {"MN": "Тайбэй (Таоюань)", "EN": "Taipei (Taoyuan)"},

    "BKK": {"MN": "Бангкок (Суварнабхуми)", "EN": "Bangkok (Suvarnabhumi)"},
    "DMK": {"MN": "Бангкок (Дон Мыанг)", "EN": "Bangkok (Don Mueang)"},
    "HKT": {"MN": "Пүкэт", "EN": "Phuket"},
    "SIN": {"MN": "Сингапур (Чанги)", "EN": "Singapore (Changi)"},
    "KUL": {"MN": "Куала Лумпур", "EN": "Kuala Lumpur"},
    "SGN": {"MN": "Хо Ши Мин", "EN": "Ho Chi Minh City"},
    "HAN": {"MN": "Ханой", "EN": "Hanoi"},
    "DAD": {"MN": "Да Nang", "EN": "Da Nang"},
    "PQC": {"MN": "Фү Куок", "EN": "Phu Quoc"},
    "MNL": {"MN": "Манила", "EN": "Manila"},
    "CEB": {"MN": "Себу", "EN": "Cebu"},
    "CGK": {"MN": "Жакарта", "EN": "Jakarta"},
    "DPS": {"MN": "Бали (Денпасар)", "EN": "Bali (Denpasar)"},

    "FRA": {"MN": "Франкфурт", "EN": "Frankfurt"},
    "BER": {"MN": "Берлин", "EN": "Berlin"},
    "MUC": {"MN": "Мюнхен", "EN": "Munich"},
    "LHR": {"MN": "Лондон (Хитроу)", "EN": "London (Heathrow)"},
    "IST": {"MN": "Истанбул", "EN": "Istanbul"},
    "SVO": {"MN": "Москва (Шереметьево)", "EN": "Moscow (Sheremetyevo)"},
    "IKT": {"MN": "Иркутск", "EN": "Irkutsk"}
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

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

        if "MN" in langs_list:
            primary_lang = "MN"
        elif "EN" in langs_list:
            primary_lang = "EN"
        else:
            primary_lang = "N/A"

        status = pax["Status Code"]
        missing_reasons = []

        if pax["TicketNo"] == "-":
            missing_reasons.append("ТК Т дугааргүй")

        if status == "UC":
            missing_reasons.append("Статус UC")
        elif status not in valid_statuses:
            missing_reasons.append(f"{status if status != '-' else 'Нэг ч'} статусгүй/буруу статус")
        
        if not emails_list:
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
            "Email": ", ".join(emails_list) if emails_list else "ОЛДООГҮЙ",
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
    reason_mn = flight_info.get('reason_mn', '')
    reason_en = flight_info.get('reason_en', '')
    status_type = flight_info['status_type']

    mn_dot_date, mn_dash_date, en_date = format_date_custom(flt_date) if flt_date else ("", "", "")
    city_title, full_route_display = get_route_text(raw_route, lang=target_lang) if raw_route else ("", "")

    no_reply_footer_mn = "\n\n--------------------------------------------------\nЭнэхүү мэйл нь автоматаар илгээгдэж буй тул хариу бичих шаардлагагүй."
    no_reply_footer_en = "\n\n--------------------------------------------------\nThis is an automated message, please do not reply to this email."

    if target_lang == "MN":
        if status_type == "CANCEL":
            subject = f"{mn_dot_date} –ний {city_title} {flt_no} нислэг цуцлагдсан тухай мэдэгдэл".strip()
            body = f"Хүндэт {pax_name},\n\nТаны {mn_dash_date}-ны өдрийн {flt_no} дугаартай {full_route_display} чиглэлийн нислэг цуцлагдсан болохыг үүгээр мэдэгдэж байна.\n\nЗОРЧИГЧИЙН МЭДЭЭЛЭЛ:\n• Зорчигчийн нэр: {pax_name}\n• Захиалгын дугаар (PNR): {pnr_code}\n• Тийзийн дугаар: {tkt_no}\n\nЦУЦЛАГДСАН НИСЛЭГИЙН МЭДЭЭЛЭЛ:\n• Нислэг: {flt_no}\n• Огноо: {flt_date}\n• Чиглэл: {raw_route}"
            if dep_time: body += f"\n• Нисэх цаг: {dep_time}"
            if arr_time: body += f"\n• Буух цаг: {arr_time}"
            if reason_mn: body += f"\n• Шалтгаан: {reason_mn}"
            body += f"\n\nТийз буцаалт болон өөр өдрийн нислэгээр тийзээ өөрчилж баталгаажуулах талаар тийз худалдан авсан аяллын агентлаг эсхүл тийз олгосон газартайгаа аль болох хурдан хугацаанд холбогдоно уу.\n\nДээрх өөрчлөлтөөс шалтгаалан Танд хүндрэл, чирэгдэл учруулж байгаад хүлцэл өчье.\n\nХүндэтгэсэн,\nМИАТ ТӨХК{no_reply_footer_mn}"
        else:
            subject = f"{mn_dot_date} –ний {city_title} {flt_no} нислэгийн хуваарийн өөрчлөлтийн тухай мэдэгдэл".strip()
            body = f"Хүндэт {pax_name},\n\nТаны {mn_dash_date}-ны өдрийн {flt_no} дугаартай {full_route_display} чиглэлийн нислэгийн цагийн хуваарьт өөрчлөлт орсон болохыг үүгээр мэдэгдэж байна.\n\nЗОРЧИГЧИЙН МЭДЭЭЛЭЛ:\n• Зорчигчийн нэр: {pax_name}\n• Захиалгын дугаар (PNR): {pnr_code}\n• Тийзийн дугаар: {tkt_no}\n\nШИНЭ НИСЛЭГИЙН МЭДЭЭЛЭЛ:\n• Нислэг: {flt_no}\n• Огноо: {flt_date}\n• Чиглэл: {raw_route}"
            if dep_time: body += f"\n• Нисэх цаг: {dep_time}"
            if arr_time: body += f"\n• Буух цаг: {arr_time}"
            body += f"\n\nТаны тийзийн төлөв байдал болон шинэ нислэгийн мэдээллийг баталгаажуулахын тулд тийз худалдан авсан аяллын агентлаг эсхүл тийз олгосон газартайгаа аль болох хурдан хугацаанд холбогдоно уу.\n\nДээрх өөрчлөлтөөс шалтгаалан Танд хүндрэл, чирэгдэл учруулж байгаад хүлцэл өчье.\n\nХүндэтгэсэн,\nМИАТ ТӨХК{no_reply_footer_mn}"
    else: 
        if status_type == "CANCEL":
            subject = f"Flight Cancellation Notification - {flt_no} ({city_title}) - {en_date}".strip()
            body = f"Dear {pax_name},\n\nWe regret to inform you that your flight {flt_no} {full_route_display}, scheduled for {en_date}, has been cancelled.\n\nPASSENGER DETAILS:\n- Passenger Name: {pax_name}\n- Booking Reference (PNR): {pnr_code}\n- Ticket Number: {tkt_no}\n\nCANCELLED FLIGHT DETAILS:\n- Flight: {flt_no}\n- Date: {flt_date}\n- Route: {raw_route}"
            if dep_time: body += f"\n- Departure Time: {dep_time}"
            if arr_time: body += f"\n- Arrival Time: {arr_time}"
            if reason_en: body += f"\n- Reason: {reason_en}"
            body += f"\n\nFor ticket refund or to change and confirm your ticket for a flight on another date, please contact your travel agent or ticket issuing office as soon as possible.\n\nBest regards,\nMIAT Mongolian Airlines{no_reply_footer_en}"
        else:
            subject = f"Flight Schedule Change Notification - {flt_no} ({city_title}) – {en_date}".strip()
            body = f"Dear {pax_name},\n\nWe regret to inform you of a schedule change for your flight {flt_no} {full_route_display} on {en_date}.\n\nPASSENGER DETAILS:\n- Passenger Name: {pax_name}\n- Booking Reference (PNR): {pnr_code}\n- Ticket Number: {tkt_no}\n\nNEW FLIGHT SCHEDULE DETAILS:\n- Flight: {flt_no}\n- Date: {flt_date}\n- Route: {raw_route}"
            if dep_time: body += f"\n- Departure Time: {dep_time}"
            if arr_time: body += f"\n- Arrival Time: {arr_time}"
            body += f"\n\nPlease contact your travel agent or issuing office as soon as possible to confirm your flight details.\n\nBest regards,\nMIAT Mongolian Airlines{no_reply_footer_en}"

    return subject, body

def text_to_html(plain_text):
    formatted = plain_text.replace('\n', '<br>')
    formatted = re.sub(r'(\b[A-Z-0-9А-ЯӨҮөү\s]+:)', r'<b>\1</b>', formatted)
    
    html_wrapper = f"""
    <!DOCTYPE html>
    <html lang="mn">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial, Helvetica, sans-serif;
                font-size: 14px;
                color: #222222;
                line-height: 1.6;
                background-color: #f9f9f9;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 25px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #ffffff;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {formatted}
        </div>
    </body>
    </html>
    """
    return html_wrapper

def render_custom_template(template_text, record):
    pax_name = record.get('Passenger Name', '{PAX_NAME}') if record else "{PAX_NAME}"
    pnr_code = record.get('PNR', '{PNR}') if record else "{PNR}"
    tkt_no = record.get('TicketNo', '{TICKET_NO}') if record else "{TICKET_NO}"

    rendered = template_text.replace("{PAX_NAME}", pax_name)
    rendered = rendered.replace("{PNR}", pnr_code)
    rendered = rendered.replace("{TICKET_NO}", tkt_no)
    return rendered

# ============================================================
# HIGH DELIVERABILITY SMTP SENDER
# ============================================================

def send_email_smtp(sender_email, app_password, recipient_email, recipient_name, subject, plain_text, html_text):
    msg = EmailMessage()
    msg['Date'] = formatdate(localtime=True)
    
    unique_id = uuid.uuid4().hex
    msg['Message-ID'] = f"<{unique_id}.notification@gmail.com>"
    
    msg['From'] = formataddr(("MIAT Mongolian Airlines Notification", sender_email))
    msg['To'] = formataddr((recipient_name, recipient_email))
