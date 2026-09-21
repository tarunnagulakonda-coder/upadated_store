from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from models import db
from models.user import User
from models.order import Order

bp = Blueprint('profile', __name__)

@bp.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@bp.route('/api/profile', methods=['PUT'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False})
        
    user = User.query.get(session['user_id'])
    data = request.json
    user.name = data.get('name', user.name)
    user.area = data.get('area', user.area)
    user.mobile = data.get('mobile', user.mobile)
    user.house_no = data.get('house_no', user.house_no)
    
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/profile/orders', methods=['GET'])
def my_orders():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.order_date.desc()).all()
    return render_template('orders.html', orders=orders)

@bp.route('/profile/orders/<int:order_id>', methods=['GET'])
def order_details(order_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    order = Order.query.filter_by(id=order_id, user_id=session['user_id']).first_or_404()
    # Easiest way to show details is to render the bill
    return redirect(url_for('profile.view_bill', order_id=order.id))

@bp.route('/profile/bills/<int:order_id>', methods=['GET'])
def view_bill(order_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    order = Order.query.filter_by(id=order_id, user_id=session['user_id']).first_or_404()
    return render_template('bill.html', order=order)
