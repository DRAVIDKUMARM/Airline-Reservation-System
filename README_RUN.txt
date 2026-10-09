SkyBook Pro — Run Guide
========================

1. Install dependencies (one time):
     py -m pip install -r requirements.txt

2. Run the app:
     py main.py

3. On first launch, main.py calls database.init_db(), which creates
   skybook_full.db in this folder and seeds it with:
     - One admin account
     - Five demo flights

DEFAULT LOGINS
--------------
Admin (use the "Admin Login" link on the login screen):
     email:    admin@gmail.com
     password: admin123

Customer:
     Register a new account from the login screen — there is no
     seeded customer account, since real customer accounts should be
     created through Register.

FILES
-----
main.py       - app window, navigation, and every screen (customer + admin)
theme.py      - single color/font palette used by every screen
ui.py         - reusable widgets (buttons, cards, stat tiles, seat grid, etc.)
database.py   - SQLite schema + all data access functions
utils.py      - password hashing, validation, booking refs, PDF ticket export
requirements.txt

NOTES
-----
- Downloaded boarding-pass PDFs are saved into the tickets/ folder.
- Booking a seat is done in a single DB transaction, so two customers
  can't accidentally book the same seat at the same time.
- Admin can add/delete flights from Manage Flights, and cancel any
  booking from All Bookings.
