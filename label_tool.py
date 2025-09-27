import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.utils import ImageReader
from io import BytesIO
import base64
import qrcode
import datetime

# ✅ Polished customer service messages
messages = {
    "Riccardo Valeria": """<br/>Important Note<br/>Thank you for placing your order with us. If you are happy with your purchase, we would truly appreciate your review.  

If you experience any issue with your order, please don’t hesitate to contact us on Tiktok or Email: info@riccardovaleria.com  
or simply scan the QR code to send us a direct message.  

<br/>Best Regards<br/>Team Riccardo Valeria""",

    "StyleMyBedroom": """<br/>Important Note<br/>Thank you for shopping with us. If you are happy with your purchase, we would be grateful if you could leave us a review.  

If you encounter any issue with your order, please contact us on Tiktok or Email: myinfo@stylemybedroom.com  
or scan the QR code to reach us directly.  

<br/>Best Regards<br/>Team StyleMyBedroom"""
}

# ✅ WhatsApp greetings per company
greetings = {
    "Riccardo Valeria": "Hi, this is Riccardo Valeria support. Please confirm your Order ID: ______",
    "StyleMyBedroom": "Hi, this is StyleMyBedroom support. Please confirm your Order ID: ______"
}

# ✅ Fixed layout values
FONT_SIZE = 6
BOTTOM_MARGIN = 30
QR_SIZE = 50
QR_X = 20
QR_Y = 20
SPACING = 13


def create_overlay(page_width, page_height, message_text, bottom_margin, add_qr, whatsapp_number, greeting):
    """Create overlay with message + QR code (with greeting text)."""
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))

    # ✅ QR Code with greeting
    qr_width = qr_height = 0
    if add_qr and whatsapp_number:
        encoded_greeting = greeting.replace(" ", "%20").replace("\n", "%0A")
        qr_url = f"https://wa.me/{whatsapp_number.replace('+', '')}?text={encoded_greeting}"

        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(qr_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        qr_img = ImageReader(img_buffer)
        qr_width = qr_height = QR_SIZE
        can.drawImage(qr_img, QR_X, QR_Y, width=qr_width, height=qr_height, mask="auto")

    # ✅ Message style
    normal = ParagraphStyle(
        "normal",
        fontName="Helvetica",
        fontSize=FONT_SIZE,
        leading=FONT_SIZE + 2,
        alignment=0
    )

    para = Paragraph(message_text, normal)

    # ✅ Place text next to QR
    text_x = QR_X + qr_width + (SPACING if qr_width > 0 else 0)
    text_y = QR_Y
    w, h = para.wrap(page_width - text_x - 40, page_height)
    para.drawOn(can, text_x, text_y)

    can.save()
    packet.seek(0)
    return PdfReader(packet)


def process_single_pdf(uploaded_file, message_text, bottom_margin, add_qr, whatsapp_number, greeting):
    """Process one PDF and return processed pages."""
    reader = PdfReader(uploaded_file)
    processed_pages = []

    for i, page in enumerate(reader.pages):
        if (i + 1) % 2 == 0:  # packing slips only
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            overlay = create_overlay(
                page_width, page_height, message_text, bottom_margin,
                add_qr, whatsapp_number, greeting
            )
            page.merge_page(overlay.pages[0])

        processed_pages.append(page)

    return processed_pages


def add_message_multiple(files, message_text, bottom_margin, add_qr, whatsapp_number, greeting):
    """Process multiple PDFs and merge into one output file."""
    writer = PdfWriter()

    for file in files:
        pages = process_single_pdf(file, message_text, bottom_margin, add_qr, whatsapp_number, greeting)
        for p in pages:
            writer.add_page(p)

    output = BytesIO()
    writer.write(output)
    output.seek(0)

    return output, len(writer.pages)


def display_pdf_page(pdf_bytes, page_num):
    """Preview single page of PDF in iframe."""
    temp_reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    writer.add_page(temp_reader.pages[page_num])

    temp_output = BytesIO()
    writer.write(temp_output)
    base64_pdf = base64.b64encode(temp_output.getvalue()).decode("utf-8")

    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="750"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# ✅ Streamlit UI
st.set_page_config(layout="wide")
st.title("📦 TikTok Label Message Tool")
st.write("Upload one or more TikTok PDF label files. The tool will merge them, and add the customer service message + WhatsApp QR code ONLY on the packing slips.")

col1, col2 = st.columns([1, 2])

with col1:
    # Company selector
    company = st.radio("🏢 Select Company", list(messages.keys()))
    default_message = messages[company]
    greeting = greetings[company]

    # Editable message box
    message_text = st.text_area("✍️ Edit or Update Message", default_message, height=200)

    # ✅ Multiple file uploader
    uploaded_files = st.file_uploader("📤 Upload Label PDFs", type="pdf", accept_multiple_files=True)

    result_pdf = None
    total_pages = 0

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")

        whatsapp_number = "+447466403232"  # same number for all companies

        result_pdf, total_pages = add_message_multiple(
            uploaded_files, message_text, BOTTOM_MARGIN,
            add_qr=True, whatsapp_number=whatsapp_number, greeting=greeting
        )

        page_num = st.number_input("📄 Select page to preview", min_value=1, max_value=total_pages, value=1)

        # ✅ Auto filename with company name + current date
        today = datetime.date.today().strftime("%Y%m%d")
        company_filename = company.replace(" ", "")
        filename = f"{company_filename}_labels_{today}.pdf"

        st.download_button(
            label="⬇️ Download Updated PDF",
            data=result_pdf,
            file_name=filename,
            mime="application/pdf"
        )

with col2:
    st.subheader("👀 PDF Preview")
    if uploaded_files and result_pdf:
        display_pdf_page(result_pdf.getvalue(), page_num - 1)
    else:
        st.info("Upload PDFs to see the preview here.")
