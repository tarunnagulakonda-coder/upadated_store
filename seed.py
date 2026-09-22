import os
from werkzeug.security import generate_password_hash
from app import create_app
from models import db
from models.user import User
from models.category import Category
from models.product import Product
from models.cart import Cart, CartItem
from models.order import Order, OrderItem
from models.admin import Admin
from datetime import datetime

app = create_app()


def _ensure_admin():
    """Create the admin row from env only if no admin exists. Never deletes."""
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin')
    if Admin.query.filter_by(username=admin_username).first():
        return
    db.session.add(Admin(
        username=admin_username,
        password_hash=generate_password_hash(admin_password),
    ))
    db.session.commit()

def seed_data():
    with app.app_context():
        # SAFETY: seed.py must NEVER wipe production data.
        # - Default behaviour is idempotent: only insert demo data when the
        #   database is empty, and never call drop_all.
        # - drop_all is only allowed for local development when the operator
        #   explicitly sets ALLOW_SEED_RESET=true. It is refused whenever
        #   DATABASE_URL points at Postgres, even with the flag, unless
        #   ALLOW_SEED_RESET=force is set (manual recovery only).
        raw_url = os.environ.get('DATABASE_URL', '')
        is_postgres = raw_url.startswith(('postgres://', 'postgresql://', 'postgresql+pg8000://'))
        reset_flag = os.environ.get('ALLOW_SEED_RESET', 'false').lower()
        if reset_flag == 'true' and is_postgres:
            print("Refusing drop_all on Postgres with ALLOW_SEED_RESET=true. Use ALLOW_SEED_RESET=force for manual recovery only.")
            db.create_all()
            return
        if reset_flag not in ('true', 'force'):
            # Idempotent seed: safe to run on Render without deleting anything.
            db.create_all()
            from models.category import Category as _Cat
            from models.product import Product as _Prod
            if _Cat.query.first() or _Prod.query.first():
                print("Database already has data — seed skipped (no rows deleted).")
                _ensure_admin()
                return
        else:
            # Explicit local reset requested (ALLOW_SEED_RESET=true locally,
            # or =force on Postgres for manual recovery).
            db.drop_all()
            db.create_all()

        # Admin (idempotent: never duplicate, never delete)
        _ensure_admin()

        # Categories hierarchy (skip if already seeded)
        hierarchy = {
            "Fresh": {"icon": "🥬", "subs": ["Vegetables", "Fruits"]},
            "Dairy & Eggs": {"icon": "🥛", "subs": ["Milk", "Curd", "Butter", "Paneer"]},
            "Snacks": {"icon": "🍪", "subs": ["Biscuits", "Chips", "Namkeen"]},
            "Beverages": {"icon": "🧃", "subs": ["Soft Drinks", "Juices", "Water"]},
            "Household": {"icon": "🧽", "subs": []},
            "Personal Care": {"icon": "🧼", "subs": []}
        }
        
        cat_map = {}
        subcat_map = {}
        for parent_name, data in hierarchy.items():
            parent = Category(name=parent_name, icon=data["icon"])
            db.session.add(parent)
            db.session.flush() # Get ID
            cat_map[parent_name] = parent
            
            for sub_name in data["subs"]:
                sub = Category(name=sub_name, icon="➡️", parent_id=parent.id)
                db.session.add(sub)
                db.session.flush()
                subcat_map[sub_name] = sub

        db.session.commit()
        
        # Products
        demo_products = [
            # Vegetables
            {"name": "Tomato", "price": 45, "unit": "1 kg", "sub": "Vegetables", "parent": "Fresh"},
            {"name": "Potato", "price": 40, "unit": "1 kg", "sub": "Vegetables", "parent": "Fresh"},
            {"name": "Onion", "price": 50, "unit": "1 kg", "sub": "Vegetables", "parent": "Fresh"},
            {"name": "Carrot", "price": 60, "unit": "1 kg", "sub": "Vegetables", "parent": "Fresh"},
            {"name": "Brinjal", "price": 50, "unit": "1 kg", "sub": "Vegetables", "parent": "Fresh"},
            {"name": "Lady Finger", "price": 55, "unit": "1 kg", "sub": "Vegetables", "parent": "Fresh"},
            {"name": "Cabbage", "price": 40, "unit": "1 piece", "sub": "Vegetables", "parent": "Fresh"},
            {"name": "Cauliflower", "price": 50, "unit": "1 piece", "sub": "Vegetables", "parent": "Fresh"},
            
            # Fruits
            {"name": "Banana", "price": 60, "unit": "1 Dozen", "sub": "Fruits", "parent": "Fresh"},
            {"name": "Apple", "price": 150, "unit": "1 kg", "sub": "Fruits", "parent": "Fresh"},
            {"name": "Orange", "price": 80, "unit": "1 kg", "sub": "Fruits", "parent": "Fresh"},
            {"name": "Mango", "price": 100, "unit": "1 kg", "sub": "Fruits", "parent": "Fresh"},
            
            # Dairy
            {"name": "Milk", "price": 30, "unit": "500 ml", "sub": "Milk", "parent": "Dairy & Eggs"},
            {"name": "Curd", "price": 40, "unit": "500 g", "sub": "Curd", "parent": "Dairy & Eggs"},
            {"name": "Butter", "price": 55, "unit": "100 g", "sub": "Butter", "parent": "Dairy & Eggs"},
            {"name": "Paneer", "price": 80, "unit": "200 g", "sub": "Paneer", "parent": "Dairy & Eggs"},

            # Snacks
            {"name": "Biscuits", "price": 20, "unit": "1 pack", "sub": "Biscuits", "parent": "Snacks"},
            {"name": "Chips", "price": 10, "unit": "1 pack", "sub": "Chips", "parent": "Snacks"},
            {"name": "Namkeen", "price": 50, "unit": "200 g", "sub": "Namkeen", "parent": "Snacks"},

            # Beverages
            {"name": "Soft Drinks", "price": 40, "unit": "750 ml", "sub": "Soft Drinks", "parent": "Beverages"},
            {"name": "Juices", "price": 110, "unit": "1 L", "sub": "Juices", "parent": "Beverages"},
            {"name": "Water", "price": 20, "unit": "1 L", "sub": "Water", "parent": "Beverages"}
        ]
        
        for p in demo_products:
            parent_cat = cat_map[p['parent']]
            sub_cat = subcat_map.get(p['sub'])
            prod = Product(
                name=p['name'],
                category_id=parent_cat.id,
                subcategory_id=sub_cat.id if sub_cat else None,
                price=p['price'],
                unit=p['unit'],
                stock="Available",
                description="Fresh and local " + p['name'],
                image_url=None
            )
            db.session.add(prod)
            
        db.session.commit()
        print("Database seeded with hierarchical categories and products!")

if __name__ == '__main__':
    seed_data()

