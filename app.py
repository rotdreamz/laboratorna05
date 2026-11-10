from flask import Flask, render_template
from flasgger import Swagger
from models import close_db, init_db
from routes.feedback import feedback_bp
from routes.shop import shop_bp
from routes.admin import admin_bp
from routes.api import api_bp

app = Flask(__name__)
app.config['DATABASE'] = 'db.sqlite'
app.config['SECRET_KEY'] = 'change-me'   # потрібен для session і flash

app.json.ensure_ascii = False   # щоб українська в JSON не перетворювалась на \u04...

swagger = Swagger(app, template={
    'info': {
        'title': 'Shop API',
        'description': 'REST API інтернет-магазину',
        'version': '1.0.0',
    },
    'definitions': {
        'Product': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer', 'example': 1},
                'name': {'type': 'string', 'example': 'Смартфон XYZ'},
                'description': {'type': 'string', 'example': 'Смартфон з потужною камерою'},
                'price': {'type': 'number', 'example': 15999},
                'stock': {'type': 'integer', 'example': 50},
                'image': {'type': 'string', 'example': 'phone.jpg'},
                'delivery': {'type': 'number', 'example': 100},
                'sale_price': {'type': 'number', 'example': 13999},
                'sale_color': {'type': 'string', 'example': 'red'},
            },
        },
        'ProductInput': {
            'type': 'object',
            'required': ['name', 'price'],
            'properties': {
                'name': {'type': 'string', 'example': 'Смартфон XYZ'},
                'description': {'type': 'string', 'example': 'Смартфон з потужною камерою'},
                'price': {'type': 'number', 'example': 15999},
                'stock': {'type': 'integer', 'example': 50},
                'delivery': {'type': 'number', 'example': 100},
                'sale_price': {'type': 'number', 'example': 13999},
                'sale_color': {'type': 'string', 'example': 'red'},
            },
        },
        'Error': {
            'type': 'object',
            'properties': {
                'error': {'type': 'string', 'example': 'Товар не знайдено'},
                'details': {'type': 'array', 'items': {'type': 'string'}},
            },
        },
    },
})

app.teardown_appcontext(close_db)
app.register_blueprint(feedback_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(api_bp)

with app.app_context():
    init_db()


@app.route('/')
def index():
    return render_template('base.html')


if __name__ == '__main__':
    app.run(debug=True)