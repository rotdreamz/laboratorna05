import sqlite3
from flask import g, current_app


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0,
    image TEXT,
    delivery REAL NOT NULL DEFAULT 0,
    sale_price REAL,
    sale_color TEXT NOT NULL DEFAULT 'red'
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);
"""

ORDER_STATUSES = ['new', 'processing', 'shipped', 'completed', 'cancelled']


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()


# ---------- фідбек ----------
def add_feedback(name, email, message):
    db = get_db()
    db.execute('INSERT INTO feedback (name, email, message) VALUES (?, ?, ?)',
               (name, email, message))
    db.commit()


def get_all_feedback():
    return get_db().execute('SELECT * FROM feedback ORDER BY created_at DESC').fetchall()


def delete_feedback(feedback_id):
    db = get_db()
    db.execute('DELETE FROM feedback WHERE id = ?', (feedback_id,))
    db.commit()


# ---------- клієнти (рівень 2) ----------
def get_all_clients():
    return get_db().execute('SELECT * FROM clients ORDER BY name').fetchall()


def get_client(client_id):
    return get_db().execute('SELECT * FROM clients WHERE id = ?', (client_id,)).fetchone()


def get_client_by_email(email):
    return get_db().execute('SELECT * FROM clients WHERE email = ?', (email,)).fetchone()


def add_client(name, email, phone):
    db = get_db()
    cur = db.execute('INSERT INTO clients (name, email, phone) VALUES (?, ?, ?)',
                     (name, email, phone))
    db.commit()
    return cur.lastrowid


def update_client(client_id, name, email, phone):
    db = get_db()
    db.execute('UPDATE clients SET name = ?, email = ?, phone = ? WHERE id = ?',
               (name, email, phone, client_id))
    db.commit()


def delete_client(client_id):
    db = get_db()
    db.execute('DELETE FROM clients WHERE id = ?', (client_id,))
    db.commit()


# ---------- продкуст ----------
def get_all_products():
    return get_db().execute('SELECT * FROM products ORDER BY name').fetchall()


def get_product(product_id):
    return get_db().execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()


def add_product(name, description, price, stock, image=None, delivery=0,
                sale_price=None, sale_color='red'):
    db = get_db()
    db.execute('INSERT INTO products (name, description, price, stock, image, '
               'delivery, sale_price, sale_color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
               (name, description, price, stock, image, delivery, sale_price, sale_color))
    db.commit()


def update_product(product_id, name, description, price, stock, image=None,
                   delivery=0, sale_price=None, sale_color='red'):
    """Порожнє посилання на картинку = лишити стару. Порожня sale_price = прибрати акцію."""
    db = get_db()
    if image:
        db.execute('UPDATE products SET name=?, description=?, price=?, stock=?, image=?, '
                   'delivery=?, sale_price=?, sale_color=? WHERE id=?',
                   (name, description, price, stock, image, delivery, sale_price,
                    sale_color, product_id))
    else:
        db.execute('UPDATE products SET name=?, description=?, price=?, stock=?, '
                   'delivery=?, sale_price=?, sale_color=? WHERE id=?',
                   (name, description, price, stock, delivery, sale_price,
                    sale_color, product_id))
    db.commit()


def delete_product(product_id):
    db = get_db()
    db.execute('DELETE FROM products WHERE id = ?', (product_id,))
    db.commit()


# ---------- замовлення ----------
def create_order(client_id, cart):
    """cart = {product_id: quantity}. Усе в одній транзакції."""
    db = get_db()
    try:
        cur = db.execute('INSERT INTO orders (client_id) VALUES (?)', (client_id,))
        order_id = cur.lastrowid
        for product_id, qty in cart.items():
            product = get_product(product_id)
            db.execute(
                'INSERT INTO order_items (order_id, product_id, quantity, price) '
                'VALUES (?, ?, ?, ?)',
                (order_id, product_id, qty, product['price']))
        db.commit()
        return order_id
    except Exception:
        db.rollback()
        raise


def get_all_orders():
    return get_db().execute("""
        SELECT o.id, o.status, o.created_at, c.name AS client_name, c.email,
               COALESCE(SUM(oi.quantity * oi.price), 0) AS total
        FROM orders o
        JOIN clients c ON c.id = o.client_id
        LEFT JOIN order_items oi ON oi.order_id = o.id
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """).fetchall()


def get_order_items(order_id):
    return get_db().execute("""
        SELECT p.name, oi.quantity, oi.price
        FROM order_items oi JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = ?
    """, (order_id,)).fetchall()


def update_order_status(order_id, status):
    db = get_db()
    db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))
    db.commit()


def delete_order(order_id):
    db = get_db()
    db.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    db.commit()