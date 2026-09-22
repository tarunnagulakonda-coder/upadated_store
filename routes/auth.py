from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db
from models.user import User, normalize_mobile

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mode = request.form.get('mode', 'register')

        # ---------- Option 1: Existing user login (phone number only) ----------
        if mode == 'login':
            mobile = normalize_mobile(request.form.get('mobile'))
            if not mobile:
                flash("Please enter a valid 10-digit phone number.", 'error')
                return render_template('login.html', active_tab='login')
            user = User.query.filter_by(mobile=mobile).first()
            if not user:
                flash("User not found. Please register as a new user.", 'error')
                return render_template('login.html', active_tab='register')
            # Existing account: load saved details, no duplicates created
            user.record_login()
            db.session.commit()
            session['user_id'] = user.id
            return redirect(url_for('products.home'))

        # ---------- Option 2: New user registration (existing flow) ----------
        name = (request.form.get('name') or '').strip()
        area = (request.form.get('area') or '').strip()
        mobile = normalize_mobile(request.form.get('mobile'))
        house_no = (request.form.get('house_no') or '').strip()

        if not name or not area or not mobile or not house_no:
            flash("Please fill all fields with a valid 10-digit phone number.", 'error')
            return render_template('login.html', active_tab='register')

        # Phone number is the unique identifier: never create duplicates
        user = User.query.filter_by(mobile=mobile).first()
        if user:
            user.name = name
            user.area = area
            user.house_no = house_no
            user.record_login()
            db.session.commit()
            session['user_id'] = user.id
            return redirect(url_for('products.home'))

        user = User(name=name, area=area, mobile=mobile, house_no=house_no)
        db.session.add(user)
        db.session.flush()  # get user.id for the login record
        user.record_login()
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('products.home'))

    return render_template('login.html', active_tab='login')

@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.login'))
