from app import create_app
from models import db

# Gunicorn entry point
app = create_app()

# Ensure tables exist on startup (safe: does not drop data).
# On Render this connects to the persistent PostgreSQL from DATABASE_URL,
# so redeploys reuse the SAME database instead of creating a fresh one.
with app.app_context():
    try:
        uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        dialect = uri.split('://', 1)[0] if '://' in uri else 'unknown'
        # Log dialect + host only; never log credentials.
        host = uri.split('@', 1)[-1].split('/', 1)[0] if '@' in uri else 'local-file'
        print(f"[startup] DB dialect={dialect} host={host} — running create_all (no data deleted)")
    except Exception:
        pass
    db.create_all()
