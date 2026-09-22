import os
import urllib.parse
from flask import Blueprint, jsonify, session, current_app
from models import db
from models.user import User
from models.cart import Cart, CartItem
from models.order import Order, OrderItem

bp = Blueprint('orders', __name__)

@bp.route('/api/orders', methods=['POST'])
def place_order():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
        
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    cart = Cart.query.filter_by(user_id=user_id).first()
    
    if not cart or not cart.items:
        return jsonify({'success': False, 'message': 'Cart is empty'})
        
    total_amount = sum(item.product.price * item.quantity for item in cart.items)
    min_amount = current_app.config.get('MIN_ORDER_AMOUNT', 100)
    if total_amount < min_amount:
        return jsonify({'success': False, 'message': f'Minimum order amount is ₹{min_amount} to continue'})
    
    # Store full delivery address
    address = f"{user.house_no}, {user.area}"
    
    # Create order
    order = Order(user_id=user_id, total_amount=total_amount, status='Pending', delivery_address=address)
    db.session.add(order)
    db.session.flush() # Get order ID before commit
    
    # Text for Whatsapp
    msg_lines = [
        "*NEW GROCERY ORDER*",
        "",
        "Customer Details",
        "-------------------------",
        f"Name: {user.name}",
        f"Mobile: {user.mobile}",
        f"Area: {user.area}",
        f"House No: {user.house_no}",
        "",
        "ORDER ITEMS",
        "-------------------------"
    ]
    
    counter = 1
    for item in cart.items:
        # Freeze price
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product.name,
            quantity=item.quantity,
            price=item.product.price, # Stored price at purchase!
            requirement=item.requirement
        )
        db.session.add(order_item)
        
        item_total = item.product.price * item.quantity
        msg_lines.append(f"{counter}. {item.product.name}")
        msg_lines.append(f"Quantity: {item.quantity}")
        msg_lines.append(f"Price: ₹{item.product.price}")
        msg_lines.append(f"Total: ₹{item_total}")
        msg_lines.append(f"Requirement: {item.requirement or 'None'}")
        msg_lines.append("")
        counter += 1
        
    msg_lines.append("-------------------------")
    msg_lines.append(f"*TOTAL: ₹{total_amount}*")
    msg_lines.append(f"Order ID: #{order.id}")
    msg_lines.append("Please confirm the order.")
    
    # Delete cart
    for item in cart.items:
        db.session.delete(item)
    db.session.delete(cart)
    
    db.session.commit()
    
    whatsapp_number = current_app.config.get('SHOP_WHATSAPP_NUMBER')
    text = urllib.parse.quote("\n".join(msg_lines))
    wa_url = f"https://wa.me/{whatsapp_number}?text={text}"
    
    return jsonify({'success': True, 'whatsapp_url': wa_url})
