import os
import ssl
from dotenv import load_dotenv

load_dotenv()


def _normalize_db_url(raw: str) -> str:
    """Normalize DATABASE_URL for SQLAlchemy + pg8000.

    - Render may provide postgres:// (legacy) or postgresql://.
    - Local dev may use sqlite.
    - Never add credentials here; URL comes from env only.
    """
    db_url = (raw or '').strip().strip('"').strip("'")
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql+pg8000://', 1)
    elif db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    return db_url


def _needs_ssl(db_url: str) -> bool:
    """Render Postgres external URLs need SSL; internal/Localhost do not."""
    if not db_url.startswith('postgresql+pg8000://'):
        return False
    # On Render, external hosts end with .onrender.com / .render.com.
    # Internal hosts (e.g. dpg-xxx-a) work with or without SSL; forcing
    # SSL on is safe for Render but breaks plain local Postgres, so only
    # enable automatically when running on Render with an external host.
    if os.environ.get('RENDER') == 'true':
        low = db_url.lower()
        if 'onrender.com' in low or 'render.com' in low:
            return True
    return False


_RAW_DB_URL = _normalize_db_url(os.environ.get('DATABASE_URL', ''))
_ON_RENDER = os.environ.get('RENDER') == 'true' or bool(os.environ.get('RENDER_SERVICE_NAME'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret')
    if not _RAW_DB_URL:
        if _ON_RENDER:
            # Fail fast on Render instead of silently using an ephemeral
            # SQLite file that is wiped on every deploy (the data-loss bug).
            raise RuntimeError(
                'DATABASE_URL is not set. Attach a Render PostgreSQL database '
                'to this service (see render.yaml) so data persists across deploys.'
            )
        # Local development fallback only. Never used on Render.
        _RAW_DB_URL = 'sqlite:///kirana.db'
    if _ON_RENDER and _RAW_DB_URL.startswith('sqlite'):
        # Someone set DATABASE_URL=sqlite on Render (or a .env leaked in).
        # Refuse: SQLite on Render is ephemeral and wipes data every deploy.
        raise RuntimeError(
            'SQLite is not allowed on Render (ephemeral filesystem wipes data). '
            'Set DATABASE_URL to the Render PostgreSQL connection string.'
        )
    SQLALCHEMY_DATABASE_URI = _RAW_DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Keep pooled Postgres connections alive across Render deploys/restarts.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    if _needs_ssl(_RAW_DB_URL):
        SQLALCHEMY_ENGINE_OPTIONS['connect_args'] = {
            'ssl_context': ssl.create_default_context(),
        }

    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
    SHOP_WHATSAPP_NUMBER = os.environ.get('SHOP_WHATSAPP_NUMBER', '')
    MIN_ORDER_AMOUNT = int(os.environ.get('MIN_ORDER_AMOUNT', 100))
