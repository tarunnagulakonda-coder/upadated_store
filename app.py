import os
from flask import Flask
from config import Config
from models import db

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

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True, port=5000)
