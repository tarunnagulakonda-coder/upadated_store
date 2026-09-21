from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db
from models.user import User

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        area = request.form.get('area')
        mobile = request.form.get('mobile')
        house_no = request.form.get('house_no')

        user = User.query.filter_by(mobile=mobile).first()
        if not user:
            user = User(name=name, area=area, mobile=mobile, house_no=house_no)
            db.session.add(user)
        else:
            user.name = name
            user.area = area
            user.house_no = house_no

        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('products.home'))
        
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.login'))
