from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from models.product import Product
from models.category import Category
from models.banner import Banner

bp = Blueprint('products', __name__)

@bp.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    categories = Category.query.filter_by(parent_id=None).all()
    banners = Banner.visible()
    return render_template('home.html', categories=categories, banners=banners)

@bp.route('/products/<int:subcategory_id>')
def products_by_subcategory(subcategory_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    subcategory = Category.query.get_or_404(subcategory_id)
    siblings = Category.query.filter_by(parent_id=subcategory.parent_id).all()
    products = Product.query.filter_by(subcategory_id=subcategory_id).all()
    return render_template('products.html', subcategory=subcategory, siblings=siblings, products=products)

@bp.route('/product/<int:id>')
def product_detail(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    product = Product.query.get_or_404(id)
    return render_template('product_detail.html', product=product)

@bp.route('/api/products/search')
def search_api():
    q = request.args.get('q', '').lower()
    products = Product.query.filter(Product.name.ilike(f'%{q}%')).all()
    result = []
    for p in products:
        result.append({
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'unit': p.unit,
            'category': p.category.name if p.category else '',
            'image_url': p.image_url
        })
    return jsonify(result)

@bp.route('/search')
def search_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    q = request.args.get('q', '')
    products = []
    if q:
        products = Product.query.filter(Product.name.ilike(f'%{q}%')).all()
    return render_template('search.html', products=products, q=q)
