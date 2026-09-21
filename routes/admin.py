import os
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db
from models.admin import Admin
from models.category import Category
from models.product import Product
from models.order import Order

bp = Blueprint('admin', __name__)

def is_admin():
    return session.get('is_admin')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['is_admin'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            flash("Invalid admin credentials.", 'error')
            
    return render_template('admin/login.html')

@bp.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
def dashboard():
    if not is_admin(): return redirect(url_for('admin.login'))
    return render_template('admin/dashboard.html')

@bp.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if not is_admin(): return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        category_id = request.form.get('category_id')
        subcategory_id = request.form.get('subcategory_id') or None
        price = request.form.get('price')
        unit = request.form.get('unit')
        stock = request.form.get('stock', 'Available')
        expiry_date = request.form.get('expiry_date')
        description = request.form.get('description')
        
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                # Save just the name for simple relative referencing, directory must exist
                upload_dir = 'static/uploads'
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                file.save(os.path.join(upload_dir, filename))
                image_url = filename
                
        prod = Product(
            name=name, category_id=category_id, subcategory_id=subcategory_id,
            price=price, unit=unit, stock=stock,
            expiry_date=expiry_date, description=description, image_url=image_url
        )
        db.session.add(prod)
        db.session.commit()
        flash("Product added successfully.", 'success')
        return redirect(url_for('admin.edit_products'))

    categories = Category.query.all()
    return render_template('admin/add_product.html', categories=categories)

@bp.route('/edit_products', methods=['GET'])
def edit_products():
    if not is_admin(): return redirect(url_for('admin.login'))
    products = Product.query.order_by(Product.name).all()
    return render_template('admin/edit_products.html', products=products)

@bp.route('/edit_products/<int:id>', methods=['POST'])
def update_product_price(id):
    if not is_admin(): return redirect(url_for('admin.login'))
    prod = Product.query.get_or_404(id)
    prod.price = request.form.get('price')
    db.session.commit()
    flash(f"Price updated for {prod.name}.", 'success')
    return redirect(url_for('admin.edit_products'))

@bp.route('/categories', methods=['GET', 'POST'])
def categories():
    if not is_admin(): return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        icon = request.form.get('icon')
        parent_id = request.form.get('parent_id') or None
        
        if name:
            new_cat = Category(name=name, icon=icon, parent_id=parent_id)
            db.session.add(new_cat)
            db.session.commit()
            flash("Category added successfully.", 'success')
            
    categories = Category.query.filter_by(parent_id=None).all()
    subcategories = Category.query.filter(Category.parent_id != None).all()
    return render_template('admin/categories.html', categories=categories, subcategories=subcategories)

@bp.route('/categories/<int:id>/edit', methods=['POST'])
def edit_category(id):
    if not is_admin(): return redirect(url_for('admin.login'))
    cat = Category.query.get_or_404(id)
    cat.name = request.form.get('name')
    db.session.commit()
    flash("Category updated.", 'success')
    return redirect(url_for('admin.categories'))
    
@bp.route('/categories/<int:id>/delete', methods=['POST'])
def delete_category(id):
    if not is_admin(): return redirect(url_for('admin.login'))
    cat = Category.query.get_or_404(id)
    if cat.products:
        flash("Cannot delete this category because products are assigned to it. Move the products to another category first.", 'error')
    else:
        db.session.delete(cat)
        db.session.commit()
        flash("Category deleted.", 'success')
    return redirect(url_for('admin.categories'))

@bp.route('/orders')
def orders():
    if not is_admin(): return redirect(url_for('admin.login'))
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@bp.route('/orders/<int:id>/status', methods=['POST'])
def update_order_status(id):
    if not is_admin(): return redirect(url_for('admin.login'))
    order = Order.query.get_or_404(id)
    order.status = request.form.get('status')
    db.session.commit()
    flash(f"Order #{order.id} status updated to {order.status}.", 'success')
    return redirect(url_for('admin.orders'))
