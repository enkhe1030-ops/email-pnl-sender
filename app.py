import re
import fitz  # PyMuPDF


def parse_pnl_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"

    # Зорчигчдын блокийг дугаараар нь салгах (3 цифртэй дарааллын дугаар)
    raw_blocks = re.split(r"\n(?=\d{3}\s+)", full_text)

    active_passengers = []
    incomplete_passengers = []

    for block in raw_blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue

        # Зорчигчийн дугаар болон үндсэн мөр мөн эсэхийг шалгах
        first_line = lines[0]
        match = re.match(r"^(\d{3})\s+(.*)", first_line)
        if not match:
            continue

        pax_num = match.group(1)
        pax_info = match.group(2)

        # 1. Нэр болон Статус шүүх
        status_match = re.search(
            r"([A-Z0-9/-]+)\s+([A-Z0-9]+)\s+([A-Z])\s+([A-Z]{2})", pax_info
        )

        pax_name = pax_info
        status = "N/A"
        if status_match:
            pax_name = status_match.group(1)
            status = status_match.group(4)
        else:
            name_extract = re.search(r"([A-Z0-9/-]+(?:\s+[A-Z]+)?)", pax_info)
            if name_extract:
                pax_name = name_extract.group(1)
            status_extract = re.search(
                r"\b(HK|TK|SA|RR|UN|UC|NO|HX)\b", pax_info
            )
            if status_extract:
                status = status_extract.group(1)

        # 2. Имэйл хаяг хайх (SSR CTCE эсвэл стандарт имэйл)
        email = None
        ctce_match = re.search(r"SSR\s+CTCE.*?\s+([^\s]+//[^\s]+)", block)
        if ctce_match:
            email = ctce_match.group(1).replace("//", "@")
        else:
            email_match = re.search(
                r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", block
            )
            if email_match:
                email = email_match.group(0)

        # 3. TKT (E-ticket) дугаар хайх (FA PAX хэсгээс)
        tkt_number = None
        tkt_match = re.search(r"FA\s+PAX\s+([0-9]{3}-[0-9]{10,})", block)
        if tkt_match:
            tkt_number = tkt_match.group(1)
        else:
            tkt_match_alt = re.search(r"FA\s+PAX\s+([0-9]{13,14})", block)
            if tkt_match_alt:
                tkt_number = tkt_match_alt.group(1)

        # Зорчигчийн мэдээллийн толь
        pax_data = {
            "num": pax_num,
            "name": pax_name,
            "status": status,
            "email": email if email else "Байхгүй",
            "tkt": tkt_number if tkt_number else "Байхгүй",
        }

        # 4. Ангилах шалгуур:
        # HK, TK, SA, RR статустай + TKT-тэй + Имэйлтэй бол ИДЭВХТЭЙ
        valid_statuses = ["HK", "TK", "SA", "RR"]
        is_status_ok = status in valid_statuses
        is_tkt_ok = tkt_number is not None
        is_email_ok = email is not None

        if is_status_ok and is_tkt_ok and is_email_ok:
            active_passengers.append(pax_data)
        else:
            reasons = []
            if not is_status_ok:
                reasons.append(f"Статус: {status}")
            if not is_tkt_ok:
                reasons.append("ТКТ-гүй")
            if not is_email_ok:
                reasons.append("Имэйлгүй")

            pax_data["reason"] = ", ".join(reasons)
            incomplete_passengers.append(pax_data)

    return active_passengers, incomplete_passengers


def print_pnl_report(active, incomplete):
    print("=" * 75)
    print(
        f"📋 Идэвхтэй Зорчигчид: {len(active)}  |  ⚠️ Мэдээлэл Дутуу Зорчигчид: {len(incomplete)}"
    )
    print("=" * 75)

    print(f"\n📋 ИДЭВХТЭЙ ЗОРЧИГЧИД ({len(active)}):")
    print("-" * 75)
    for p in active:
        print(
            f"#{p['num']} | {p['name']:<25} | Статус: {p['status']} | TKT: {p['tkt']} | Email: {p['email']}"
        )

    print(f"\n⚠️ МЭДЭЭЛЭЛ ДУТУУ ЗОРЧИГЧИД ({len(incomplete)}):")
    print("-" * 75)
    for p in incomplete:
        print(
            f"#{p['num']} | {p['name']:<25} | Шалтгаан: [{p['reason']}] | TKT: {p['tkt']} | Email: {p['email']}"
        )


if __name__ == "__main__":
    # PDF файлынхаа нэрийг энд оруулна уу
    pdf_file_path = "name list.pdf"

    try:
        active_pax, incomplete_pax = parse_pnl_pdf(pdf_file_path)
        print_pnl_report(active_pax, incomplete_pax)
    except FileNotFoundError:
        print(
            f"Алдаа: '{pdf_file_path}' файл олдсонгүй. Файлын нэр ба зам заагчаа шалгана уу."
        )
    except Exception as e:
        print(f"Алдаа гарлаа: {e}")
