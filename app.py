import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ----------------------------------------------------
# 1. EXCEL ФАЙЛ ҮҮСГЭХ (openpyxl)
# ----------------------------------------------------
def create_excel_report(output_filename="PNL_Report.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "PNL Data"

    # Сүлжээний шугамыг нууж No Border хэлбэртэй болгох
    ws.views.sheetView[0].showGridLines = False

    # Баганы толгой мөрүүд
    headers = [
        "PNL No", 
        "Passenger Name", 
        "PNR", 
        "Class", 
        "Booking date", 
        "Ticket NO", 
        "Office code"
    ]

    # Загвар болон өнгөний тохиргоо (Header - Дээд мөр)
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid") # Хөх дэвсгэр
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF") # Цагаан өнгийн бичиг
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")

    # Дээд мөрийг бичих
    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center

    # Жишээ дээж мэдээлэл
    sample_data = [
        ["PNL-001", "BAT / ERDENE MR", "ABC12D", "Y", "2026-09-15", "097-1234567890", "ULN1A0100"],
        ["PNL-002", "BOLOR / TUYA MS", "XYZ98W", "J", "2026-09-16", "097-0987654321", "ULN1A0100"],
        ["PNL-003", "KHULAN / BAYAR MS", "KLM34E", "Y", "2026-09-18", "097-1122334455", "ULN1A0200"],
    ]

    # Хүснэгтийн өгөгдлийг оруулах (Хүрээ шугамгүй - No Border)
    for row_data in sample_data:
        ws.append(row_data)

    # Өгөгдлийн мөрүүдийн цуврал тохиргоо
    data_font = Font(name="Calibri", size=10)
    for row in ws.iter_rows(min_row=2, max_row=len(sample_data) + 1, min_col=1, max_col=len(headers)):
        for cell in row:
            cell.font = data_font
            cell.alignment = align_left

    # Баганы өргөнийг автоматаар тааруулах
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # Хэвлэх тохиргоо (A4 болон Portrait хэмжээ)
    ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
    ws.page_setup.paperSize = ws.PAPERSIZE_A4

    wb.save(output_filename)
    print(f"Excel файл амжилттай үүсгэгдлээ: {output_filename}")


# ----------------------------------------------------
# 2. PDF ФАЙЛ ҮҮСГЭХ (reportlab - A4, Portrait, No Border)
# ----------------------------------------------------
def create_pdf_report(output_filename="PNL_Report.pdf"):
    # A4 ба Portrait хэмжээ тохируулах
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=portrait(A4),
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Гарчиг
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        alignment=1, # Center
        spaceAfter=15
    )
    story.append(Paragraph("Passenger Name List (PNL)", title_style))
    story.append(Spacer(1, 10))

    # Хүснэгтийн мэдээлэл
    headers = [
        "PNL No", 
        "Passenger Name", 
        "PNR", 
        "Class", 
        "Booking date", 
        "Ticket NO", 
        "Office code"
    ]

    data = [headers] + [
        ["PNL-001", "BAT / ERDENE MR", "ABC12D", "Y", "2026-09-15", "097-1234567890", "ULN1A0100"],
        ["PNL-002", "BOLOR / TUYA MS", "XYZ98W", "J", "2026-09-16", "097-0987654321", "ULN1A0100"],
        ["PNL-003", "KHULAN / BAYAR MS", "KLM34E", "Y", "2026-09-18", "097-1122334455", "ULN1A0200"],
    ]

    # Багануудын өргөн (A4 Portrait - Нийт өргөн ~523 pt)
    col_widths = [55, 120, 50, 40, 75, 100, 80]

    # Хүснэгтийн загвар (No Border болон Цагаан текстийн тохиргоо)
    t_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E78')),  # Дээд мөрний фон
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),                 # Толгой хэсгийн текст ЦАГААН
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Энд ямар нэгэн GRID эсвап BORDER стиль нэмээгүй тул БҮРЭН NO BORDER байна
    ])

    table = Table(data, colWidths=col_widths, style=t_style)
    story.append(table)

    # PDF үүсгэх
    doc.build(story)
    print(f"PDF файл амжилттай үүсгэгдлээ: {output_filename}")


if __name__ == "__main__":
    create_excel_report()
    create_pdf_report()
