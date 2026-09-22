import os
from flask import Flask
from config import Config
from models import db

def _ensure_schema(app):
    """Lightweight idempotent migration for existing databases.

    db.create_all() creates new tables but never alters existing ones,
    so new columns/indexes on old databases are applied here.
    Safe to run on every startup (SQLite + Postgres).
    """
    with app.app_context():
        from sqlalchemy import text, inspect
        db.create_all()  # safe: creates missing tables, never alters/drops
        insp = inspect(db.engine)
        if 'users' not in insp.get_table_names():
            return
        cols = [c['name'] for c in insp.get_columns('users')]
        with db.engine.begin() as conn:
            if 'last_login' not in cols:
                conn.execute(text('ALTER TABLE users ADD COLUMN last_login TIMESTAMP'))
            if 'created_at' not in cols:
                conn.execute(text('ALTER TABLE users ADD COLUMN created_at TIMESTAMP'))
            conn.execute(text('UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL'))
            try:
                conn.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_users_mobile_unique ON users (mobile)'))
            except Exception:
                pass  # pre-existing duplicate numbers: app-level checks still prevent new ones

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_class)

    # Simple fallback secret key
    if not app.secret_key:
        app.secret_key = 'kirana_secret_key'

    db.init_app(app)

    # Register blueprints
    from routes.auth import bp as auth_bp
    from routes.products import bp as products_bp
    from routes.categories import bp as categories_bp
    from routes.cart import bp as cart_bp
    from routes.orders import bp as orders_bp
    from routes.profile import bp as profile_bp
    from routes.admin import bp as admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    _ensure_schema(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True, port=5000)
