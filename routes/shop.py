from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import models

shop_bp = Blueprint('shop', __name__)


@shop_bp.route('/shop')
def shop():
    return render_template('shop.html', products=models.get_all_products())


@shop_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart = session.get('cart', {})
    key = str(product_id)
    cart[key] = cart.get(key, 0) + 1
    session['cart'] = cart
    return redirect(url_for('shop.shop'))


@shop_bp.route('/cart')
def cart():
    items, total = [], 0
    for pid, qty in session.get('cart', {}).items():
        product = models.get_product(int(pid))
        if product:
            items.append({'product': product, 'qty': qty})
            total += product['price'] * qty
    return render_template('cart.html', items=items, total=total)


@shop_bp.route('/checkout', methods=['POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Кошик порожній')
        return redirect(url_for('shop.shop'))

    name = request.form['name'].strip()
    email = request.form['email'].strip()
    phone = request.form.get('phone', '').strip()

    # Інтеграція з таблицею клієнтів: знайти існуючого або створити нового
    client = models.get_client_by_email(email)
    client_id = client['id'] if client else models.add_client(name, email, phone)

    models.create_order(client_id, {int(k): v for k, v in cart.items()})
    session.pop('cart')
    flash('Замовлення оформлено!')
    return redirect(url_for('shop.shop'))