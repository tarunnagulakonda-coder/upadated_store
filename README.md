# Simple Kirana E-Commerce Website

## Technologies
- HTML, CSS, JavaScript (Vanilla)
- Python Flask
- REST API
- PostgreSQL / SQLite (configured via `.env`)
- SQLAlchemy (pg8000 driver)

## Features
- Fully dynamic cart system stored in the database.
- Checkout flow generates correct WhatsApp Click-to-Chat URLs.
- Admin dashboard for adding products, modifying product prices, managing categories, and tracking orders.
- Order price freezing ensuring that when an admin modifies a price, old orders stay at their purchase amount.

## Installation

1. Install Python 3
2. Initialize python virtual environment
   ```bash
   python -m venv venv
   ```
3. Activate virtual environment
   ```bash
   venv\Scripts\activate
   ```
4. Install requirements
   ```bash
   pip install -r requirements.txt
   ```
5. Configure `.env` using `.env.example`
6. Seed database
   ```bash
   python seed.py
   ```
7. Start server
   ```bash
   python app.py
   ```
8. Website will be available at `http://127.0.0.1:5000`
9. Admin Portal available at `/admin/login` (Default logins via `.env`).
