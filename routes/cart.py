from flask import Blueprint, jsonify, request, session, render_template, redirect, url_for, current_app
from models import db
from models.user import User
from models.cart import Cart, CartItem
from models.product import Product

bp = Blueprint('cart', __name__)

@bp.route('/cart', methods=['GET'])
def view_cart():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('cart.html')

@bp.route('/api/cart/count', methods=['GET'])
def get_cart_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})
    cart = Cart.query.filter_by(user_id=session['user_id']).first()
    count = sum(item.quantity for item in cart.items) if cart else 0
    return jsonify({'count': count})

@bp.route('/api/cart', methods=['GET'])
def get_cart():
    if 'user_id' not in session:
        return jsonify({'items': []})
    
    cart = Cart.query.filter_by(user_id=session['user_id']).first()
    if not cart:
        return jsonify({'items': []})
        
    items = []
    for item in cart.items:
        items.append({
            'cart_item_id': item.id,
            'name': item.product.name,
            'price': item.product.price,
            'quantity': item.quantity,
            'requirement': item.requirement
        })
    return jsonify({'items': items})

@bp.route('/api/cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
        
    data = request.json
    user_id = session['user_id']
    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))
    requirement = data.get('requirement', '')
    
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()
        
    existing_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if existing_item:
        existing_item.quantity += quantity
        if requirement:
            existing_item.requirement = requirement
    else:
        new_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity, requirement=requirement)
        db.session.add(new_item)
        
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/checkout', methods=['GET'])
def checkout_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    cart = Cart.query.filter_by(user_id=session['user_id']).first()
    if not cart or not cart.items:
        return redirect(url_for('cart.view_cart'))
        
    total_amount = sum(item.product.price * item.quantity for item in cart.items)
    min_amount = current_app.config.get('MIN_ORDER_AMOUNT', 100)
    if total_amount < min_amount:
        return redirect(url_for('cart.view_cart'))
        
    user = User.query.get(session['user_id'])
    return render_template('checkout.html', user=user, total=total_amount)

@bp.route('/api/cart/<int:item_id>', methods=['PUT'])
def update_cart_item(item_id):
    if 'user_id' not in session:
        return jsonify({'success': False})
    
    item = CartItem.query.get_or_404(item_id)
    action = request.json.get('action')
    
    if action == 'inc':
        item.quantity += 1
    elif action == 'dec':
        if item.quantity > 1:
            item.quantity -= 1
        else:
            db.session.delete(item)
        
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/cart/<int:item_id>', methods=['DELETE'])
def remove_cart_item(item_id):
    if 'user_id' not in session:
        return jsonify({'success': False})
        
    item = CartItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True})
