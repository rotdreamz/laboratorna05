import sqlite3
from flask import Blueprint, jsonify, request
from models import get_all_products, get_product, add_product, update_product, delete_product
api_bp = Blueprint('api', __name__, url_prefix='/api')

ALLOWED_FIELDS = {'name', 'description', 'price', 'stock', 'image',
                  'delivery', 'sale_price', 'sale_color'}


def error(message, status, details=None):
    body = {'error': message}
    if details:
        body['details'] = details
    return jsonify(body), status


def validate_product(data, partial=False):
    """Повертає список помилок. partial=True для PATCH (поля необов'язкові)."""
    errors = []
    if not partial or 'name' in data:
        if not isinstance(data.get('name'), str) or not data['name'].strip():
            errors.append('name: потрібен непорожній рядок')
    if not partial or 'price' in data:
        price = data.get('price')
        if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
            errors.append('price: потрібне число >= 0')
    if 'stock' in data:
        stock = data['stock']
        if isinstance(stock, bool) or not isinstance(stock, int) or stock < 0:
            errors.append('stock: потрібне ціле число >= 0')
    for field in ('delivery', 'sale_price'):
        value = data.get(field)
        if value is not None and (isinstance(value, bool)
                                  or not isinstance(value, (int, float)) or value < 0):
            errors.append(f'{field}: потрібне число >= 0')
    return errors


def get_json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@api_bp.route('/products', methods=['GET'])
def api_get_products():
    """Список усіх товарів
    ---
    tags:
      - Products
    responses:
      200:
        description: Масив товарів
        schema:
          type: array
          items:
            $ref: '#/definitions/Product'
    """
    return jsonify([dict(row) for row in get_all_products()]), 200


@api_bp.route('/products/<int:product_id>', methods=['GET'])
def api_get_product(product_id):
    """Отримати товар за id
    ---
    tags:
      - Products
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        example: 1
    responses:
      200:
        description: Дані товару
        schema:
          $ref: '#/definitions/Product'
      404:
        description: Товар не знайдено
        schema:
          $ref: '#/definitions/Error'
    """
    row = get_product(product_id)
    if row is None:
        return error('Товар не знайдено', 404)
    return jsonify(dict(row)), 200


@api_bp.route('/products', methods=['POST'])
def api_create_product():
    """Створити товар
    ---
    tags:
      - Products
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/ProductInput'
    responses:
      201:
        description: Товар створено
        schema:
          $ref: '#/definitions/Product'
      400:
        description: Некоректні дані
        schema:
          $ref: '#/definitions/Error'
    """
    data = get_json_body()
    if data is None:
        return error('Тіло запиту має бути JSON-об\'єктом', 400)
    errors = validate_product(data)
    if errors:
        return error('Помилка валідації', 400, errors)

    new_id = add_product(
        data['name'].strip(), data.get('description'), data['price'],
        data.get('stock', 0), data.get('image'), data.get('delivery', 0),
        data.get('sale_price'), data.get('sale_color', 'red'))
    return jsonify(dict(get_product(new_id))), 201


@api_bp.route('/products/<int:product_id>', methods=['PUT'])
def api_replace_product(product_id):
    """Повне оновлення товару
    ---
    tags:
      - Products
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        example: 1
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/ProductInput'
    responses:
      200:
        description: Товар оновлено
        schema:
          $ref: '#/definitions/Product'
      400:
        description: Некоректні дані
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Товар не знайдено
        schema:
          $ref: '#/definitions/Error'
    """
    if get_product(product_id) is None:
        return error('Товар не знайдено', 404)
    data = get_json_body()
    if data is None:
        return error('Тіло запиту має бути JSON-об\'єктом', 400)
    errors = validate_product(data)
    if errors:
        return error('Помилка валідації', 400, errors)

    update_product(
        product_id, data['name'].strip(), data.get('description'), data['price'],
        data.get('stock', 0), data.get('image'), data.get('delivery', 0),
        data.get('sale_price'), data.get('sale_color', 'red'))
    return jsonify(dict(get_product(product_id))), 200


@api_bp.route('/products/<int:product_id>', methods=['PATCH'])
def api_patch_product(product_id):
    """Часткове оновлення товару
    ---
    tags:
      - Products
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        example: 1
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            price:
              type: number
              example: 14999
            stock:
              type: integer
              example: 45
    responses:
      200:
        description: Товар оновлено
        schema:
          $ref: '#/definitions/Product'
      400:
        description: Некоректні дані
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Товар не знайдено
        schema:
          $ref: '#/definitions/Error'
    """
    row = get_product(product_id)
    if row is None:
        return error('Товар не знайдено', 404)
    data = get_json_body()
    if data is None:
        return error('Тіло запиту має бути JSON-об\'єктом', 400)
    changes = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
    if not changes:
        return error('Немає полів для оновлення', 400, sorted(ALLOWED_FIELDS))
    errors = validate_product(changes, partial=True)
    if errors:
        return error('Помилка валідації', 400, errors)

    merged = {**dict(row), **changes}
    update_product(
        product_id, merged['name'].strip(), merged['description'], merged['price'],
        merged['stock'], merged['image'], merged['delivery'],
        merged['sale_price'], merged['sale_color'])
    return jsonify(dict(get_product(product_id))), 200


@api_bp.route('/products/<int:product_id>', methods=['DELETE'])
def api_delete_product(product_id):
    """Видалити товар
    ---
    tags:
      - Products
    parameters:
      - name: product_id
        in: path
        type: integer
        required: true
        example: 1
    responses:
      204:
        description: Товар видалено
      404:
        description: Товар не знайдено
        schema:
          $ref: '#/definitions/Error'
      409:
        description: Товар є в замовленнях, видалити не можна
        schema:
          $ref: '#/definitions/Error'
    """
    if get_product(product_id) is None:
        return error('Товар не знайдено', 404)
    try:
        delete_product(product_id)
    except sqlite3.IntegrityError:
        return error('Товар використовується в замовленнях', 409)
    return '', 204


# ---------- JSON-помилки тільки для адрес /api/ ----------
@api_bp.app_errorhandler(404)
def handle_404(e):
    if request.path.startswith('/api/'):
        return error('Ресурс не знайдено', 404)
    return e


@api_bp.app_errorhandler(405)
def handle_405(e):
    if request.path.startswith('/api/'):
        return error('Метод не дозволений для цього ресурсу', 405)
    return e


@api_bp.app_errorhandler(500)
def handle_500(e):
    if request.path.startswith('/api/'):
        return error('Внутрішня помилка сервера', 500)
    return e