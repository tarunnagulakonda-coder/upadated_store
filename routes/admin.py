import os
import time
from datetime import datetime
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from models import db
from models.admin import Admin
from models.user import User, UserLogin
from models.category import Category
from models.product import Product
from models.order import Order
from models.banner import Banner

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

# ==============================
# BANNERS (promotional carousel)
# ==============================
ALLOWED_BANNER_EXTS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def _banner_upload_dir():
    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'banners')
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def _save_banner_image(file):
    """Validate, optimize and save an uploaded banner image.
    Returns the path relative to the static folder, or None."""
    if not file or not file.filename:
        return None
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_BANNER_EXTS:
        return None
    filename = f"{int(time.time())}_{secure_filename(file.filename)}"
    filepath = os.path.join(_banner_upload_dir(), filename)
    file.save(filepath)
    # Optimize for fast loading: downscale wide images, compress
    try:
        from PIL import Image
        img = Image.open(filepath)
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
            filepath = os.path.splitext(filepath)[0] + '.jpg'
            filename = os.path.splitext(filename)[0] + '.jpg'
        if img.width > 900:
            img = img.resize((900, int(img.height * 900 / img.width)), Image.LANCZOS)
        img.save(filepath, optimize=True, quality=70)
    except Exception:
        pass  # keep the original file if optimization fails
    return f"uploads/banners/{filename}"

def _delete_banner_image(rel_path):
    if not rel_path:
        return
    try:
        full = os.path.join(current_app.static_folder, rel_path)
        # Safety: only delete files inside the banners folder
        if os.path.isfile(full) and 'banners' in rel_path.replace('\\', '/'):
            os.remove(full)
    except Exception:
        pass

def _parse_date(value):
    value = (value or '').strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None

def _read_banner_form(banner):
    banner.title = (request.form.get('title') or '').strip()
    banner.description = (request.form.get('description') or '').strip() or None
    banner.offer_text = (request.form.get('offer_text') or '').strip() or None
    banner.button_text = (request.form.get('button_text') or '').strip() or None
    banner.redirect_url = (request.form.get('redirect_url') or '').strip() or None
    status = request.form.get('status')
    banner.status = status if status in ('Active', 'Inactive') else 'Active'
    try:
        banner.display_order = int(request.form.get('display_order') or 0)
    except (TypeError, ValueError):
        banner.display_order = 0
    banner.start_date = _parse_date(request.form.get('start_date'))
    banner.end_date = _parse_date(request.form.get('end_date'))

@bp.route('/banners')
def banners():
    if not is_admin(): return redirect(url_for('admin.login'))
    all_banners = Banner.query.order_by(Banner.display_order.asc(), Banner.id.asc()).all()
    return render_template('admin/banners.html', banners=all_banners)

@bp.route('/banners/add', methods=['POST'])
def add_banner():
    if not is_admin(): return redirect(url_for('admin.login'))
    title = (request.form.get('title') or '').strip()
    if not title:
        flash("Banner title is required.", 'error')
        return redirect(url_for('admin.banners'))
    banner = Banner(title=title)
    _read_banner_form(banner)
    banner.image = _save_banner_image(request.files.get('image'))
    db.session.add(banner)
    db.session.commit()
    flash("Banner added successfully.", 'success')
    return redirect(url_for('admin.banners'))

@bp.route('/banners/<int:id>/edit', methods=['GET', 'POST'])
def edit_banner(id):
    if not is_admin(): return redirect(url_for('admin.login'))
    banner = Banner.query.get_or_404(id)
    if request.method == 'POST':
        _read_banner_form(banner)
        if not banner.title:
            flash("Banner title is required.", 'error')
            return render_template('admin/edit_banner.html', banner=banner)
        new_image = _save_banner_image(request.files.get('image'))
        if new_image:
            _delete_banner_image(banner.image)
            banner.image = new_image
        db.session.commit()
        flash("Banner updated successfully.", 'success')
        return redirect(url_for('admin.banners'))
    return render_template('admin/edit_banner.html', banner=banner)

@bp.route('/banners/<int:id>/toggle', methods=['POST'])
def toggle_banner(id):
    if not is_admin(): return redirect(url_for('admin.login'))
    banner = Banner.query.get_or_404(id)
    banner.status = 'Inactive' if banner.status == 'Active' else 'Active'
    db.session.commit()
    flash(f"Banner '{banner.title}' is now {banner.status}.", 'success')
    return redirect(url_for('admin.banners'))

@bp.route('/banners/<int:id>/delete', methods=['POST'])
def delete_banner(id):
    if not is_admin(): return redirect(url_for('admin.login'))
    banner = Banner.query.get_or_404(id)
    _delete_banner_image(banner.image)
    db.session.delete(banner)
    db.session.commit()
    flash("Banner deleted.", 'success')
    return redirect(url_for('admin.banners'))

# ==============================
# USERS / CUSTOMERS
# ==============================
@bp.route('/users')
def users():
    if not is_admin(): return redirect(url_for('admin.login'))
    import re as _re
    q = (request.args.get('q') or '').strip()
    query = User.query
    if q:
        digits = _re.sub(r'\D', '', q)
        filters = [User.name.ilike(f'%{q}%')]
        if digits:
            filters.append(User.mobile.ilike(f'%{digits}%'))
        query = query.filter(db.or_(*filters))
    all_users = query.order_by(User.id.desc()).all()
    total = User.query.count()
    recent_logins = UserLogin.query.order_by(UserLogin.login_at.desc()).limit(10).all()
    return render_template('admin/users.html', users=all_users, total=total, q=q,
                           recent_logins=recent_logins)
