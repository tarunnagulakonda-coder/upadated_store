import re
from datetime import datetime
from models import db


def normalize_mobile(value):
    """Normalize an Indian mobile number to plain 10 digits.

    Accepts '98765 43210', '+91-9876543210', '919876543210', '09876543210'.
    Returns the 10-digit string, or None if invalid.
    """
    if not value:
        return None
    digits = re.sub(r'\D', '', str(value))
    if not digits:
        return None
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]
    if re.fullmatch(r'\d{10}', digits or ''):
        return digits
    return None


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    area = db.Column(db.String(100), nullable=False)
    # Unique customer identifier (plain 10 digits, see normalize_mobile)
    mobile = db.Column(db.String(15), nullable=False)
    house_no = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    def record_login(self):
        """Update last login and append to login history. No duplicates created."""
        now = datetime.utcnow()
        self.last_login = now
        db.session.add(UserLogin(user_id=self.id, login_at=now))


class UserLogin(db.Model):
    """Login history: one row per successful customer login."""
    __tablename__ = 'user_logins'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    login_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('logins', lazy='dynamic'))
