import re
import smtplib
from datetime import datetime
from zoneinfo import ZoneInfo  
from email.message import EmailMessage
import pandas as pd
import streamlit as st

# ============================================================
# SETTINGS & DATA
# ============================================================

AIRPORT_NAMES = {
    # ==========================================
    # 1. МОНГОЛ УЛС (Орон нутаг & Олон улс)
    # ==========================================
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

    # ==========================================
    # 2. ЗҮҮН АЗИ (East Asia)
    # ==========================================
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

    # ==========================================
    # 3. ЗҮҮН ӨМНӨД АЗИ (Southeast Asia)
    # ==========================================
    "BKK": {"MN": "Бангкок (Суварнабхуми)", "EN": "Bangkok (Suvarnabhumi)"},
    "DMK": {"MN": "Бангкок (Дон Мыанг)", "EN": "Bangkok (Don Mueang)"},
    "HKT": {"MN": "Пүкэт", "EN": "Phuket"},
    "SIN": {"MN": "Сингапур (Чанги)", "EN": "Singapore (Changi)"},
    "KUL": {"MN": "Куала Лумпур", "EN": "Kuala Lumpur"},
    "SGN": {"MN": "Хо Ши Мин", "EN": "Ho Chi Minh City"},
    "HAN": {"MN": "Ханой", "EN": "Hanoi"},
    "DAD": {"MN": "Да Нанг", "EN": "Da Nang"},
    "PQC": {"MN": "Фү Куок", "EN": "Phu Quoc"},
    "MNL": {"MN": "Манила", "EN": "Manila"},
    "CEB": {"MN": "Себу", "EN": "Cebu"},
    "CGK": {"MN": "Жакарта", "EN": "Jakarta"},
    "DPS": {"MN": "Бали (Денпасар)", "EN": "Bali (Denpasar)"},

    # ==========================================
    # 4. ЭНЭТХЭГ & ТӨВ АЗИ (South & Central Asia)
    # ==========================================
    "DEL": {"MN": "Нью Дели", "EN": "New Delhi"},
    "BOM": {"MN": "Мумбай", "EN": "Mumbai"},
    "ALA": {"MN": "Алматы", "EN": "Almaty"},
    "NQZ": {"MN": "Астана", "EN": "Astana"},
    "TAS": {"MN": "Ташкент", "EN": "Tashkent"},
    "FRU": {"MN": "Бишкек", "EN": "Bishkek"},

    # ==========================================
    # 5. ОЙРХИ ДОРНОД (Middle East)
    # ==========================================
    "DXB": {"MN": "Дубай", "EN": "Dubai"},
    "DWC": {"MN": "Дубай (Аль-Мактум)", "EN": "Dubai (Al Maktoum)"},
    "AUH": {"MN": "Абу Даби", "EN": "Abu Dhabi"},
    "DOH": {"MN": "Доха", "EN": "Doha"},
    "IST": {"MN": "Истанбул", "EN": "Istanbul"},
    "SAW": {"MN": "Истанбул (Сабиха Гөкчен)", "EN": "Istanbul (Sabiha Gokcen)"},
    "AYT": {"MN": "Анталья", "EN": "Antalya"},
    "MCT": {"MN": "Маскат", "EN": "Muscat"},
    "RUH": {"MN": "Эр-Рияд", "EN": "Riyadh"},

    # ==========================================
    # 6. ОРОСЫН ХОЛБООНЫ УЛС (Russia)
    # ==========================================
    "SVO": {"MN": "Москва (Шереметьево)", "EN": "Moscow (Sheremetyevo)"},
    "DME": {"MN": "Москва (Домодедово)", "EN": "Moscow (Domodedovo)"},
    "VKO": {"MN": "Москва (Внуково)", "EN": "Moscow (Vnukovo)"},
    "LED": {"MN": "Санкт-Петербург", "EN": "St. Petersburg"},
    "IKT": {"MN": "Иркутск", "EN": "Irkutsk"},
    "UUD": {"MN": "Улаан-Үд", "EN": "Ulan-Ude"},
    "VVO": {"MN": "Владивосток", "EN": "Vladivostok"},
    "OVB": {"MN": "Новосибирск", "EN": "Novosibirsk"},
    "KJA": {"MN": "Красноярск", "EN": "Krasnoyarsk"},
    "KGD": {"MN": "Калининград", "EN": "Kaliningrad"},

    # ==========================================
    # 7. ЕВРОП & ИРЛАНД (Europe & Ireland)
    # ==========================================
    "LHR": {"MN": "Лондон (Хитроу)", "EN": "London (Heathrow)"},
    "LGW": {"MN": "Лондон (Гатвик)", "EN": "London (Gatwick)"},
    "STN": {"MN": "Лондон (Станстед)", "EN": "London (Stansted)"},
    "LTN": {"MN": "Лондон (Лутон)", "EN": "London (Luton)"},
    "MAN": {"MN": "Манчестер", "EN": "Manchester"},
    "BHX": {"MN": "Бирмингем", "EN": "Birmingham"},
    "EDI": {"MN": "Эдинбург", "EN": "Edinburgh"},
    "DUB": {"MN": "Дублин", "EN": "Dublin"},
    "ORK": {"MN": "Корг", "EN": "Cork"},
    "SNN": {"MN": "Шэннон", "EN": "Shannon"},

    "GOT": {"MN": "Гётеборг", "EN": "Gothenburg"},
    "ARN": {"MN": "Стокгольм", "EN": "Stockholm"},
    "CPH": {"MN": "Копенгаген", "EN": "Copenhagen"},
    "OSL": {"MN": "Осло", "EN": "Oslo"},
    "HEL": {"MN": "Хельсинки", "EN": "Helsinki"},

    "FRA": {"MN": "Франкфурт", "EN": "Frankfurt"},
    "MUC": {"MN": "Мюнхен", "EN": "Munich"},
    "BER": {"MN": "Берлин", "EN": "Berlin"},
    "CDG": {"MN": "Парис (Шарль де Голль)", "EN": "Paris (Charles de Gaulle)"},
    "ORY": {"MN": "Парис (Орли)", "EN": "Paris (Orly)"},
    "AMS": {"MN": "Амстердам", "EN": "Amsterdam"},
    "ZRH": {"MN": "Цюрих", "EN": "Zurich"},
    "VIE": {"MN": "Вена", "EN": "Vienna"},
    "PRG": {"MN": "Прага", "EN": "Prague"},
    "FCO": {"MN": "Ром", "EN": "Rome"},
    "MXP": {"MN": "Милан (Мальпенса)", "EN": "Milan (Malpensa)"},
    "MAD": {"MN": "Мадрид", "EN": "Madrid"},
    "BCN": {"MN": "Барселона", "EN": "Barcelona"},
    "ATH": {"MN": "Афин", "EN": "Athens"},
    "WAW": {"MN": "Варшав", "EN": "Warsaw"},
    "BUD": {"MN": "Будапешт", "EN": "Budapest"},

    # ==========================================
    # 8. ХОЁР БҮЛДИЙН АМЕРИК (North & South America)
    # ==========================================
    "JFK": {"MN": "Нью-Йорк (JFK)", "EN": "New York (JFK)"},
    "EWR": {"MN": "Нью-Йорк (Ньюарк)", "EN": "New York (Newark)"},
    "LAX": {"MN": "Лос-Анжелес", "EN": "Los Angeles"},
    "SFO": {"MN": "Сан Франциско", "EN": "San Francisco"},
    "ORD": {"MN": "Чикаго (О'Хара)", "EN": "Chicago (O'Hare)"},
    "SEA": {"MN": "Сиэтл", "EN": "Seattle"},
    "MIA": {"MN": "Майами", "EN": "Miami"},
    "IAD": {"MN": "Вашингтон (Даллес)", "EN": "Washington (Dulles)"},
    "YVR": {"MN": "Ванкувер", "EN": "Vancouver"},
    "YYZ": {"MN": "Торонто", "EN": "Toronto"},
    "GRU": {"MN": "Сан Пауло", "EN": "Sao Paulo"},
    "EZE": {"MN": "Буэнос-Айрес", "EN": "Buenos Aires"},

    # ==========================================
    # 9. АВСТРАЛИ & ДАЛАЙН ОРОН (Australia & Pacific)
    # ==========================================
    "SYD": {"MN": "Сидней", "EN": "Sydney"},
    "MEL": {"MN": "Мельбурн", "EN": "Melbourne"},
    "BNE": {"MN": "Брисбен", "EN": "Brisbane"},
    "PER": {"MN": "Перт", "EN": "Perth"},
    "AKL": {"MN": "Окленд", "EN": "Auckland"},

    # ==========================================
    # 10. АФРИК (Africa)
    # ==========================================
    "CAI": {"MN": "Каир", "EN": "Cairo"},
    "JNB": {"MN": "Йоханнесбург", "EN": "Johannesburg"},
    "CPT": {"MN": "Кейптаун", "EN": "Cape Town"},
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_ubn_now():
    """ Улаанбаатарын одоогийн цагийг авах (UTC+8) """
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
        now = datetime.now(ZoneInfo("Asia/Ulaanbaatar"))
        return now.strftime("%Y.%m.%d"), now.strftime("%Y-%m-%d"), now.strftime("%B %d, %Y")

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

        status = pax["Status Code"]
        missing_reasons = []

        if pax["TicketNo"] == "-":
            missing_reasons.append("TKT дугааргүй")

        if status in ["UC", "UN", "HL", "TL"]:
            missing_reasons.append(f"{status} статус")
        
        if not joined_emails:
            missing_reasons.append("Имэйл хаяггүй")

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

def generate_email_text_base(target_lang, flight_info):
    pax_name = "{PAX_NAME}"
    pnr_code = "{PNR}"
    tkt_no = "{TICKET_NO}"

    flt_no = flight_info['flight'] or "OM137"
    flt_date = flight_info['date'] or "08NOV30"
    raw_route = flight_info['route'] or "UBN-FRA"
    dep_time = flight_info['dep_time']
    arr_time = flight_info['arr_time']
    reason = flight_info['reason']
    status_type = flight_info['status_type']

    mn_dot_date, mn_dash_date, en_date = format_date_custom(flt_date)
    city_title, full_route_display = get_route_text(raw_route, lang=target_lang)

    if target_lang == "MN":
        if status_type == "CANCEL":
            subject = f"{mn_dot_date} –ний {city_title} {flt_no} нислэг цуцлагдсан тухай мэдэгдэл"
            body = f"Хүндэт {pax_name},\n\nТаны {mn_dash_date}-ны өдрийн {flt_no} дугаартай {full_route_display} чиглэлийн нислэг цуцлагдсан болохыг үүгээр мэдэгдэж байна.\n\nЗОРЧИГЧИЙН МЭДЭЭЛЭЛ:\n• Зорчигчийн нэр: {pax_name}\n• Захиалгын дугаар (PNR): {pnr_code}\n• Тийзийн дугаар: {tkt_no}\n\nЦУЦЛАГДСАН НИСЛЭГИЙН МЭДЭЭЛЭЛ:\n• Нислэг: {flt_no}\n• Огноо: {flt_date}\n• Чиглэл: {raw_route}"
            if dep_time: body += f"\n• Нисэх цаг: {dep_time}"
            if arr_time: body += f"\n• Буух цаг: {arr_time}"
            if reason: body += f"\n• Шалтгаан: {reason}"
            body += "\n\nТийз буцаалт болон өөр өдрийн нислэгээр тийзээ өөрчилж баталгаажуулах талаар тийз худалдан авсан аяллын агентлаг эсхүл тийз олгосон газартайгаа аль болох хурдан хугацаанд холбогдоно уу.\n\nДээрх өөрчлөлтөөс шалтгаалан Танд хүндрэл, чирэгдэл учруулж байгаад хүлцэл өчье.\n\nХүндэтгэсэн,\nМИАТ ТӨХК"
        else:
            subject = f"{mn_dot_date} –ний {city_title} {flt_no} нислэгийн хуваарийн өөрчлөлтийн тухай мэдэгдэл"
            body = f"Хүндэт {pax_name},\n\nТаны {mn_dash_date}-ны өдрийн {flt_no} дугаартай {full_route_display} чиглэлийн нислэгийн цагийн хуваарьт өөрчлөлт орсон болохыг үүгээр мэдэгдэж байна.\n\nЗОРЧИГЧИЙН МЭДЭЭЛЭЛ:\n• Зорчигчийн нэр: {pax_name}\n• Захиалгын дугаар (PNR): {pnr_code}\n• Тийзийн дугаар: {tkt_no}\n\nШИНЭ НИСЛЭГИЙН МЭДЭЭЛЭЛ:\n• Нислэг: {flt_no}\n• Огноо: {flt_date}\n• Чиглэл: {raw_route}"
            if dep_time: body += f"\n• Нисэх цаг: {dep_time}"
            if arr_time: body += f"\n• Буух цаг: {arr_time}"
            body += "\n\nТаны тийзийн төлөв байдал болон шинэ нислэгийн мэдээллийг баталгаажуулахын тулд тийз худалдан авсан аяллын агентлаг эсхүл тийз олгосон газартайгаа аль болох хурдан хугацаанд холбогдоно уу.\n\nДээрх өөрчлөлтөөс шалтгаалан Танд хүндрэл, чирэгдэл учруулж байгаад хүлцэл өчье.\n\nХүндэтгэсэн,\nМИАТ ТӨХК"
    else: # EN
        if status_type == "CANCEL":
            subject = f"Flight Cancellation Notification - {flt_no} ({city_title}) - {en_date}"
            body = f"Dear {pax_name},\n\nWe regret to inform you that your flight {flt_no} {full_route_display}, scheduled for {en_date}, has been cancelled.\n\nPASSENGER DETAILS:\n- Passenger Name: {pax_name}\n- Booking Reference (PNR): {pnr_code}\n- Ticket Number: {tkt_no}\n\nCANCELLED FLIGHT DETAILS:\n- Flight: {flt_no}\n- Date: {flt_date}\n- Route: {raw_route}"
            if dep_time: body += f"\n- Departure Time: {dep_time}"
            if arr_time: body += f"\n- Arrival Time: {arr_time}"
            if reason: body += f"\n- Reason: {reason}"
            body += "\n\nFor ticket refund or to change and confirm your ticket for a flight on another date, please contact your travel agent or ticket issuing office as soon as possible.\n\nBest regards,\nMIAT Mongolian Airlines"
        else:
            subject = f"Flight Schedule Change Notification - {flt_no} ({city_title}) – {en_date}"
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
    pax_name = record.get('Passenger Name', '') if record else "{PAX_NAME}"
    pnr_code = record.get('PNR', '') if record else "{PNR}"
    tkt_no = record.get('TicketNo', '') if record else "{TICKET_NO}"

    rendered = template_text.replace("{PAX_NAME}", pax_name)
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
# CLEAR ALL CALLBACK FUNCTION (Алдаанаас сэргийлэх шийдэл)
# ============================================================

def clear_all_data():
    st.session_state.records = []
    st.session_state.missing_records = []
    st.session_state.pnl_text = ""
    st.session_state.custom_templates = {"MN": {"subject": "", "text": ""}, "EN": {"subject": "", "text": ""}}
    st.session_state.edit_mode = False
    st.session_state.pnl_textarea = ""

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
if "pnl_textarea" not in st.session_state:
    st.session_state.pnl_textarea = ""
if "custom_templates" not in st.session_state:
    st.session_state.custom_templates = {"MN": {"subject": "", "text": ""}, "EN": {"subject": "", "text": ""}}
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
    pnl_input = st.text_area("PNL Эх текст хуулах:", height=250, key="pnl_textarea")

    col_btn1, col_btn2 = st.columns([1, 1])
    if col_btn1.button("Extract PNL", type="primary"):
        if pnl_input.strip():
            st.session_state.pnl_text = pnl_input
            st.session_state.records, st.session_state.missing_records = parse_pnl(pnl_input)
            st.success("PNL амжилттай уншигдлаа!")
        else:
            st.warning("PNL текстээ оруулна уу.")
            
    col_btn2.button("Clear All", on_click=clear_all_data)

with col2:
    st.subheader("2. Нислэгийн Мэдээлэл")
    
    first_pax = st.session_state.records[0] if st.session_state.records else (st.session_state.missing_records[0] if st.session_state.missing_records else {})
    
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
        col_s1, col_s2, col_s3 = st.columns([1, 1, 3])
        if col_s1.button("☑️ Бүгдийг сонгох"):
            for r in st.session_state.records:
                r["Selected"] = True
            st.rerun()

        if col_s2.button("🔲 Бүгдийг болиулах"):
            for r in st.session_state.records:
                r["Selected"] = False
            st.rerun()

        df_valid = pd.DataFrame(st.session_state.records)
        cols_to_show = ["Selected", "SeqNo", "PNLNo", "Passenger Name", "PNR", "StatusCode", "BookingDate", "TicketNo", "Email", "Language", "SendStatus"]
        
        edited_df = st.data_editor(
            df_valid[cols_to_show],
            column_config={
                "Selected": st.column_config.CheckboxColumn("Сонгох", default=True)
            },
            disabled=["SeqNo", "PNLNo", "Passenger Name", "PNR", "StatusCode", "BookingDate", "TicketNo", "Email", "Language", "SendStatus"],
            hide_index=True,
            use_container_width=True,
            key="passenger_editor"
        )
        
        for idx, row in edited_df.iterrows():
            st.session_state.records[idx]["Selected"] = row["Selected"]

        mn_cnt = sum(1 for r in st.session_state.records if r["Language"] == "MN" and r["Selected"])
        en_cnt = sum(1 for r in st.session_state.records if r["Language"] == "EN" and r["Selected"])
        na_cnt = sum(1 for r in st.session_state.records if r["Language"] == "N/A" and r["Selected"])
        
        no_tkt_cnt = sum(1 for r in st.session_state.missing_records if "TKT дугааргүй" in r["MissingReason"])
        no_email_cnt = sum(1 for r in st.session_state.missing_records if "Имэйл хаяггүй" in r["MissingReason"])
        
        total_pax = len(st.session_state.records) + len(st.session_state.missing_records)
        
        st.write(f"**Мэдээлэл:** 🔵 MN: {mn_cnt} | 🟢 EN: {en_cnt} | 🔴 N/A: {na_cnt} | 🎟️ TKT-гүй: {no_tkt_cnt} | 📧 Имэйлгүй: {no_email_cnt} | 👥 **Нийт зорчигчид:** {total_pax}")
    else:
        st.info("Одоогоор уншигдсан идэвхтэй зорчигч байхгүй байна.")

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
        if st.session_state.custom_templates[preview_lang]["text"]:
            if st.button("🔄 Анхны хувилбар"):
                st.session_state.custom_templates[preview_lang] = {"subject": "", "text": ""}
                st.session_state.edit_mode = False
                st.rerun()

    orig_subj, orig_text = generate_email_text_base(preview_lang, flight_info)

    curr_subj = st.session_state.custom_templates[preview_lang]["subject"] or orig_subj
    curr_text = st.session_state.custom_templates[preview_lang]["text"] or orig_text

    lbl_title = "ГАРЧИГ:" if preview_lang == "MN" else "SUBJECT:"

    if st.session_state.edit_mode:
        st.info("💡 Текст доторх `{PAX_NAME}`, `{PNR}`, `{TICKET_NO}` түлхүүр үгс нь зорчигч бүрийн мэдээллээр автоматаар солигдох болно.")
        new_subj = st.text_input(f"{lbl_title}", value=curr_subj)
        new_text = st.text_area("Засах боломжтой эх текст:", value=curr_text, height=320)
        
        st.session_state.custom_templates[preview_lang]["subject"] = new_subj
        st.session_state.custom_templates[preview_lang]["text"] = new_text
    else:
        sample_rec = st.session_state.records[0] if st.session_state.records else None
        st.markdown(f"**{lbl_title}** {curr_subj}")
        
        rendered_plain = render_custom_template(curr_text, sample_rec)
        rendered_html = text_to_html(rendered_plain)
        st.components.v1.html(rendered_html, height=350, scrolling=True)

st.divider()

# --- DIALOG / MODAL FOR CONFIRMATION ---
@st.dialog("Имэйл текстийг шалгах ба Баталгаажуулах", width="large")
def confirm_and_send_dialog():
    st.warning("⚠️ Дараах имэйлийн эх текст зорчигчид руу илгээгдэх гэж байна. Шалгаад 'Илгээх' эсвэл 'Засах' товчийг сонгоно уу.")
    
    tab_mn, tab_en = st.tabs(["🇲🇳 Монгол (MN)", "🇬🇧 Англи (EN)"])
    sample_rec = st.session_state.records[0] if st.session_state.records else None
    
    with tab_mn:
        orig_subj, orig_text = generate_email_text_base("MN", flight_info)
        s_subj = st.session_state.custom_templates["MN"]["subject"] or orig_subj
        s_text = st.session_state.custom_templates["MN"]["text"] or orig_text
        st.markdown(f"**ГАРЧИГ:** {s_subj}")
        st.components.v1.html(text_to_html(render_custom_template(s_text, sample_rec)), height=250, scrolling=True)
        
    with tab_en:
        orig_subj_en, orig_text_en = generate_email_text_base("EN", flight_info)
        s_subj_en = st.session_state.custom_templates["EN"]["subject"] or orig_subj_en
        s_text_en = st.session_state.custom_templates["EN"]["text"] or orig_text_en
        st.markdown(f"**SUBJECT:** {s_subj_en}")
        st.components.v1.html(text_to_html(render_custom_template(s_text_en, sample_rec)), height=250, scrolling=True)
        
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
                    orig_subj, orig_text = generate_email_text_base(lang, flight_info)
                    
                    cust_subj = st.session_state.custom_templates[lang]["subject"]
                    cust_text = st.session_state.custom_templates[lang]["text"]
                    
                    final_subj = cust_subj if cust_subj else orig_subj
                    raw_text = cust_text if cust_text else orig_text
                    
                    final_plain = render_custom_template(raw_text, pax)
                    final_html = text_to_html(final_plain)

                    send_email_smtp(sender_email, app_password, recipient, final_subj, final_plain, final_html)
                    pax["SendStatus"] = "Sent Successfully"
                    pax["SentTime"] = get_ubn_now()
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
        
        cols_to_drop = ["Selected", "SeqNo", "EmailList"]
        df_export_cleaned = df_export.drop(columns=[c for c in cols_to_drop if c in df_export.columns])
        
        csv_data = df_export_cleaned.to_csv(index=False).encode('utf-8-sig')
        
        ubn_file_time = datetime.now(ZoneInfo("Asia/Ulaanbaatar")).strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 EXCEL тайлан татах",
            data=csv_data,
            file_name=f"PNL_Export_{ubn_file_time}.csv",
            mime="text/csv",
            use_container_width=True
        )
