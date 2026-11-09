from flask import Flask, render_template
from models import close_db, init_db
from routes.feedback import feedback_bp
from routes.shop import shop_bp
from routes.admin import admin_bp

app = Flask(__name__)
app.config['DATABASE'] = 'db.sqlite'
app.config['SECRET_KEY'] = 'change-me'   # потрібен для session і flash

app.teardown_appcontext(close_db)
app.register_blueprint(feedback_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')

with app.app_context():
    init_db()


@app.route('/')
def index():
    return render_template('base.html')


if __name__ == '__main__':
    app.run(debug=True)