from flask import Blueprint, render_template, request, redirect, url_for, flash
import models

feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        message = request.form['message'].strip()
        if not (name and email and message):
            flash('Заповніть усі поля')
        else:
            models.add_feedback(name, email, message)
            flash('Дякуємо за відгук!')
            return redirect(url_for('feedback.feedback'))
    return render_template('feedback.html')