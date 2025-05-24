# IT Inventory System

This is a lightweight web-based IT inventory management tool built with Flask.

## Features

- User login system (admin only)
- Add, edit, delete, and search IT inventory
- Track device type, brand, model, serial, location, installation date, and condition
- Request management with status tracking
- SQLite database backend
- Clean and responsive UI

## How to Run

1. Create virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```

2. Start the server:
    ```bash
    python app.py
    ```

3. Open your browser at [http://localhost:5000](http://localhost:5000)

## Default Credentials

- **Username**: admin
- **Password**: admin

## Notes

- Requires Python 3.10+
- Database is stored in `inventory.db` (SQLite)

---

Made with ❤️ for internal IT tracking.