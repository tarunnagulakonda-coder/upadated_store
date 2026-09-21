from flask import Blueprint, jsonify, render_template, session, redirect, url_for
from models.category import Category

bp = Blueprint('categories', __name__)

@bp.route('/categories')
def categories_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    main_categories = Category.query.filter_by(parent_id=None).all()
    return render_template('categories.html', categories=main_categories)

@bp.route('/categories/<int:id>')
def subcategories_page(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    parent_category = Category.query.get_or_404(id)
    subcategories = Category.query.filter_by(parent_id=id).all()
    return render_template('subcategories.html', parent=parent_category, subcategories=subcategories)

@bp.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.filter_by(parent_id=None).all()
    res = []
    for cat in categories:
        subs = [{'id': sub.id, 'name': sub.name, 'icon': sub.icon} for sub in cat.subcategories]
        res.append({'id': cat.id, 'name': cat.name, 'icon': cat.icon, 'subcategories': subs})
    return jsonify(res)
