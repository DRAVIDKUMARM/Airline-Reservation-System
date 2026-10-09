import sqlite3
import os
import random
from datetime import datetime, timedelta

from utils import AIRPORTS, AIRLINES

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skybook_full.db")

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cur = self.conn.cursor()
        self.setup()
        self.seed()

    def setup(self):
        self._migrate_legacy_tables()
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'customer',
            created_at TEXT
        )
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS flights(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_no TEXT UNIQUE NOT NULL,
            airline TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            depart_time TEXT NOT NULL,
            arrive_time TEXT NOT NULL,
            duration TEXT NOT NULL,
            seats INTEGER NOT NULL,
            fare INTEGER NOT NULL,
            status TEXT DEFAULT 'On Time'
        )
        """)

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            passenger TEXT,
            flight_no TEXT,
            airline TEXT,
            route TEXT,
            travel_date TEXT,
            travellers TEXT,
            travel_class TEXT,
            fare_type TEXT,
            seat TEXT,
            price INTEGER,
            payment_method TEXT,
            payment_reference TEXT,
            status TEXT DEFAULT 'Confirmed',
            booked_at TEXT,
            passenger_details TEXT
        )
        """)

        booking_columns = {
            row[1] for row in self.cur.execute("PRAGMA table_info(bookings)").fetchall()
        }
        if "cancellation_id" not in booking_columns:
            self.cur.execute("ALTER TABLE bookings ADD COLUMN cancellation_id TEXT")
        if "cancellation_reason" not in booking_columns:
            self.cur.execute("ALTER TABLE bookings ADD COLUMN cancellation_reason TEXT")
        if "passenger_details" not in booking_columns:
            self.cur.execute("ALTER TABLE bookings ADD COLUMN passenger_details TEXT")

        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER,
            amount INTEGER,
            method TEXT,
            reference TEXT,
            status TEXT,
            paid_at TEXT
        )
        """)


        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS refunds(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER,
            amount INTEGER,
            status TEXT DEFAULT 'Pending',
            processed_at TEXT
        )
        """)

        self.conn.commit()

    def _migrate_legacy_tables(self):
        """Keep older project databases from breaking the current schema."""
        flights_columns = {
            row[1] for row in self.cur.execute("PRAGMA table_info(flights)").fetchall()
        }
        if flights_columns and "flight_no" not in flights_columns:
            self.cur.execute("ALTER TABLE flights RENAME TO flights_legacy")

        bookings_columns = {
            row[1] for row in self.cur.execute("PRAGMA table_info(bookings)").fetchall()
        }
        if bookings_columns and "user_email" not in bookings_columns:
            self.cur.execute("ALTER TABLE bookings RENAME TO bookings_legacy")
        self.conn.commit()

    def seed(self):
        self.cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
        if self.cur.fetchone()[0] == 0:
            self.cur.execute(
                "INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)",
                ("Admin", "admin@gmail.com", "admin123", "admin", datetime.now().strftime("%d-%m-%Y %I:%M %p"))
            )

        self.cur.execute("SELECT COUNT(*) FROM flights")
        if self.cur.fetchone()[0] == 0:
            rows = [
                ("FL1001","Emirates","Chennai (MAA)","Dubai (DXB)","08:30","12:45","4h 15m",72,18500,"On Time"),
                ("FL1002","Air India","Chennai (MAA)","Delhi (DEL)","09:15","12:05","2h 50m",72,5500,"On Time"),
                ("FL1003","Singapore Airlines","Chennai (MAA)","Singapore (SIN)","10:00","16:20","4h 50m",72,21000,"On Time"),
                ("FL1004","Qatar Airways","Delhi (DEL)","Dubai (DXB)","15:20","19:10","3h 50m",72,20000,"Delayed"),
                ("FL1005","British Airways","Mumbai (BOM)","London (LHR)","02:30","10:15","9h 15m",72,42000,"On Time"),
                ("FL1006","Singapore Airlines","Bangalore (BLR)","Tokyo (HND)","23:10","08:45","8h 05m",72,36000,"On Time"),
                ("FL1007","IndiGo","Mumbai (BOM)","Delhi (DEL)","06:10","08:20","2h 10m",72,6100,"On Time"),
                ("FL1008","Etihad Airways","Chennai (MAA)","Abu Dhabi (AUH)","11:00","14:35","4h 05m",72,17800,"On Time"),
                ("FL1009","Lufthansa","Delhi (DEL)","Berlin (BER)","01:20","09:35","8h 45m",72,45500,"On Time"),
                ("FL1010","Thai Airways","Kolkata (CCU)","Bangkok (BKK)","13:00","16:05","2h 35m",72,16500,"On Time"),
            ]

            self.cur.executemany("""
            INSERT INTO flights(flight_no, airline, source, destination, depart_time, arrive_time, duration, seats, fare, status)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """, rows)

        self.conn.commit()
        self._ensure_demo_flights(1000)
        self._ensure_route_coverage(3)

    def _ensure_demo_flights(self, target_count):
        """Fill the local demo database with enough searchable routes."""
        current_count = self.cur.execute("SELECT COUNT(*) FROM flights").fetchone()[0]
        if current_count >= target_count:
            return

        existing_numbers = {
            row[0] for row in self.cur.execute("SELECT flight_no FROM flights").fetchall()
        }
        rng = random.Random(20260830)
        rows = []
        number = 2000
        while current_count + len(rows) < target_count:
            flight_no = f"FL{number}"
            number += 1
            if flight_no in existing_numbers:
                continue
            source, destination = rng.sample(AIRPORTS, 2)
            depart_hour = rng.randrange(0, 24)
            depart_minute = rng.choice([0, 10, 20, 30, 40, 50])
            duration_hours = rng.randrange(1, 13)
            duration_minutes = rng.choice([0, 15, 30, 45])
            arrive_hour = (depart_hour + duration_hours) % 24
            arrive_minute = (depart_minute + duration_minutes) % 60
            rows.append((
                flight_no, rng.choice(AIRLINES), source, destination,
                f"{depart_hour:02d}:{depart_minute:02d}",
                f"{arrive_hour:02d}:{arrive_minute:02d}",
                f"{duration_hours}h {duration_minutes:02d}m", rng.randrange(40, 181),
                rng.randrange(4500, 50001, 250), rng.choice(["On Time", "On Time", "Delayed"])
            ))
            existing_numbers.add(flight_no)

        self.cur.executemany("""
        INSERT INTO flights(flight_no, airline, source, destination, depart_time, arrive_time, duration, seats, fare, status)
        VALUES(?,?,?,?,?,?,?,?,?,?)
        """, rows)
        self.conn.commit()

    def _ensure_route_coverage(self, minimum_per_route=3):
        """Ensure every airport pair used by the app has at least N flights.

        The home-page airport list contains Indian and international airports.
        This keeps search results useful for every selectable origin/destination
        pair instead of relying on random demo flights.
        """
        extra_airports = [
            "Bengaluru (BLR)", "Hyderabad (HYD)", "Kolkata (CCU)", "Kochi (COK)",
            "Coimbatore (CJB)", "Madurai (IXM)", "Trichy (TRZ)", "Goa (GOI)",
            "Pune (PNQ)", "Ahmedabad (AMD)", "Jaipur (JAI)", "Doha (DOH)",
            "Abu Dhabi (AUH)", "Kuala Lumpur (KUL)", "Bangkok (BKK)", "Sydney (SYD)",
            "Melbourne (MEL)", "Auckland (AKL)", "Cape Town (CPT)", "Johannesburg (JNB)",
            "Toronto (YYZ)", "Frankfurt (FRA)", "Amsterdam (AMS)", "Zurich (ZRH)"
        ]
        airports = sorted(set(AIRPORTS + extra_airports))

        existing = {}
        for source, destination, count in self.cur.execute(
            "SELECT source, destination, COUNT(*) FROM flights GROUP BY source, destination"
        ).fetchall():
            existing[(source, destination)] = count

        existing_numbers = {
            row[0] for row in self.cur.execute("SELECT flight_no FROM flights").fetchall()
        }
        rng = random.Random(20260925)
        rows = []
        number = 10000

        for source in airports:
            for destination in airports:
                if source == destination:
                    continue
                missing = max(0, minimum_per_route - existing.get((source, destination), 0))
                for _ in range(missing):
                    while f"FL{number}" in existing_numbers:
                        number += 1
                    flight_no = f"FL{number}"
                    number += 1

                    depart_hour = rng.randrange(0, 24)
                    depart_minute = rng.choice([0, 10, 20, 30, 40, 50])
                    duration_hours = rng.randrange(1, 13)
                    duration_minutes = rng.choice([0, 15, 30, 45])
                    arrive_total = depart_hour * 60 + depart_minute + duration_hours * 60 + duration_minutes
                    arrive_hour = (arrive_total // 60) % 24
                    arrive_minute = arrive_total % 60

                    rows.append((
                        flight_no, rng.choice(AIRLINES), source, destination,
                        f"{depart_hour:02d}:{depart_minute:02d}",
                        f"{arrive_hour:02d}:{arrive_minute:02d}",
                        f"{duration_hours}h {duration_minutes:02d}m",
                        rng.randrange(60, 181),
                        rng.randrange(4500, 50001, 250),
                        rng.choice(["On Time", "On Time", "On Time", "Delayed"])
                    ))
                    existing_numbers.add(flight_no)

        if rows:
            self.cur.executemany("""
            INSERT INTO flights(flight_no, airline, source, destination, depart_time, arrive_time, duration, seats, fare, status)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """, rows)
            self.conn.commit()

    def register_user(self, name, email, password):
        self.cur.execute(
            "INSERT INTO users(name,email,password,role,created_at) VALUES(?,?,?,?,?)",
            (name.strip(), email.strip(), password.strip(), "customer", datetime.now().strftime("%d-%m-%Y %I:%M %p"))
        )
        self.conn.commit()

    def login(self, email, password):
        self.cur.execute(
            "SELECT id,name,email,role FROM users WHERE email=? AND password=?",
            (email.strip(), password.strip())
        )
        return self.cur.fetchone()

    def search_flights(self, source, destination):
        self.cur.execute("""
        SELECT flight_no, airline, source, destination, depart_time, arrive_time, duration, seats, fare, status
        FROM flights WHERE lower(trim(source))=lower(trim(?))
        AND lower(trim(destination))=lower(trim(?))
        ORDER BY depart_time
        """, (source, destination))
        return self.cur.fetchall()

    def all_flights(self):
        self.cur.execute("""
        SELECT id, flight_no, airline, source, destination, depart_time, arrive_time, duration, seats, fare, status
        FROM flights ORDER BY id DESC
        """)
        return self.cur.fetchall()

    def add_flight(self, flight_no, airline, source, destination, depart, arrive, duration, seats, fare, status):
        self.cur.execute("""
        INSERT INTO flights(flight_no, airline, source, destination, depart_time, arrive_time, duration, seats, fare, status)
        VALUES(?,?,?,?,?,?,?,?,?,?)
        """, (flight_no, airline, source, destination, depart, arrive, duration, seats, fare, status))
        self.conn.commit()

    def delete_flight(self, flight_no):
        self.cur.execute("DELETE FROM flights WHERE flight_no=?", (flight_no,))
        self.conn.commit()

    def booked_seats(self, flight_no, travel_date):
        self.cur.execute("""
        SELECT seat FROM bookings WHERE flight_no=? AND travel_date=? AND status='Confirmed'
        """, (flight_no, travel_date))
        return [
            seat.strip()
            for row in self.cur.fetchall()
            for seat in str(row[0] or "").split(",")
            if seat.strip()
        ]

    def add_booking(self, data):
        self.cur.execute("""
        INSERT INTO bookings(
            user_email, passenger, flight_no, airline, route, travel_date, travellers,
            travel_class, fare_type, seat, price, payment_method, payment_reference, status, booked_at
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, data)
        self.conn.commit()
        return self.cur.lastrowid

    def add_payment(self, booking_id, amount, method, reference):
        self.cur.execute("""
        INSERT INTO payments(booking_id,amount,method,reference,status,paid_at)
        VALUES(?,?,?,?,?,?)
        """, (booking_id, amount, method, reference, "Success", datetime.now().strftime("%d-%m-%Y %I:%M %p")))
        self.conn.commit()

    def create_booking_with_payment(self, booking_data, method, reference):
        """Atomically create one booking and its successful payment."""
        return self.create_bookings_with_payment([booking_data], method, reference)[0]

    def create_bookings_with_payment(self, booking_items, method, reference, expected_total=None):
        """Atomically create every flight leg and its payment records."""
        if not booking_items:
            raise ValueError("At least one flight booking is required.")

        validated_items = []
        today = datetime.now().date()
        latest_date = (datetime.now() + timedelta(days=90)).date()
        for booking_data in booking_items:
            if len(booking_data) != 16:
                raise ValueError("Booking data must contain all 16 booking fields.")
            flight_no = str(booking_data[2]).strip()
            travel_date = str(booking_data[5]).strip()
            seats = [seat.strip() for seat in str(booking_data[9]).split(",") if seat.strip()]
            amount = int(booking_data[10])
            if not flight_no or not travel_date or not seats:
                raise ValueError("Flight, travel date, and at least one seat are required.")
            if str(booking_data[11]).strip() != str(method).strip():
                raise ValueError("Booking and payment methods must match.")
            if str(booking_data[12]).strip() != str(reference).strip():
                raise ValueError("Booking and payment references must match.")
            if len(seats) != len(set(seats)):
                raise ValueError("The selected seat list contains duplicates.")
            if amount <= 0:
                raise ValueError("The booking amount must be greater than zero.")
            try:
                departure_date = datetime.strptime(travel_date, "%d-%m-%Y").date()
            except ValueError as error:
                raise ValueError("Travel date must use DD-MM-YYYY.") from error
            if departure_date < today:
                raise ValueError("Cannot book a flight in the past.")
            if departure_date > latest_date:
                raise ValueError("Flights can only be booked up to 3 months ahead.")
            validated_items.append((booking_data, flight_no, travel_date, seats, amount))

        if expected_total is not None and sum(item[4] for item in validated_items) != int(expected_total):
            raise ValueError("Booking leg amounts must add up to the final ticket amount.")

        try:
            self.conn.execute("BEGIN IMMEDIATE")
            booking_ids = []
            for booking_data, flight_no, travel_date, seats, amount in validated_items:
                self.cur.execute(
                    """SELECT seat FROM bookings
                       WHERE flight_no=? AND travel_date=? AND status='Confirmed'""",
                    (flight_no, travel_date)
                )
                booked = {
                    seat.strip()
                    for row in self.cur.fetchall()
                    for seat in str(row[0] or "").split(",")
                    if seat.strip()
                }
                conflicts = booked.intersection(seats)
                if conflicts:
                    raise ValueError(f"Seat(s) already booked: {', '.join(sorted(conflicts))}")

                self.cur.execute("""
                    INSERT INTO bookings(
                        user_email, passenger, flight_no, airline, route, travel_date, travellers,
                        travel_class, fare_type, seat, price, payment_method, payment_reference,
                        status, booked_at, passenger_details
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, booking_data)
                booking_id = self.cur.lastrowid
                booking_ids.append(booking_id)
                self.cur.execute("""
                    INSERT INTO payments(booking_id,amount,method,reference,status,paid_at)
                    VALUES(?,?,?,?,?,?)
                """, (
                    booking_id, amount, method, reference, "Success",
                    datetime.now().strftime("%d-%m-%Y %I:%M %p")
                ))
            self.conn.commit()
            return booking_ids
        except Exception:
            self.conn.rollback()
            raise

    def user_bookings(self, email):
        self.cur.execute("""
        SELECT id,flight_no,airline,route,travel_date,travellers,travel_class,fare_type,seat,price,status,booked_at,
               cancellation_id,cancellation_reason
        FROM bookings WHERE user_email=? ORDER BY id DESC
        """, (email,))
        return self.cur.fetchall()

    def cancel_booking(self, booking_id, email, reason=""):
        return self._cancel_booking_with_refund(booking_id, reason, email)

    def all_bookings(self):
        self.cur.execute("""
        SELECT id,passenger,user_email,flight_no,airline,route,travel_date,seat,price,status,booked_at,
               travellers,travel_class,fare_type,payment_method,payment_reference,passenger_details
        FROM bookings ORDER BY id DESC
        """)
        return self.cur.fetchall()

    def stats(self):
        self.cur.execute("SELECT COUNT(*) FROM flights")
        flights = self.cur.fetchone()[0]

        self.cur.execute("SELECT COUNT(*) FROM bookings")
        bookings = self.cur.fetchone()[0]

        self.cur.execute("SELECT IFNULL(SUM(price),0) FROM bookings WHERE status='Confirmed'")
        revenue = self.cur.fetchone()[0]

        self.cur.execute("SELECT COUNT(*) FROM users WHERE role='customer'")
        users = self.cur.fetchone()[0]

        return flights, bookings, revenue, users

    # ---------------- ADMIN / REPORTING HELPERS ----------------

    def admin_stats(self):
        self.cur.execute("SELECT COUNT(*) FROM flights")
        flights = self.cur.fetchone()[0]
        self.cur.execute("SELECT COUNT(*) FROM users WHERE role='customer'")
        users = self.cur.fetchone()[0]
        self.cur.execute("SELECT COUNT(*) FROM bookings")
        bookings = self.cur.fetchone()[0]
        self.cur.execute("SELECT IFNULL(SUM(price),0) FROM bookings WHERE status='Confirmed'")
        revenue = self.cur.fetchone()[0]
        self.cur.execute("SELECT COUNT(*) FROM bookings WHERE status='Cancelled'")
        cancelled = self.cur.fetchone()[0]
        return flights, users, bookings, revenue, cancelled

    def all_users(self):
        self.cur.execute("""
            SELECT id,name,email,created_at,role
            FROM users WHERE role='customer' ORDER BY id DESC
        """)
        return self.cur.fetchall()

    def all_payments(self):
        self.cur.execute("""
            SELECT id,booking_id,amount,method,reference,status,paid_at
            FROM payments ORDER BY id DESC
        """)
        return self.cur.fetchall()

    def update_flight(self, flight_no, airline, source, destination,
                      depart_time, arrive_time, duration, seats, fare, status):
        self.cur.execute("""
            UPDATE flights
            SET airline=?, source=?, destination=?, depart_time=?, arrive_time=?,
                duration=?, seats=?, fare=?, status=?
            WHERE flight_no=?
        """, (airline, source, destination, depart_time, arrive_time,
              duration, int(seats), int(fare), status, flight_no))
        self.conn.commit()
        return self.cur.rowcount

    def admin_cancel_booking(self, booking_id, reason=""):
        return self._cancel_booking_with_refund(booking_id, reason)

    def _cancel_booking_with_refund(self, booking_id, reason, email=None):
        cancellation_id = f"CNL-{int(booking_id):06d}"
        condition = "id=? AND lower(status)!='cancelled'"
        parameters = [cancellation_id, reason.strip(), booking_id]
        if email is not None:
            condition += " AND user_email=?"
            parameters.append(email)

        try:
            self.conn.execute("BEGIN IMMEDIATE")
            self.cur.execute(
                f"""UPDATE bookings
                    SET status='Cancelled', cancellation_id=?, cancellation_reason=?
                    WHERE {condition}""",
                parameters
            )
            changed = self.cur.rowcount
            if changed:
                self._create_pending_refund_for_cancelled_booking(booking_id)
            self.conn.commit()
            return changed, cancellation_id if changed else None
        except Exception:
            self.conn.rollback()
            raise

    def all_refunds(self):
        self.cur.execute("""
            SELECT r.id,r.booking_id,r.amount,r.status,r.processed_at,
                   b.passenger,b.flight_no
            FROM refunds r
            LEFT JOIN bookings b ON b.id=r.booking_id
            ORDER BY r.id DESC
        """)
        return self.cur.fetchall()

    def _create_pending_refund_for_cancelled_booking(self, booking_id):
        self.cur.execute("SELECT price,status FROM bookings WHERE id=?", (booking_id,))
        booking = self.cur.fetchone()
        if not booking or str(booking[1]).strip().lower() != "cancelled":
            return False

        amount = int(booking[0] or 0)
        if amount <= 0:
            return False
        self.cur.execute(
            """SELECT 1 FROM refunds
               WHERE booking_id=? AND lower(status)!='rejected' LIMIT 1""",
            (booking_id,)
        )
        if self.cur.fetchone():
            return False
        self.cur.execute("""
            INSERT INTO refunds(booking_id,amount,status,processed_at)
            VALUES(?,?,?,?)
        """, (booking_id, amount, "Pending", None))
        return True

    def create_refund_request(self, booking_id, amount):
        requested_amount = int(amount)
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            self.cur.execute("SELECT price,status FROM bookings WHERE id=?", (booking_id,))
            booking = self.cur.fetchone()
            if not booking or str(booking[1]).strip().lower() != "cancelled":
                self.conn.rollback()
                return False
            if requested_amount != int(booking[0] or 0):
                raise ValueError("Refund amount must match the cancelled booking amount.")
            created = self._create_pending_refund_for_cancelled_booking(booking_id)
            self.conn.commit()
            return created
        except Exception:
            self.conn.rollback()
            raise

    def update_refund_status(self, refund_id, status):
        processed_at = datetime.now().strftime("%d-%m-%Y %I:%M %p") if status == "Processed" else None
        self.cur.execute(
            "UPDATE refunds SET status=?, processed_at=? WHERE id=?",
            (status, processed_at, refund_id)
        )
        self.conn.commit()
        return self.cur.rowcount

    def change_password(self, email, old_password, new_password):
        self.cur.execute("""
            UPDATE users SET password=?
            WHERE email=? AND password=?
        """, (new_password.strip(), email.strip(), old_password.strip()))
        self.conn.commit()
        return self.cur.rowcount

    def report_summary(self):
        self.cur.execute("""
            SELECT COUNT(*) FROM bookings
            WHERE date(substr(booked_at,7,4)||'-'||substr(booked_at,4,2)||'-'||substr(booked_at,1,2))
                  = date('now','localtime')
        """)
        daily = self.cur.fetchone()[0]

        self.cur.execute("""
            SELECT COUNT(*) FROM bookings
            WHERE substr(booked_at,4,7)=strftime('%m-%Y','now','localtime')
        """)
        monthly = self.cur.fetchone()[0]

        self.cur.execute("SELECT IFNULL(SUM(price),0) FROM bookings WHERE status='Confirmed'")
        revenue = self.cur.fetchone()[0]

        self.cur.execute("""
            SELECT flight_no,COUNT(*) AS total
            FROM bookings GROUP BY flight_no
            ORDER BY total DESC LIMIT 5
        """)
        most_booked = self.cur.fetchall()

        self.cur.execute("""
            SELECT SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END), COUNT(*)
            FROM bookings
        """)
        cancelled,total = self.cur.fetchone()
        cancelled = cancelled or 0
        rate = round((cancelled/total)*100,1) if total else 0
        return daily,monthly,revenue,most_booked,cancelled,rate

    def close(self):
        self.conn.close()