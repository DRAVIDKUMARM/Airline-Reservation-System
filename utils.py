"""
utils.py
Small stateless helpers shared across the app: password hashing,
input validation, ID generation, and PDF boarding-pass export.
"""

import hashlib
import re
import random
import string
import os
import textwrap
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PRIMARY_COLOR = "#1677FF"
TICKET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tickets")

AIRPORTS = [
    "Chennai (MAA)", "Delhi (DEL)", "Mumbai (BOM)", "Bangalore (BLR)", "Hyderabad (HYD)",
    "Kolkata (CCU)", "Dubai (DXB)", "Singapore (SIN)", "London (LHR)", "New York (JFK)",
    "Tokyo (HND)", "Paris (CDG)", "Sydney (SYD)", "Auckland (AKL)", "Doha (DOH)",
    "Cape Town (CPT)", "Toronto (YYZ)", "Berlin (BER)", "Bangkok (BKK)", "Kuala Lumpur (KUL)",
    "Abu Dhabi (AUH)", "Sharjah (SHJ)", "Frankfurt (FRA)", "Amsterdam (AMS)", "Rome (FCO)",
    "Chicago (ORD)", "Los Angeles (LAX)", "San Francisco (SFO)", "Washington (IAD)",
    "Dallas (DFW)", "Houston (IAH)", "Miami (MIA)", "Boston (BOS)", "Atlanta (ATL)",
    "Vancouver (YVR)", "Montreal (YUL)", "Mexico City (MEX)", "Sao Paulo (GRU)",
    "Buenos Aires (EZE)", "Lima (LIM)", "Johannesburg (JNB)", "Cairo (CAI)",
    "Nairobi (NBO)", "Istanbul (IST)", "Madrid (MAD)", "Barcelona (BCN)",
    "Vienna (VIE)", "Zurich (ZRH)", "Copenhagen (CPH)", "Oslo (OSL)",
    "Stockholm (ARN)", "Helsinki (HEL)", "Moscow (SVO)", "Beijing (PEK)",
    "Shanghai (PVG)", "Hong Kong (HKG)", "Seoul (ICN)", "Taipei (TPE)",
    "Manila (MNL)", "Jakarta (CGK)", "Bali (DPS)", "Perth (PER)",
    "Melbourne (MEL)", "Brisbane (BNE)", "Wellington (WLG)", "Christchurch (CHC)",
    "Riyadh (RUH)", "Jeddah (JED)", "Muscat (MCT)", "Kuwait City (KWI)",
    "Tel Aviv (TLV)", "Kathmandu (KTM)", "Colombo (CMB)", "Dhaka (DAC)",
    "Yangon (RGN)", "Phuket (HKT)", "Mauritius (MRU)", "Maldives (MLE)"
]

AIRLINES = [
    "IndiGo", "Air India", "Emirates", "Singapore Airlines", "Qatar Airways",
    "British Airways", "Etihad Airways", "Lufthansa", "Thai Airways"
]


def class_price(base, travel_class):
    if travel_class == "Premium Economy":
        return base + 2500
    if travel_class == "Business":
        return base + 12000
    if travel_class == "First Class":
        return base + 25000
    return base


def apply_discount(price, fare_type):
    if fare_type == "Student - 50% OFF":
        return int(price * 0.50)
    if fare_type == "Senior Citizen - 25% OFF":
        return int(price * 0.75)
    if fare_type == "Armed Forces - 30% OFF":
        return int(price * 0.70)
    return price


def final_price(base, travel_class, travellers, fare_type):
    price = class_price(base, travel_class)
    count = int(str(travellers).split()[0])
    price *= count
    return apply_discount(price, fare_type)


def hash_password(password: str) -> str:
    """SHA-256 hash. Not bcrypt-grade, but avoids ever storing plaintext."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip()))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    return True, ""


def generate_booking_ref() -> str:
    return "SB" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def format_currency(amount: float) -> str:
    return f"${amount:,.2f}"


def _safe_ticket_name(value):
    text = str(value or "ticket").replace(" ", "_")
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    return cleaned.strip("._") or "ticket"


def _airport_code(city: str) -> str:
    """
    Best-effort 3-letter airport code from a city name, since the DB
    only stores full city names, not real IATA codes.
    """
    letters = "".join(ch for ch in city.upper() if ch.isalpha())
    return (letters + "XXX")[:3] if letters else "XXX"


def _carrier_code(airline: str) -> str:
    """Best-effort 2-letter carrier code, e.g. 'Air Canada' -> 'AC'."""
    words = [w for w in airline.split() if w]
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    if words:
        return words[0][:2].upper()
    return "XX"


def _flight_number(booking_ref: str, carrier_code: str) -> str:
    """Create a stable display flight number from a booking reference."""
    digits = sum(ord(char) for char in booking_ref) % 9000 + 1000
    return f"{carrier_code} {digits}"


def _pdf_safe_text(value):
    """Keep text compatible with ReportLab's built-in Helvetica fonts."""
    return str(value or "N/A").encode("latin-1", "replace").decode("latin-1")


def create_ticket_pdf(ticket):
    os.makedirs(TICKET_DIR, exist_ok=True)
    seat = ticket.get("seat", "N/A")
    seat_value = ", ".join(seat) if isinstance(seat, (list, tuple)) else str(seat)
    if ticket.get("return_seat"):
        seat_value += f" / Return: {ticket['return_seat']}"
    flight_no = _safe_ticket_name(ticket.get("flight_no", "FLT"))
    file_name = os.path.join(TICKET_DIR, f"SkyBook_Ticket_{flight_no}_{_safe_ticket_name(seat_value)}.pdf")
    pdf = canvas.Canvas(file_name, pagesize=letter)
    width, height = letter

    pdf.setFillColor(HexColor(PRIMARY_COLOR))
    pdf.rect(0, height - 120, width, 120, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawString(50, height - 70, "SKYBOOK AIRLINES")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 95, "Premium Boarding Pass")

    pdf.setFillColor(colors.HexColor("#f3f4f6"))
    pdf.roundRect(40, height - 360, width - 80, 210, 16, fill=1, stroke=0)
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 130, "PASSENGER DETAILS")
    pdf.drawString(320, height - 130, "TRAVEL DETAILS")

    route = str(ticket.get("route", "N/A"))
    route_from, separator, route_to = route.partition("→")
    if not separator:
        route_from, route_to = route, "N/A"
    booking_ids = ticket.get("booking_ids") or [ticket.get("booking_id", "N/A")]
    booking_id_text = ", ".join(str(booking_id) for booking_id in booking_ids)
    return_flight = ticket.get("return_flight") or {}

    passenger_fields = [
        ("Booking ID / PNR", booking_id_text),
        ("Passenger", ", ".join(ticket.get("passengers", [])) or ticket.get("passenger", "N/A")),
        ("Seat", seat_value),
        ("Class", ticket.get("travel_class", "N/A")),
    ]
    travel_fields = [
        ("Airline", ticket.get("airline", "N/A")),
        ("Flight No", ticket.get("flight_no", "N/A")),
        ("From", route_from.strip()),
        ("To", route_to.strip()),
        ("Travel Date", ticket.get("travel_date", "N/A")),
    ]
    if return_flight:
        travel_fields.extend([
            ("Return Flight", return_flight.get("flight_no", "N/A")),
            ("Return Route", return_flight.get("route", "N/A")),
            ("Return Date", return_flight.get("date", ticket.get("return_date", "N/A"))),
        ])

    pdf.setFont("Helvetica", 11)
    y_offset = height - 160
    for label, value in passenger_fields:
        pdf.drawString(50, y_offset, _pdf_safe_text(label))
        value_lines = textwrap.wrap(_pdf_safe_text(value), width=26) or ["N/A"]
        for line_index, line in enumerate(value_lines):
            prefix = ": " if line_index == 0 else "  "
            pdf.drawString(150, y_offset, f"{prefix}{line}")
            if line_index < len(value_lines) - 1:
                y_offset -= 14
        y_offset -= 22

    y_offset = height - 160
    for label, value in travel_fields:
        pdf.drawString(320, y_offset, _pdf_safe_text(label))
        pdf.drawString(420, y_offset, f": {_pdf_safe_text(value)}")
        y_offset -= 22

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 372, "PAYMENT SUMMARY")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, height - 394, f"Method: {_pdf_safe_text(ticket.get('payment_method', 'N/A'))}")
    pdf.drawString(50, height - 414, f"Reference: {_pdf_safe_text(ticket.get('payment_reference', 'N/A'))}")
    amount = int(ticket.get("price", 0) or 0)
    pdf.drawString(50, height - 434, f"Total Amount Paid (INR): {amount:,}")
    pdf.setStrokeColor(colors.black)
    pdf.rect(width - 190, height - 340, 140, 140, fill=0)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(width - 120, height - 270, "QR CODE")
    pdf.drawCentredString(width - 120, height - 290, "PLACEHOLDER")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(50, height - 455, "Please arrive at least 90 minutes prior to departure. Carry valid ID.")
    pdf.drawString(50, height - 470, f"Generated on: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}")
    pdf.setFillColor(HexColor(PRIMARY_COLOR))
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(50, 50, "SkyBook Airlines - Travel Smart, Fly Premium")
    pdf.save()
    return file_name
